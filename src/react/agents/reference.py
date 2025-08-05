from src.react.agent import ReactAgentManager, create_react_agent
from typing import Any, Dict, List, Optional

import asyncio
import logging
from typing import Any, Dict, List

from agents import Agent, OpenAIChatCompletionsModel, function_tool
from dotenv import load_dotenv
from openai import AsyncOpenAI
from src.react.runner import ReactRunner
import os
import glob


load_dotenv(verbose=True)

class ReferenceAgent():
    
    def __init__(self, name: str = "Reference Agent"):
        self.agent = None
        self.name = name
        self.system_prompt = """You are a wealth management assistant. 
        Review meeting summaries and gather topics related to tax for Canadian assets.
        If a client's assets are not in Canada, do not return any topics."""
        self.user_prompt = """
        Given the following meeting summaries, extract and list topics related to Canadian tax regulations. "
        Return the result as a JSON array of topic strings.
        """

    
    async def initialize(self) -> None:
        """Initialize the Reference agent and its resources."""
        if self.agent:
            return
            
        try:
            
            self.agent = await create_react_agent(name=self.name,
                                                  instructions=self.system_prompt)
            logging.info(f"Reference agent '{self.name}' initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Reference agent: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        # Add any specific cleanup logic if needed
        logging.info("Reference agent resources cleaned up")
    
    def get_agent(self) -> Agent:
        """Get the initialized agent."""
        if not self.agent:
            raise ValueError("Agent not initialized. Call 'initialize' first.")
        return self.agent
    async def get_topics(self,context):
        runner = ReactRunner(tracing_disabled=True)
        result = await runner.run_single_query(self.agent, self.user_prompt+context, verbose=False)
        return result

async def run_reference_agent():
    agent = ReferenceAgent()
    await agent.initialize()
    file_paths = sorted(glob.glob(os.path.join("data", "summary", "*")))
    result =""
    for file_path in file_paths:
        with open(file_path, "r") as f:
            context = f.read()
        topics = await agent.get_topics(context)
        result += "File: " + file_path + "\n" + "Extracted Topics: " + topics["final_output"] + "\n\n"
    with open("data/reference.txt", "w") as out_file:
        out_file.write(str(result))
    await agent.cleanup()