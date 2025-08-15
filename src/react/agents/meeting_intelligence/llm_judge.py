"""LLM as judge agent for evaluating client profile extraction quality."""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

import agents
from agents import Agent, OpenAIChatCompletionsModel, function_tool
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from src.prompts.tools import JUDGE_PROMPT_TEMPLATE
from src.utils import setup_langfuse_tracer

from src.utils.tools.cp_db import get_client_profile, client_db
from src.react.agents.meeting_intelligence.reference_tools import ReferenceToolsAgent

load_dotenv(verbose=True)

logger = logging.getLogger(__name__)

AGENT_LLM_NAME = "gemini-2.5-flash"

class JudgeEvaluationResult(BaseModel):
    """Pydantic model for judge evaluation results."""
    
    success: bool = Field(description="Whether the evaluation was successful")
    score: Optional[int] = Field(default=None, ge=1, le=10, description="Evaluation score from 1-10")
    reason: str = Field(description="Explanation for the score")
    client_name: str = Field(description="Name of the client being evaluated")
    generated_answer: Optional[str] = Field(default=None, description="Generated profile from ReferenceToolsAgent")
    reference_answer: Optional[str] = Field(default=None, description="Reference profile from database")
    error: Optional[str] = Field(default=None, description="Error message if evaluation failed")


