"""Semantic Analysis Agent for extracting structured information from meeting content."""

import glob
import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

from ....prompts.system import SEMANTIC_ANALYSIS_PROMPT
from ...agent import AgentManager
from ...runner import ReactRunner

load_dotenv(verbose=True)

logger = logging.getLogger(__name__)


class SemanticAnalysisAgent:
    """Semantic analysis agent using AgentManager pattern like ReferenceGenerationAgent."""
    
    def __init__(self):
        """Initialize the semantic analysis agent."""
        self.react_agent_manager = AgentManager()
        self.runner = ReactRunner(tracing_disabled=True)
        self.initialized = False
        
    async def initialize(self, model: str = None):
        """Initialize the ReAct agent for semantic analysis."""
        if not self.initialized:
            await self.react_agent_manager.initialize("Semantic Analysis Agent", "react", model)
            self.initialized = True
    
    async def extract_topics(self, context: str) -> Dict:
        """
        Extract tax-related topics from meeting content.
        
        Args:
            context: Meeting transcript or summary text
            
        Returns:
            Dictionary containing extraction results
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            prompt = SEMANTIC_ANALYSIS_PROMPT.format(context=context)
            result = await self.runner.run_single_query(
                self.react_agent_manager.get_agent(),
                prompt,
                verbose=False
            )
            return result
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return {
                "success": False,
                "error": str(e),
                "final_output": "[]"
            }
    
    async def process_meeting_files(self, file_paths: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Process multiple meeting files for semantic analysis.
        
        Args:
            file_paths: List of file paths to process. If None, processes all summary files.
            
        Returns:
            Dictionary mapping file paths to extracted topics
        """
        if not self.initialized:
            await self.initialize()
            
        if not file_paths:
            file_paths = sorted(glob.glob(os.path.join("data", "summary", "*.md")))
        
        results = {}
        for file_path in file_paths:
            try:
                with open(file_path, "r") as f:
                    context = f.read()
                
                topics = await self.extract_topics(context)
                results[file_path] = topics["final_output"]
                logger.info(f"Processed: {file_path}")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results[file_path] = f"Error: {str(e)}"
        
        return results