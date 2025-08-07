"""Reference generation agent using multiple AgentManager instances."""

import json
import logging
from typing import Dict

from src.prompts.system import (
    CRA_SEARCH_TERM_GENERATION, 
    WEB_SEARCH_QUERY_GENERATION, 
    WEB_SEARCH_EXECUTION,
    REFERENCE_SYNTHESIS
)
from src.utils import AsyncWeaviateKnowledgeBase, Configs, get_weaviate_async_client
from src.react.agent import AgentManager
from src.react.runner import ReactRunner

logger = logging.getLogger(__name__)


class ReferenceGenerationAgent:
    """Reference generation agent using multiple AgentManager instances."""
    
    def __init__(self):
        # Multiple agent managers for different purposes
        self.react_agent_manager = AgentManager()  # For CRA search terms and synthesis
        self.web_agent_manager = AgentManager()    # For web search
        self.runner = ReactRunner(tracing_disabled=True)
        self.cra_kb = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the agents and knowledge base."""
        if not self.initialized:
            # Initialize both agents
            await self.react_agent_manager.initialize("Reference Generation Agent", "react")
            await self.web_agent_manager.initialize("Web Search Agent", "web_search")
            
            # Initialize CRA knowledge base
            configs = Configs.from_env_var()
            async_weaviate_client = get_weaviate_async_client(
                http_host=configs.weaviate_http_host,
                http_port=configs.weaviate_http_port,
                http_secure=configs.weaviate_http_secure,
                grpc_host=configs.weaviate_grpc_host,
                grpc_port=configs.weaviate_grpc_port,
                grpc_secure=configs.weaviate_grpc_secure,
                api_key=configs.weaviate_api_key,
            )
            
            self.cra_kb = AsyncWeaviateKnowledgeBase(
                async_weaviate_client,
                collection_name="rbc_2_cra_public_documents",
            )
            
            self.initialized = True
    
    async def generate_reference(self, client_situation: str) -> Dict:
        """Generate advisor reference material from client situation."""
        if not self.initialized:
            await self.initialize()
            
        try:
            research_data = await self._stage1_research(client_situation)
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
        cra_keywords = await self._generate_cra_search_terms(client_situation)
        
        # Split CRA keywords into multiple queries (one per line)
        cra_queries = [q.strip() for q in cra_keywords.split('\n') if q.strip()]
        
        # Execute CRA searches sequentially to avoid connection issues
        cra_search_results = []
        for query in cra_queries:
            try:
                kb_results = await self.cra_kb.search_knowledgebase(query)
                # Format the structured results into text
                if kb_results:
                    formatted_results = []
                    for i, result in enumerate(kb_results[:5], 1):  # Return 5 results per pattern
                        text = result.highlight.text[0] if result.highlight.text else ""
                        title = result.source.title or "CRA Document"
                        formatted_results.append(f"{i}. {title}:\n{text[:800]}")
                    result_text = "\n\n".join(formatted_results)
                else:
                    result_text = f"No CRA results found for: {query}"
                    
                cra_search_results.append({
                    "query": query,
                    "result": result_text
                })
            except Exception as e:
                logger.error(f"Error searching CRA for '{query}': {e}")
                cra_search_results.append({
                    "query": query,
                    "result": f"Search error for: {query}"
                })
        
        # Execute web search
        web_search_data = await self._execute_web_search(client_situation)
        logger.info(f"Web search data: {web_search_data}")
        
        return {
            "client_situation": client_situation,
            "cra_results": cra_search_results,  # Now list of {query, result} dicts
            "web_results": web_search_data["results"],
            "web_query": web_search_data["query"],
            "cra_keywords": cra_keywords
        }
    
    async def _generate_cra_search_terms(self, client_situation: str) -> str:
        """Generate CRA search terms using react agent."""
        prompt = CRA_SEARCH_TERM_GENERATION.format(client_situation=client_situation)
        result = await self.runner.run_single_query(
            self.react_agent_manager.get_agent(),
            prompt,
            verbose=False
        )
        return result["final_output"].strip() if result["success"] else "tax regulations"
    
    async def _execute_web_search(self, client_situation: str) -> Dict[str, str]:
        """Execute web search using dedicated web search agent."""
        try:
            # Step 1: Generate web search query using react agent
            web_query_prompt = WEB_SEARCH_QUERY_GENERATION.format(client_situation=client_situation)
            logger.info(f"Web query prompt: {web_query_prompt[:200]}...")
            
            query_result = await self.runner.run_single_query(
                self.react_agent_manager.get_agent(),
                web_query_prompt,
                verbose=False
            )
            
            logger.info(f"Web query generation success: {query_result['success']}")
            logger.info(f"Web query generation output: {query_result['final_output'][:200] if query_result['final_output'] else 'EMPTY'}")
            
            if query_result["success"] and query_result["final_output"].strip():
                web_queries_text = query_result["final_output"].strip()
                logger.info(f"Generated web queries: {web_queries_text}")
                
                # Split web queries into individual queries (one per line)
                web_queries = [q.strip() for q in web_queries_text.split('\n') if q.strip()]
                logger.info(f"Individual web queries: {web_queries}")
                
                # Step 2: Execute web searches in parallel
                import asyncio
                async def search_web_single(query):
                    try:
                        search_prompt = WEB_SEARCH_EXECUTION.format(query=query)
                        search_result = await self.runner.run_single_query(
                            self.web_agent_manager.get_agent(),  # Use web search agent
                            search_prompt,
                            verbose=False
                        )
                        
                        if search_result["success"]:
                            logger.info(f"Web search successful for: {query}")
                            return {
                                "query": query,
                                "result": search_result["final_output"]
                            }
                        else:
                            logger.warning(f"Web search failed for: {query}")
                            return {
                                "query": query,
                                "result": f"No web results found for: {query}"
                            }
                            
                    except Exception as e:
                        logger.error(f"Error searching web for '{query}': {e}")
                        return {
                            "query": query,
                            "result": f"Search error for: {query}"
                        }
                
                # Run all web searches in parallel
                web_search_results = await asyncio.gather(*[search_web_single(q) for q in web_queries])
                
                # Combine all web search results
                combined_results = []
                for i, search_result in enumerate(web_search_results, 1):
                    query = search_result["query"]
                    result = search_result["result"]
                    combined_results.append(f"Web Search {i} ('{query}'):\n{result}")
                
                combined_results_text = "\n\n---\n\n".join(combined_results)
                
                return {
                    "query": web_queries_text,  # All queries combined
                    "results": combined_results_text
                }
            else:
                logger.error(f"Web query generation failed")
                return {
                    "query": "Failed to generate web query",
                    "results": "Web query generation failed"
                }
                
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {
                "query": f"Error: {str(e)}",
                "results": "Web search failed due to error"
            }
    
    async def _stage2_synthesis(self, research_data: Dict) -> Dict:
        """Stage 2: Synthesize research into advisor reference material."""
        # Format CRA results from parallel searches
        cra_text = self._format_cra_parallel_results(research_data["cra_results"])
        
        prompt = REFERENCE_SYNTHESIS.format(
            client_situation=research_data["client_situation"],
            cra_results=cra_text,
            web_results=research_data["web_results"]
        )
        
        result = await self.runner.run_single_query(
            self.react_agent_manager.get_agent(),
            prompt,
            verbose=False
        )
        
        if result["success"]:
            try:
                content = result["final_output"]
                return self._extract_json_from_response(content)
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"JSON parsing error: {e}")
                return {
                    "error": "Failed to parse reference material",
                    "raw_response": content[:500],
                    "regulatory_overview": [],
                    "current_numbers": {},
                    "source_references": [],
                    "advisor_notes": []
                }
        else:
            return {
                "error": "Synthesis failed",
                "regulatory_overview": [],
                "current_numbers": {},
                "source_references": [],
                "advisor_notes": []
            }
    
    def _format_cra_parallel_results(self, cra_results: list) -> str:
        """Format parallel CRA search results for synthesis."""
        if not cra_results:
            return "No CRA documents found"
        
        formatted = []
        for i, search_result in enumerate(cra_results, 1):
            query = search_result["query"]
            result = search_result["result"]
            formatted.append(f"Search {i} ('{query}'):\n{result}")
        
        return "\n\n---\n\n".join(formatted)
    
    def _extract_json_from_response(self, content: str) -> dict:
        """Extract JSON from LLM response."""
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            # Try extracting from code blocks
            import re
            json_matches = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            for match in json_matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
            raise ValueError(f"Could not extract valid JSON from response: {content[:200]}...")