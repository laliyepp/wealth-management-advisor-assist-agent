"""Reference tools agent with client profile and financial data capabilities."""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from agents import Agent, OpenAIChatCompletionsModel, function_tool
from dotenv import load_dotenv
from openai import AsyncOpenAI

from src.prompts.tools import CLIENT_PROFILE_INSTRUCTIONS, STOCK_PRICE_INSTRUCTIONS
from src.utils.tools.cp_db import get_client_profile, client_db
from src.utils.tools.twelvedata_retrieval import AsyncFinancialDataTool
from src.react.agent import AgentManager
from src.react.runner import ReactRunner

load_dotenv(verbose=True)

logger = logging.getLogger(__name__)

AGENT_LLM_NAME = "gemini-2.5-flash"


class ReferenceToolsAgent:
    """Agent that provides client profile and financial data tools."""
    
    def __init__(self):
        """Initialize the reference tools agent."""
        self.agent_manager = AgentManager()
        self.runner = ReactRunner(tracing_disabled=False)
        self.financial_tool: Optional[AsyncFinancialDataTool] = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the agent and tools."""
        if not self.initialized:
            # Initialize financial data tool
            try:
                self.financial_tool = AsyncFinancialDataTool()
            except ValueError as e:
                logger.warning(f"Financial tool initialization failed: {e}")
                self.financial_tool = None
            
            # Create agent with tools
            await self._create_agent()
            
            # Load client profiles if not already loaded
            if not client_db.is_loaded():
                # Try to load from default location
                import os
                data_path = os.getenv("CLIENT_PROFILES_PATH", "data/client_profiles.jsonl")
                if os.path.exists(data_path):
                    client_db.load_from_jsonl(data_path)
                    logger.info(f"Loaded client profiles from {data_path}")
                else:
                    logger.warning(f"Client profiles file not found: {data_path}")
            
            self.initialized = True
    
    async def _create_agent(self):
        """Create agent with client and financial tools."""
        # Set up OpenAI client
        async_openai_client = AsyncOpenAI()
        
        # Create base tools
        tools = [function_tool(get_client_profile)]
        
        # Add financial data tool if available
        if self.financial_tool:
            tools.append(function_tool(self.financial_tool.get_price))
        
        # Create the agent
        agent = Agent(
            name="Reference Tools Agent",
            instructions=f"""You are a wealth management reference assistant with access to client profiles and financial data.

For client profile queries:
{CLIENT_PROFILE_INSTRUCTIONS}

For stock price queries:
{STOCK_PRICE_INSTRUCTIONS}

Always:
- Follow the specific instructions for each type of query
- Use the exact tool function names as specified
- Return data in the requested format (JSON for prices, natural language for profiles)
- Be precise with ticker symbols - use only the symbol itself (e.g., "AAPL" not "Apple Inc. (AAPL)")
- Explain which tool is used for each query""",
            tools=tools,
            model=OpenAIChatCompletionsModel(
                model=AGENT_LLM_NAME, 
                openai_client=async_openai_client
            ),
        )
        
        # Initialize with the agent manager
        await self.agent_manager.initialize_with_agent("Reference Tools Agent", agent)
    
    async def analyze_meeting_for_client_profile(self, meeting_content: str) -> Dict[str, Any]:
        """Analyze meeting content to extract client profile.
        
        Parameters
        ----------
        meeting_content : str
            The meeting transcript or content to analyze
            
        Returns
        -------
        Dict[str, Any]
            Result containing success status and client profile analysis
        """
        if not self.initialized:
            await self.initialize()
        
        query = CLIENT_PROFILE_INSTRUCTIONS.format(meeting_content=meeting_content)
        
        try:
            result = await self.runner.run_single_query(
                self.agent_manager.get_agent(),
                query,
                verbose=False
            )
            return result
        except Exception as e:
            logger.error(f"Error analyzing meeting for client profile: {e}")
            return {
                "success": False,
                "error": str(e),
                "final_output": f"Error analyzing meeting content: {str(e)}"
            }
    
    async def extract_stock_prices(self, meeting_transcript: str) -> Dict[str, Any]:
        """Extract stock prices from meeting transcript.
        
        Parameters
        ----------
        meeting_transcript : str
            The meeting transcript to analyze for ticker symbols
            
        Returns
        -------
        Dict[str, Any]
            Result containing success status and price information
        """
        if not self.initialized:
            await self.initialize()
        
        query = f"{STOCK_PRICE_INSTRUCTIONS}\n\nMeeting transcript: {meeting_transcript}"
        
        try:
            result = await self.runner.run_single_query(
                self.agent_manager.get_agent(),
                query,
                verbose=False
            )
            return result
        except Exception as e:
            logger.error(f"Error extracting stock prices: {e}")
            return {
                "success": False,
                "error": str(e),
                "final_output": f"Error extracting stock prices: {str(e)}"
            }
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a general query using the reference tools agent.
        
        Parameters
        ----------
        query : str
            The query to process
            
        Returns
        -------
        Dict[str, Any]
            Result containing success status and response
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            result = await self.runner.run_single_query(
                self.agent_manager.get_agent(),
                query,
                verbose=True
            )
            return result
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "error": str(e),
                "final_output": f"Error processing query: {str(e)}"
            }
    
    async def close(self):
        """Clean up resources."""
        if self.financial_tool:
            await self.financial_tool.close()


# Convenience function for direct usage
async def create_reference_tools_agent() -> ReferenceToolsAgent:
    """Create and initialize a reference tools agent.
    
    Returns
    -------
    ReferenceToolsAgent
        Initialized agent ready for use
    """
    agent = ReferenceToolsAgent()
    await agent.initialize()
    return agent