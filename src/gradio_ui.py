"""Gradio web interface for the ReAct Wealth Management Agent with advisor reference generation."""

import asyncio
import contextlib
import json
import logging
import os
import signal
import sys

import agents
import gradio as gr
from dotenv import load_dotenv
from gradio.components.chatbot import ChatMessage
from openai import AsyncOpenAI

from .prompts.system import REACT_INSTRUCTIONS
from .react.agents.meeting_intelligence.reference_generation import ReferenceGenerationAgent
from .utils import (
    AsyncWeaviateKnowledgeBase,
    Configs,
    get_weaviate_async_client,
    oai_agent_items_to_gradio_messages,
    oai_agent_stream_to_gradio_messages,
    pretty_print,
    setup_langfuse_tracer,
)


load_dotenv(verbose=True)


logging.basicConfig(level=logging.INFO)


# Use environment variable or default
AGENT_LLM_NAME = os.getenv("AGENT_LLM_MODEL", "gemini-2.5-flash")

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
    collection_name="rbc_2_cra_public_documents",
)

# Initialize reference generation agent
reference_agent = ReferenceGenerationAgent()


async def _cleanup_clients() -> None:
    """Close async clients."""
    await async_weaviate_client.close()
    await async_openai_client.close()


def _handle_sigint(signum: int, frame: object) -> None:
    """Handle SIGINT signal to gracefully shutdown."""
    with contextlib.suppress(Exception):
        asyncio.get_event_loop().run_until_complete(_cleanup_clients())
    sys.exit(0)


async def _main_chat(question: str, gr_messages: list[ChatMessage]):
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


async def generate_reference(client_situation: str, progress=gr.Progress()):
    """Generate advisor reference material from client situation."""
    if not client_situation or not client_situation.strip():
        return "Please provide a client situation description.", "{}", "{}", "", "", "", ""
    
    if len(client_situation) > 5000:
        return "Client situation description is too long (max 5000 characters).", "{}", "{}", "", "", "", ""
    
    # Initialize agent if not done already
    if not reference_agent.initialized:
        await reference_agent.initialize()
    
    progress(0.2, desc="Generating search terms...")
    
    try:
        # Get the raw search results by calling internal method
        research_data = await reference_agent._stage1_research(client_situation)
        
        progress(0.5, desc="Processing search results...")
        
        # Format raw CRA results - now from parallel searches
        cra_raw = []
        for search_result in research_data.get("cra_results", []):
            query = search_result.get("query", "Unknown query")
            result = search_result.get("result", "No result")
            # Show full results instead of truncating to 1000 chars
            cra_raw.append(f"=== Search: '{query}' ===\n{result}")
        cra_raw_text = "\n\n".join(cra_raw) if cra_raw else "No CRA results found"
        
        # Get web results
        web_raw_text = research_data.get("web_results", "No web results")
        
        progress(0.8, desc="Generating reference material...")
        
        # Generate reference material
        reference_data = await reference_agent._stage2_synthesis(research_data)
        
        # Format outputs for display
        regulatory_text = "\n".join(f"• {item}" for item in reference_data.get("regulatory_overview", []))
        
        current_numbers = reference_data.get("current_numbers", {})
        numbers_text = "\n".join(f"• {k}: {v}" for k, v in current_numbers.items())
        
        sources = reference_data.get("source_references", [])
        sources_text = "\n".join(f"• {source}" for source in sources)
        
        notes = reference_data.get("advisor_notes", [])
        notes_text = "\n".join(f"• {note}" for note in notes)
        
        # Create summary display
        summary = f"""## Regulatory Overview
{regulatory_text or "No regulatory information found."}

## Current Numbers
{numbers_text or "No current numbers available."}

## Sources
{sources_text or "No sources cited."}

## Advisor Notes
{notes_text or "No additional notes."}"""
        
        # Get search terms used
        cra_keywords = research_data.get("cra_keywords", "")
        web_query = research_data.get("web_query", "No web query generated")
        
        # Return all data including raw results and search terms
        return summary, json.dumps(reference_data, indent=2), json.dumps(reference_data.get("current_numbers", {}), indent=2), cra_raw_text, web_raw_text, cra_keywords, web_query
        
    except Exception as e:
        logging.error(f"Error generating reference: {e}")
        return f"Error: {str(e)}", "{}", "{}", "", "", "", ""


