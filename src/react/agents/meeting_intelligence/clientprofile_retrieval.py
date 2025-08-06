"""Enrich client profile Agent for meeting content."""

import asyncio
import logging
from typing import Dict, List

import agents
from dotenv import load_dotenv
from openai import AsyncOpenAI

from ....prompts.cp import Client_Profile_PROMPT
from ....utils.tools.cp_db import get_client_profile, client_db
from ....utils import pretty_print

logger = logging.getLogger(__name__)

load_dotenv(verbose=True)

AGENT_LLM_NAME = "gemini-2.5-flash"
no_tracing_config = agents.RunConfig(tracing_disabled=True)


async def _main(query: str):
    # Load client profiles if not already loaded
    if not client_db.is_loaded():
        import os
        # Get to project root from src/react/agents/meeting_intelligence/
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        client_profile_path = os.path.join(project_root, "data", "profile", "client_profile.jsonl")
        client_db.load_from_jsonl(client_profile_path)
        logger.info(f"Loaded {client_db.count()} client profiles")

    async_openai_client = AsyncOpenAI()
    cp_agent = agents.Agent(
        name="Client Profile Agent",
        instructions=Client_Profile_PROMPT,
        tools=[agents.function_tool(get_client_profile)],
        model=agents.OpenAIChatCompletionsModel(
            model=AGENT_LLM_NAME, openai_client=async_openai_client
        ),
    )

    response = await agents.Runner.run(
        cp_agent,
        input=query,
        run_config=no_tracing_config,
    )

    for item in response.new_items:
        pretty_print(item.raw_item)
        print()

    pretty_print(response.final_output)

    await async_openai_client.close()


if __name__ == "__main__":
    query = (
        "Michael has $18,600 RRSP room and wants to maximize his $1,300 annual tax savings at 33% marginal rate. Currently contributing $8,000/year."
    )

    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main(query))