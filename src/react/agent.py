"""ReAct agent implementation using OpenAI Agent SDK."""

import asyncio
import logging
import os
from typing import Any, Dict, List

from agents import Agent, OpenAIChatCompletionsModel, function_tool
from dotenv import load_dotenv
from openai import AsyncOpenAI

from src.prompts.system import REACT_INSTRUCTIONS, WEB_SEARCH_AGENT_INSTRUCTIONS
from src.utils import (
    AsyncWeaviateKnowledgeBase,
    Configs,
    get_weaviate_async_client,
)
from src.utils.tools.twelve_data import create_financial_data_tool

load_dotenv(verbose=True)

def get_default_model():
    """Get the default model from environment or fallback."""
    return os.getenv("AGENT_LLM_MODEL", "gemini-2.5-flash")


from google import genai
from google.genai import types


class WebSearchAgent:
    """Web search agent using Google's native Gemini API with Google Search tool."""
    
    def __init__(self, name: str, model: str, instructions: str, api_key: str):
        self.name = name
        self.model_name = model
        self.instructions = instructions
        
        # Create Google Search tool as per official documentation
        self.google_search_tool = types.Tool(google_search=types.GoogleSearch())
        
        # Create client for new API
        self.client = genai.Client(api_key=api_key)
        
    async def search_and_respond(self, query: str) -> str:
        """Search the web and provide a response with current information."""
        try:           
            # Create comprehensive prompt with instructions
            prompt = f"""
            {self.instructions}

            User Query: {query}

            Answer the user's query with searched information:
            """
            
            # Use the official Google Search tool configuration
            config = types.GenerateContentConfig(
                tools=[self.google_search_tool],
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            # Extract text from response
            result = ""
            if hasattr(response, 'text') and response.text:
                result = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to extract text from candidates
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        result = candidate.content.parts[0].text if candidate.content.parts[0].text else ""
            
            if not result:
                return "No search results found."
                
            # Check for grounding metadata and append sources
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    grounding = candidate.grounding_metadata
                    
                    # Add search queries used (as per official docs)
                    if hasattr(grounding, 'search_queries') and grounding.search_queries:
                        result += "\n\n**Search Queries Used:**\n"
                        for search_query in grounding.search_queries:
                            result += f"- {search_query}\n"
                    
                    # Add grounding chunks (sources) as per official docs
                    if hasattr(grounding, 'grounding_chunks') and grounding.grounding_chunks:
                        result += "\n**Sources:**\n"
                        for i, chunk in enumerate(grounding.grounding_chunks[:5], 1):  # Limit to 5 sources
                            if hasattr(chunk, 'web') and chunk.web:
                                title = getattr(chunk.web, 'title', 'Unknown Title')
                                uri = getattr(chunk.web, 'uri', 'Unknown URL')
                                result += f"{i}. [{title}]({uri})\n"
            
            return result
            
        except Exception as e:
            return f"Search error: {str(e)}"


async def create_web_search_agent(
    name: str = "Web Search Agent",
    instructions: str = WEB_SEARCH_AGENT_INSTRUCTIONS,
    model: str = None,
) -> WebSearchAgent:
    """Create a native Gemini web search agent with actual web search capability."""
    model_name = model or get_default_model()
    
    # Get API key from environment with proper priority
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Set GEMINI_API_KEY, GOOGLE_AI_API_KEY, or OPENAI_API_KEY environment variable.")
    
    return WebSearchAgent(
        name=name, 
        model=model_name, 
        instructions=instructions,
        api_key=api_key
    )

async def create_react_agent(
    name: str = "ReAct Agent",
    instructions: str = REACT_INSTRUCTIONS,
    additional_tools: List[Any] = None,
    model: str = None,
) -> Agent:
    """Create a ReAct agent with knowledge base search capability."""
    configs = Configs.from_env_var()
    
    # Set up Weaviate client and knowledge base (Wikipedia)
    async_weaviate_client = get_weaviate_async_client(
        http_host=configs.weaviate_http_host,
        http_port=configs.weaviate_http_port,
        http_secure=configs.weaviate_http_secure,
        grpc_host=configs.weaviate_grpc_host,
        grpc_port=configs.weaviate_grpc_port,
        grpc_secure=configs.weaviate_grpc_secure,
        api_key=configs.weaviate_api_key,
    )
    
    async_weaviate_kb = AsyncWeaviateKnowledgeBase(
        async_weaviate_client,
        collection_name="rbc_2_cra_public_documents",
    )
    
    # Set up OpenAI client
    async_openai_client = AsyncOpenAI()
    
    # Set up financial data tool
    financial_tool = create_financial_data_tool()
    
    # Create base tools - Wikipedia search + financial data
    tools = [
        function_tool(async_weaviate_kb.search_knowledgebase),
        function_tool(financial_tool.get_price),
        function_tool(financial_tool.get_time_series)
    ]
    
    
    # Add any additional tools
    if additional_tools:
        tools.extend(additional_tools)
    
    # Use provided model or fall back to default
    model_name = model or get_default_model()
    
    # Create the agent
    agent = Agent(
        name=name,
        instructions=instructions,
        tools=tools,
        model=OpenAIChatCompletionsModel(
            model=model_name, 
            openai_client=async_openai_client
        ),
    )
    
    return agent


class AgentManager:
    """Manager for agent lifecycle and resources."""
    
    def __init__(self):
        self.agent = None
        self.weaviate_client = None
        self.openai_client = None
        self.initialized = False
    
    async def initialize(
        self, 
        agent_name: str = "ReAct Agent", 
        agent_type: str = "react",
        model: str = None
    ) -> None:
        """Initialize an agent of the specified type.
        
        Args:
            agent_name: Name for the agent
            agent_type: Type of agent ("react", "web_search", or "openai_web_search")
            model: Model name to use (defaults to get_default_model())
        """
        if self.initialized:
            return
            
        try:
            if agent_type == "react":
                self.agent = await create_react_agent(name=agent_name, model=model)
            elif agent_type == "web_search":
                # Use native Gemini web search agent
                self.agent = await create_web_search_agent(name=agent_name, model=model)
            else:
                raise ValueError(f"Unknown agent type: {agent_type}. Supported: react, web_search")
                
            self.initialized = True
            model_info = f" (model: {model})" if model else ""
            logging.info(f"{agent_type.title()} agent '{agent_name}'{model_info} initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize {agent_type} agent: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        if self.weaviate_client:
            await self.weaviate_client.close()
        if self.openai_client:
            await self.openai_client.close()
        self.initialized = False
        logging.info("ReAct agent resources cleaned up")
    
    async def initialize_with_agent(self, agent_name: str, agent: Agent) -> None:
        """Initialize the manager with a pre-built agent.
        
        Args:
            agent_name: Name for the agent
            agent: Pre-built agent instance
        """
        if self.initialized:
            return
            
        try:
            self.agent = agent
            self.initialized = True
            logging.info(f"Agent '{agent_name}' initialized with pre-built agent successfully")
        except Exception as e:
            logging.error(f"Failed to initialize agent '{agent_name}': {e}")
            raise
    
    def get_agent(self) -> Agent:
        """Get the initialized agent."""
        if not self.initialized or not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        return self.agent