# Create the Gradio interface with tabs
with gr.Blocks(title="Wealth Management Assistant") as demo:
    gr.Markdown("# Wealth Management Assistant")
    gr.Markdown("ReAct-powered assistant with advisor reference generation")
    
    with gr.Tabs():
        # Reference generation tab FIRST
        with gr.Tab("Advisor Reference"):
            gr.Markdown("## Generate Reference Material from Client Situations")
            
            # Concise examples from meeting_06
            example_situations = [
                "Michael has $18,600 RRSP room and wants to maximize his $1,300 annual tax savings at 33% marginal rate. Currently contributing $8,000/year.",
                "RRSP funds sitting in savings account earning minimal returns. Need ETF portfolio recommendations for 30+ year horizon with 6-7% target returns.",
                "Michael has $18,600 RRSP room and $43,000 TFSA room. Earning $87,000 with $500/month savings capacity. Need optimal RRSP vs TFSA strategy.",
                "Common-law couple: Michael ($87,000) and girlfriend ($45,000). Looking for spousal RRSP strategies to optimize retirement income splitting."
            ]
            
            with gr.Row():
                with gr.Column(scale=3):
                    situation_input = gr.Textbox(
                        label="Client Situation",
                        placeholder="Describe the client's financial situation and needs...",
                        lines=5,
                        value=example_situations[0]  # Default to first example
                    )
                    
                    gr.Examples(
                        examples=example_situations,
                        inputs=situation_input,
                        label="Example Situations"
                    )
                    
                    generate_btn = gr.Button("Generate Reference Material", variant="primary")
            
            with gr.Row():
                with gr.Column():
                    summary_output = gr.Markdown(label="Reference Summary")
                
            with gr.Row():
                with gr.Column():
                    full_json_output = gr.Code(
                        label="Full Reference Data (JSON)",
                        language="json",
                        lines=10
                    )
                with gr.Column():
                    numbers_output = gr.Code(
                        label="Current Numbers",
                        language="json",
                        lines=10
                    )
            
            # Add search terms display
            with gr.Row():
                with gr.Column():
                    cra_search_terms = gr.Textbox(
                        label="CRA Search Keywords",
                        lines=4,
                        max_lines=6,
                        interactive=False
                    )
                with gr.Column():
                    web_search_terms = gr.Textbox(
                        label="Web Search Queries",
                        lines=3,
                        max_lines=4,
                        interactive=False
                    )
            
            # Add raw search results section
            with gr.Accordion("Raw Search Results", open=False):
                with gr.Row():
                    with gr.Column():
                        cra_raw_output = gr.Textbox(
                            label="CRA Knowledge Base Results",
                            lines=20,
                            show_copy_button=True,
                            interactive=False
                        )
                    with gr.Column():
                        web_raw_output = gr.Textbox(
                            label="Web Search Results", 
                            lines=20,
                            show_copy_button=True,
                            interactive=False
                        )
            
            generate_btn.click(
                fn=generate_reference,
                inputs=[situation_input],
                outputs=[summary_output, full_json_output, numbers_output, cra_raw_output, web_raw_output, cra_search_terms, web_search_terms]
            )
        
        # Chat tab SECOND
        with gr.Tab("Chat Assistant"):
            gr.ChatInterface(
                _main_chat,
                description="Chat with the ReAct-powered wealth management assistant",
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
    server_port: int = None,
    share: bool = False
) -> None:
    """Launch the Gradio application with reference generation.
    
    Args:
        server_name: Server host address
        server_port: Server port number (defaults to env var GRADIO_SERVER_PORT or 7860)
        share: Whether to create a shareable link
    """
    global async_weaviate_client, async_knowledgebase, async_openai_client, reference_agent
    
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
        collection_name="rbc_2_cra_public_documents",
    )

    async_openai_client = AsyncOpenAI()
    
    # Reinitialize reference generation agent
    reference_agent = ReferenceGenerationAgent()
    
    # Set up Langfuse tracing with full instrumentation
    setup_langfuse_tracer("wealth-management-gradio")
    agents.set_tracing_disabled(disabled=False)

    signal.signal(signal.SIGINT, _handle_sigint)

    # Use environment variable for port if not specified
    if server_port is None:
        server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    
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