"""ReAct agent implementation using OpenAI Agent SDK."""

import asyncio
import logging
from typing import Any, Dict, List

from agents import Agent, OpenAIChatCompletionsModel, function_tool
from dotenv import load_dotenv
from openai import AsyncOpenAI

from ..prompts.system import REACT_INSTRUCTIONS
from ..utils import (
    AsyncWeaviateKnowledgeBase,
    Configs,
    get_weaviate_async_client,
)

load_dotenv(verbose=True)

AGENT_LLM_NAME = "gemini-2.5-flash"


async def create_web_search_agent(
    name: str = "Web Search Agent",
) -> Agent:
    """Create a web search agent with no tools (uses built-in web search)."""
    async_openai_client = AsyncOpenAI()
    
    # Create agent with NO tools - uses built-in web search capabilities
    agent = Agent(
        name=name,
        instructions="Search the web for current information. Always search the web when asked and provide sources with URLs when possible.",
        tools=[],  # NO tools - enables built-in web search
        model=OpenAIChatCompletionsModel(
            model=AGENT_LLM_NAME, 
            openai_client=async_openai_client
        ),
    )
    
    return agent


async def create_react_agent(
    name: str = "ReAct Agent",
    instructions: str = REACT_INSTRUCTIONS,
    additional_tools: List[Any] = None,
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
    
    # Create base tools - Wikipedia search
    tools = [function_tool(async_weaviate_kb.search_knowledgebase)]
    
    
    # Add any additional tools
    if additional_tools:
        tools.extend(additional_tools)
    
    # Create the agent
    agent = Agent(
        name=name,
        instructions=instructions,
        tools=tools,
        model=OpenAIChatCompletionsModel(
            model=AGENT_LLM_NAME, 
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
    
    async def initialize(self, agent_name: str = "ReAct Agent", agent_type: str = "react") -> None:
        """Initialize an agent of the specified type.
        
        Args:
            agent_name: Name for the agent
            agent_type: Type of agent ("react" or "web_search")
        """
        if self.initialized:
            return
            
        try:
            if agent_type == "react":
                self.agent = await create_react_agent(name=agent_name)
            elif agent_type == "web_search":
                self.agent = await create_web_search_agent(name=agent_name)
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
                
            self.initialized = True
            logging.info(f"{agent_type.title()} agent '{agent_name}' initialized successfully")
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