class LLMJudgeAgent:
    """LLM-powered judge for evaluating client profile extraction quality."""
    
    def __init__(self):
        """Initialize the LLM judge agent."""
        self.openai_client = AsyncOpenAI()
        self.model_name = AGENT_LLM_NAME
        self.reference_agent: Optional[ReferenceToolsAgent] = None
        self.judge_agent: Optional[Agent] = None
        self.initialized = False
        self.run_config = agents.RunConfig(tracing_disabled=True)
    
    async def initialize(self):
        """Initialize the judge agent and reference tools."""
        if not self.initialized:
            # Initialize reference tools agent for comparison
            self.reference_agent = ReferenceToolsAgent()
            await self.reference_agent.initialize()
            
            # Create judge agent for LLM evaluation
            self.judge_agent = Agent(
                name="LLM Judge Agent for Client Profile Evaluation",
                instructions="Evaluate the quality of client profile extraction based on generated vs reference data.",
                model=OpenAIChatCompletionsModel(
                    model=self.model_name,
                    openai_client=self.openai_client
                )
            )
            
            self.initialized = True
            logger.info("LLMJudgeAgent initialized successfully")
    
    async def evaluate_client_profile_extraction(
        self, 
        meeting_content: str, 
        client_name: str
    ) -> JudgeEvaluationResult:
        """Evaluate client profile extraction quality by comparing generated vs reference data.
        
        Parameters
        ----------
        meeting_content : str
            The meeting transcript/content used for extraction
        client_name : str
            The client's first name to look up reference data
            
        Returns
        -------
        JudgeEvaluationResult
            Evaluation result with score, reason, and comparison data
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            logger.info(f"Starting evaluation for client: {client_name}")
            logger.info(f"Meeting content (first 200 chars): {meeting_content[:200]}{'...' if len(meeting_content) > 200 else ''}")
            
            # Get generated profile from ReferenceToolsAgent
            generated_result = await self.reference_agent.analyze_meeting_for_client_profile(meeting_content)
            generated_answer = generated_result.get("final_output", "No profile generated")
            
            logger.info(f"Generated answer (full text): {generated_answer}")
            
            # Get reference profile from database
            reference_data = get_client_profile(client_name)
            
            if reference_data is None:
                logger.warning(f"No reference profile found for client '{client_name}'")
                return JudgeEvaluationResult(
                    success=False,
                    error=f"No reference profile found for client '{client_name}'",
                    reason="Cannot evaluate - no reference data available",
                    client_name=client_name
                )
            
            # Format reference data as readable text
            reference_answer = self._format_reference_data(reference_data)
            
            logger.info(f"Reference answer (full text): {reference_answer}")
            
            # Prepare evaluation prompt
            evaluation_prompt = self._prepare_evaluation_prompt(
                generated_answer, reference_answer
            )
            
            logger.info(f"Evaluation prompt prepared (length: {len(evaluation_prompt)} chars)")
            
            # Get LLM evaluation
            evaluation = await self._get_llm_evaluation(evaluation_prompt)
            
            logger.info(f"LLM evaluation completed - Score: {evaluation['score']}/10, Reason: {evaluation['reason']}")
            
            result = JudgeEvaluationResult(
                success=True,
                score=evaluation["score"],
                reason=evaluation["reason"],
                generated_answer=generated_answer,
                reference_answer=reference_answer,
                client_name=client_name
            )
            
            logger.info(f"Evaluation result created successfully for client {client_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error in profile evaluation for client '{client_name}': {e}")
            logger.error(f"Meeting content length: {len(meeting_content)} chars")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return JudgeEvaluationResult(
                success=False,
                error=str(e),
                reason=f"Evaluation failed: {str(e)}",
                client_name=client_name
            )
    
    def _prepare_evaluation_prompt(self, generated_answer: str, reference_answer: str) -> str:
        """Prepare the evaluation prompt for the LLM judge.
        
        Parameters
        ----------
        generated_answer : str
            The generated profile description
        reference_answer : str
            The reference profile data formatted as text
            
        Returns
        -------
        str
            Formatted prompt for LLM evaluation
        """
        return JUDGE_PROMPT_TEMPLATE.format(
            reference_answer=reference_answer,
            generated_answer=generated_answer
        )
    
    def _format_reference_data(self, reference_data: Dict[str, Any]) -> str:
        """Format reference profile data as readable text.
        
        Parameters
        ----------
        reference_data : Dict[str, Any]
            The reference profile data from database
            
        Returns
        -------
        str
            Formatted reference data as natural language
        """
        sections = []
        
        # Client identification
        if "client_identification" in reference_data:
            ci = reference_data["client_identification"]
            section = f"Client: {ci.get('full_name', 'Unknown')}, age {ci.get('age', 'N/A')}, {ci.get('gender', 'N/A')}, citizen of {ci.get('citizenship', 'N/A')}, resident of {ci.get('residency', 'N/A')}, works as {ci.get('occupation', 'N/A')}"
            sections.append(section)
        
        # Financial situation
        if "financial_situation" in reference_data:
            fs = reference_data["financial_situation"]
            section = f"Financial: Annual income ${fs.get('annual_income', 0):,.0f}, income stability: {fs.get('income_stability', 'N/A')}, monthly savings: ${fs.get('monthly_savings_rate', 0) or 0:,.0f}, external assets: ${fs.get('external_asset_value', 0) or 0:,.0f}, tax complexity: {fs.get('tax_complexity_rating', 'N/A')}/5"
            sections.append(section)
        
        # Investment profile
        if "investment_profile" in reference_data:
            ip = reference_data["investment_profile"]
            section = f"Investment Profile: Risk tolerance {ip.get('risk_tolerance', 'N/A')}/10, risk capacity {ip.get('risk_capacity', 'N/A')}/10, {ip.get('investment_experience_years', 'N/A')} years experience, goal: {ip.get('primary_goal', 'N/A')}, time horizon: {ip.get('time_horizon_years', 'N/A')} years, liquidity needs: {ip.get('liquidity_needs', 'N/A')}"
            sections.append(section)
        
        # Investment preferences
        if "investment_preferences" in reference_data:
            prefs = reference_data["investment_preferences"]
            section = f"Preferences: {prefs.get('investment_style', 'N/A')} style, allocation: {prefs.get('asset_allocation_preference', 'N/A')}, sectors: {prefs.get('sector_preferences', 'N/A')}, ESG interest: {prefs.get('esg_interest', 'N/A')}"
            sections.append(section)
        
        # Planning needs
        if "planning_needs" in reference_data:
            pn = reference_data["planning_needs"]
            section = f"Planning: Retire at {pn.get('target_retirement_age', 'N/A')}, estate planning: {pn.get('estate_planning_needed', 'N/A')}, education fund: {pn.get('education_fund_needed', 'N/A')}, insurance review: {pn.get('insurance_review_needed', 'N/A')}"
            sections.append(section)
        
        # Account summary
        if "account_summary" in reference_data:
            acc = reference_data["account_summary"]
            balances = acc.get("account_balances", {})
            section = f"Accounts: {acc.get('relationship_tenure_years', 'N/A')} years tenure, balances - transactional: ${balances.get('transactional', 0) or 0:,.0f}, registered investments: ${balances.get('registered_investments', 0) or 0:,.0f}, non-registered: ${balances.get('non_registered_investments', 0) or 0:,.0f}"
            sections.append(section)
        
        return " | ".join(sections)
    
    async def _get_llm_evaluation(self, prompt: str) -> Dict[str, Any]:
        """Get evaluation from LLM using agents.Runner.run.
        
        Parameters
        ----------
        prompt : str
            The evaluation prompt
            
        Returns
        -------
        Dict[str, Any]
            Parsed evaluation with score and reason
        """
        try:
            # Use agents.Runner.run for the evaluation
            response = await agents.Runner.run(
                self.judge_agent,
                input=prompt,
                run_config=self.run_config
            )
            
            # Get the final output from the response
            response_text = response.final_output.strip()
            logger.info(f"Raw LLM response: {repr(response_text)}")
            
            # Parse JSON response
            parsed_result = self._parse_json_response(response_text)
            logger.info(f"Parsed evaluation result: Score={parsed_result['score']}, Reason={parsed_result['reason']}")
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error getting LLM evaluation: {e}")
            return {
                "score": 1,
                "reason": f"Evaluation failed due to LLM error: {str(e)}"
            }
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM's JSON response with fallback handling.
        
        Parameters
        ----------
        response_text : str
            The raw response from LLM
            
        Returns
        -------
        Dict[str, Any]
            Parsed evaluation with score and reason
        """
        import re
        
        # Clean the response text
        cleaned_text = response_text.strip()
        
        # Try to extract JSON from text (handle cases where LLM adds extra text)
        json_matches = re.findall(r'\{[^{}]*\}', cleaned_text)
        
        for json_match in json_matches:
            try:
                result = json.loads(json_match)
                
                # Validate required fields
                if "score" in result and "reason" in result:
                    # Ensure score is in valid range
                    score = max(1, min(10, int(result["score"])))
                    return {
                        "score": score,
                        "reason": str(result["reason"])
                    }
            except (json.JSONDecodeError, ValueError, KeyError):
                continue
        
        # Try parsing the whole response as JSON
        try:
            result = json.loads(cleaned_text)
            if "score" in result and "reason" in result:
                score = max(1, min(10, int(result["score"])))
                return {
                    "score": score,
                    "reason": str(result["reason"])
                }
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}. Response: {repr(cleaned_text[:200])}")
        
        # Fallback: try to extract score and reason from text
        lines = cleaned_text.split('\n')
        score = 5  # Default middle score
        reason = "Failed to parse evaluation response"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for score patterns
            if 'score' in line.lower():
                numbers = re.findall(r'\d+', line)
                if numbers:
                    score = max(1, min(10, int(numbers[0])))
            
            # Look for reason patterns
            elif 'reason' in line.lower():
                # Extract reason after the colon or quotes
                reason_match = re.search(r'reason["\s]*:?\s*["\s]*([^"]+)', line, re.IGNORECASE)
                if reason_match:
                    reason = reason_match.group(1).strip().rstrip('"').rstrip(',')
                else:
                    reason = line.replace('reason:', '').replace('Reason:', '').strip().strip('"').rstrip(',')
            elif len(line) > 20 and 'score' not in line.lower():
                # Use longer lines as potential reasons if no specific reason found
                if reason == "Failed to parse evaluation response":
                    reason = line.strip().strip('"').rstrip(',')
        
        logger.info(f"Fallback parsing result - Score: {score}, Reason: {reason}")
        return {
            "score": score,
            "reason": reason
        }
    
    async def close(self):
        """Clean up resources."""
        if self.reference_agent:
            await self.reference_agent.close()
        if self.openai_client:
            await self.openai_client.close()


