"""Dual-stage reference agent for generating advisor reference material."""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional

from openai import AsyncOpenAI

from ....prompts.system import (
    CRA_SEARCH_TERM_GENERATION, 
    WEB_SEARCH_QUERY_GENERATION, 
    WEB_SEARCH_EXECUTION,
    REFERENCE_SYNTHESIS
)
from ....utils import AsyncWeaviateKnowledgeBase

logger = logging.getLogger(__name__)


class ReferenceGenerationAgent:
    """Dual-stage agent for generating advisor reference material."""
    
    def __init__(self, cra_kb: AsyncWeaviateKnowledgeBase, llm_client: AsyncOpenAI, model: str = "gemini-2.5-flash"):
        if not cra_kb:
            raise ValueError("cra_kb cannot be None")
        if not llm_client:
            raise ValueError("llm_client cannot be None")
        
        self.cra_kb = cra_kb
        self.llm_client = llm_client
        self.model = model  # Keep gemini-2.5-flash as it's configured in .env
    
    async def generate_reference(self, client_situation: str) -> Dict:
        """Generate advisor reference material from client situation."""
        try:
            # Stage 1: Dual search
            research_data = await self._stage1_research(client_situation)
            
            # Stage 2: Reference synthesis
            reference = await self._stage2_synthesis(research_data)
            
            return reference
        except Exception as e:
            logger.error(f"Error generating reference: {e}")
            return {
                "error": str(e),
                "regulatory_overview": [],
                "current_numbers": {},
                "source_references": [],
                "advisor_notes": []
            }
    
    async def _stage1_research(self, client_situation: str) -> Dict:
        """Stage 1: Generate search terms and execute dual search."""
        # Generate search terms separately
        cra_keywords = await self._generate_cra_search_terms(client_situation)
        web_query = await self._generate_web_search_query(client_situation)
        
        logger.info(f"CRA keywords: {cra_keywords}")
        logger.info(f"Web query: {web_query}")
        
        # Split CRA keywords if multiple queries (one per line)
        cra_queries = [q.strip() for q in cra_keywords.split('\n') if q.strip()]
        
        # Execute CRA searches in parallel
        async def search_cra(query):
            try:
                return await self.cra_kb.search_knowledgebase(query)
            except Exception as e:
                logger.error(f"Error searching CRA for '{query}': {e}")
                return []
        
        # Run all CRA searches in parallel
        cra_search_results = await asyncio.gather(*[search_cra(q) for q in cra_queries])
        
        # Combine all results into a single list
        all_cra_results = []
        for results in cra_search_results:
            if isinstance(results, list):
                all_cra_results.extend(results)
            elif results:
                all_cra_results.append(results)
        
        cra_results = all_cra_results
        
        # Split web queries if multiple (one per line)
        web_queries = [q.strip() for q in web_query.split('\n') if q.strip()]
        
        # Execute web searches in parallel
        async def search_web(query):
            try:
                return await self._execute_web_search(query)
            except Exception as e:
                logger.error(f"Error searching web for '{query}': {e}")
                return None
        
        # Run all web searches in parallel
        web_search_results = await asyncio.gather(*[search_web(q) for q in web_queries])
        
        # Filter out None results and combine
        all_web_results = [r for r in web_search_results if r]
        web_results = "\n\n---\n\n".join(all_web_results) if all_web_results else "No web results found"
        
        return {
            "client_situation": client_situation,
            "cra_results": cra_results,
            "web_results": web_results,
            "cra_keywords": cra_keywords,
            "web_query": web_query
        }
    
    async def _generate_cra_search_terms(self, client_situation: str) -> str:
        """Generate CRA regulatory search keywords."""
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": CRA_SEARCH_TERM_GENERATION.format(client_situation=client_situation)
                }],
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating CRA search terms: {e}")
            # Return fallback keywords based on common topics
            if "RRSP" in client_situation:
                return "RRSP contribution limits"
            elif "TFSA" in client_situation:
                return "TFSA contribution rules"
            else:
                return "tax regulations"
    
    async def _generate_web_search_query(self, client_situation: str) -> str:
        """Generate web search query for current information."""
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": WEB_SEARCH_QUERY_GENERATION.format(client_situation=client_situation)
                }],
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating web search query: {e}")
            # Return fallback query
            return f"Canada financial regulations 2024 {client_situation[:50]}"
    
    async def _execute_web_search(self, query: str) -> str:
        """Execute web search using LLM with web search capabilities.
        
        Uses the LLM to search and summarize web results.
        """
        logger.info(f"Executing web search for: {query}")
        try:
            # Use LLM to search and summarize web results
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": WEB_SEARCH_EXECUTION.format(query=query)
                }],
                temperature=0.3
            )
            
            search_results = response.choices[0].message.content.strip()
            return f"Web search results for '{query}':\n{search_results}"
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"Web search unavailable for query: {query}"
    
    
    async def _stage2_synthesis(self, research_data: Dict) -> Dict:
        """Stage 2: Synthesize research into advisor reference material."""
        # Format CRA results
        cra_text = self._format_cra_results(research_data["cra_results"])
        
        # Build synthesis prompt
        prompt = REFERENCE_SYNTHESIS.format(
            client_situation=research_data["client_situation"],
            cra_results=cra_text,
            web_results=research_data["web_results"]
        )
        
        # Generate reference material
        response = await self.llm_client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.1
        )
        
        # Parse JSON response
        try:
            content = response.choices[0].message.content
            reference_data = self._extract_json_from_response(content)
            return reference_data
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON parsing error: {e}")
            return {
                "error": "Failed to parse reference material",
                "raw_response": response.choices[0].message.content[:500],
                "regulatory_overview": [],
                "current_numbers": {},
                "source_references": [],
                "advisor_notes": []
            }
    
    def _extract_json_from_response(self, content: str) -> dict:
        """Extract JSON from LLM response with fallback handling."""
        # Try direct JSON parsing first
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass
        
        # Try extracting from code blocks
        json_matches = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        for match in json_matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
        
        # If all parsing fails, raise with context
        raise ValueError(f"Could not extract valid JSON from response: {content[:200]}...")
    
    def _format_cra_results(self, cra_results: List) -> str:
        """Format CRA search results for synthesis."""
        if not cra_results:
            return "No CRA documents found"
        
        formatted = []
        # Send ALL results to LLM, not just top 3
        for i, result in enumerate(cra_results, 1):
            text = result.highlight.text[0] if result.highlight.text else ""
            # Extract chapter/section info from text
            chapter_info = "CRA Document" 
            if "Chapter" in text:
                chapter_info = text.split("\n")[0].strip("#").strip()
            # Increase text length to 800 chars for more context
            formatted.append(f"{i}. {chapter_info}:\n{text[:800]}...")
        
        return "\n\n".join(formatted)