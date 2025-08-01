"""Gradio web interface for the ReAct Wealth Management Agent."""

import asyncio
import contextlib
import logging
import signal
import sys

import agents
import gradio as gr
from dotenv import load_dotenv
from gradio.components.chatbot import ChatMessage
from openai import AsyncOpenAI

from .prompts.system import REACT_INSTRUCTIONS
from .utils import (
    AsyncWeaviateKnowledgeBase,
    Configs,
    get_weaviate_async_client,
    oai_agent_items_to_gradio_messages,
    oai_agent_stream_to_gradio_messages,
    pretty_print,
)


load_dotenv(verbose=True)


logging.basicConfig(level=logging.INFO)


AGENT_LLM_NAME = "gemini-2.5-flash"

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
async_openai_client = AsyncOpenAI()
async_knowledgebase = AsyncWeaviateKnowledgeBase(
    async_weaviate_client,
    collection_name="enwiki_20250520",
)


async def _cleanup_clients() -> None:
    """Close async clients."""
    await async_weaviate_client.close()
    await async_openai_client.close()


def _handle_sigint(signum: int, frame: object) -> None:
    """Handle SIGINT signal to gracefully shutdown."""
    with contextlib.suppress(Exception):
        asyncio.get_event_loop().run_until_complete(_cleanup_clients())
    sys.exit(0)


async def _main(question: str, gr_messages: list[ChatMessage]):
    """Main function to handle chat interactions."""
    main_agent = agents.Agent(
        name="Wealth Management ReAct Agent",
        instructions=REACT_INSTRUCTIONS,
        tools=[agents.function_tool(async_knowledgebase.search_knowledgebase)],
        model=agents.OpenAIChatCompletionsModel(
            model=AGENT_LLM_NAME, openai_client=async_openai_client
        ),
    )

    result_stream = agents.Runner.run_streamed(main_agent, input=question)
    async for _item in result_stream.stream_events():
        gr_messages += oai_agent_stream_to_gradio_messages(_item)
        if len(gr_messages) > 0:
            yield gr_messages


demo = gr.ChatInterface(
    _main,
    title="Wealth Management ReAct Agent",
    description="A ReAct-powered assistant for wealth management and financial guidance",
    type="messages",
    examples=[
        "What are the current investment trends in technology stocks?",
        "How should I diversify my portfolio for retirement planning?",
        "What are the tax implications of selling stocks this year?",
        "Tell me about recent developments in ESG investing",
    ],
)


def launch_gradio_app(
    server_name: str = "0.0.0.0", 
    server_port: int = 7860,
    share: bool = False
) -> None:
    """Launch the Gradio application.
    
    Args:
        server_name: Server host address
        server_port: Server port number
        share: Whether to create a shareable link
    """
    global async_weaviate_client, async_knowledgebase, async_openai_client
    
    # Reinitialize clients for the main process
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
    async_knowledgebase = AsyncWeaviateKnowledgeBase(
        async_weaviate_client,
        collection_name="enwiki_20250520",
    )

    async_openai_client = AsyncOpenAI()
    agents.set_tracing_disabled(disabled=True)

    signal.signal(signal.SIGINT, _handle_sigint)

    try:
        demo.launch(
            server_name=server_name,
            server_port=server_port,
            share=share
        )
    finally:
        asyncio.run(_cleanup_clients())


if __name__ == "__main__":
    launch_gradio_app()