# Convenience function for direct usage
async def create_llm_judge_agent() -> LLMJudgeAgent:
    """Create and initialize an LLM judge agent.
    
    Returns
    -------
    LLMJudgeAgent
        Initialized judge agent ready for use
    """
    judge = LLMJudgeAgent()
    await judge.initialize()
    return judge


# Main function for direct execution
async def main():
    """Main function to demonstrate judge agent usage."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python llm_judge.py '<meeting_content>' '<client_name>'")
        print("Example: python llm_judge.py 'Met with John today about investments' 'John'")
        return
    
    meeting_content = sys.argv[1]
    client_name = sys.argv[2]
    
    print(f"🔍 Evaluating client profile extraction...")
    print(f"Client: {client_name}")
    print(f"Meeting content: {meeting_content[:100]}{'...' if len(meeting_content) > 100 else ''}")
    print()
    
    setup_langfuse_tracer("JudgeAgent wealth-management-advisor-assist-agent")

    judge = await create_llm_judge_agent()
    
    try:
        result = await judge.evaluate_client_profile_extraction(meeting_content, client_name)
        
        print(f"✅ Evaluation Results:")
        print(f"Success: {result.success}")
        print(f"Client: {result.client_name}")
        
        if result.success:
            print(f"Score: {result.score}/10")
            print(f"Reason: {result.reason}")
            print(f"\n🤖 Generated Profile (first 200 chars):")
            gen_preview = result.generated_answer[:200] + "..." if len(result.generated_answer or "") > 200 else result.generated_answer
            print(gen_preview)
            print(f"\n📚 Reference Profile (first 200 chars):")
            ref_preview = result.reference_answer[:200] + "..." if len(result.reference_answer or "") > 200 else result.reference_answer
            print(ref_preview)
        else:
            print(f"Error: {result.error}")
            print(f"Reason: {result.reason}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await judge.close()


if __name__ == "__main__":
        # Reload client profile database
    CLIENT_PROFILE_DATA_PATH = os.getenv(
        "CLIENT_PROFILE_DATA_PATH", 
        "data/profile/client_profile.jsonl"
    )
    client_db.load_from_jsonl(CLIENT_PROFILE_DATA_PATH)
    logging.info(f"Reloaded {client_db.count()} client profiles from {CLIENT_PROFILE_DATA_PATH}")
    asyncio.run(main())