"""Gradio web interface for the ReAct Wealth Management Agent with advisor reference generation."""

import asyncio
import contextlib
import json
import logging
import os
import signal
import sys

import gradio as gr
from dotenv import load_dotenv
from openai import AsyncOpenAI

from .react.agents.meeting_intelligence.reference_generation import ReferenceGenerationAgent
from .utils import (
    AsyncWeaviateKnowledgeBase,
    Configs,
    get_weaviate_async_client,
    setup_langfuse_tracer,
)


load_dotenv(verbose=True)
logging.basicConfig(level=logging.INFO)

# Global variables - will be initialized in launch_gradio_app()
async_weaviate_client = None
async_openai_client = None
async_knowledgebase = None
reference_agent = None


async def _cleanup_clients() -> None:
    """Close async clients."""
    await async_weaviate_client.close()
    await async_openai_client.close()


def _handle_sigint(signum: int, frame: object) -> None:
    """Handle SIGINT signal to gracefully shutdown."""
    with contextlib.suppress(Exception):
        asyncio.get_event_loop().run_until_complete(_cleanup_clients())
    sys.exit(0)




async def generate_reference(client_situation: str, progress=gr.Progress()):
    """Generate advisor reference material from client situation."""
    if not client_situation or not client_situation.strip():
        error_msg = "Please provide a client situation description."
        return error_msg, error_msg, error_msg, "{}", "", ""
    
    if len(client_situation) > 5000:
        error_msg = "Client situation description is too long (max 5000 characters)."
        return error_msg, error_msg, error_msg, "{}", "", ""
    
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
        
        # Format the 3 new tab sections
        
        # 1. Regulatory Overview
        regulatory_items = reference_data.get("regulatory_overview", [])
        if regulatory_items:
            regulatory_md = "## CRA Rules & Regulations\n\n"
            for item in regulatory_items:
                if isinstance(item, dict):
                    regulation = item.get("regulation", "")
                    source = item.get("source", "")
                    details = item.get("details", "")
                    regulatory_md += f"### {regulation}\n**Source:** {source}\n\n{details}\n\n---\n\n"
                else:
                    regulatory_md += f"• {item}\n\n"
        else:
            regulatory_md = "No regulatory information found."
        
        # 2. Web Search Results (with URLs)
        web_items = reference_data.get("web_search_results", [])
        if web_items:
            web_md = "## Current Web Information\n\n"
            for item in web_items:
                if isinstance(item, dict):
                    finding = item.get("finding", "")
                    source_url = item.get("source_url", "")
                    relevance = item.get("relevance", "")
                    web_md += f"**Finding:** {finding}\n\n"
                    web_md += f"**Source:** [{source_url}]({source_url})\n\n"
                    web_md += f"**Relevance:** {relevance}\n\n---\n\n"
                else:
                    web_md += f"• {item}\n\n"
        else:
            web_md = "No web search results available."
        
        # 3. Final Recommendation
        final_rec = reference_data.get("final_recommendation", {})
        if final_rec:
            rec_md = "## Final Recommendations\n\n"
            if isinstance(final_rec, dict):
                answer = final_rec.get("answer", "")
                reasoning = final_rec.get("reasoning", "")
                next_steps = final_rec.get("next_steps", "")
                
                if answer:
                    rec_md += f"### Answer\n{answer}\n\n"
                if reasoning:
                    rec_md += f"### Reasoning\n{reasoning}\n\n"
                if next_steps:
                    rec_md += f"### Next Steps\n{next_steps}\n\n"
            else:
                rec_md += f"{final_rec}\n\n"
        else:
            rec_md = "No final recommendations available."
        
        # Return the formatted data for the new UI structure:
        # [regulatory_output, web_results_output, final_recommendation_output, full_json_output, cra_raw_output, web_raw_output]
        return regulatory_md, web_md, rec_md, json.dumps(reference_data, indent=2), cra_raw_text, web_raw_text
        
    except Exception as e:
        logging.error(f"Error generating reference: {e}")
        error_msg = f"Error: {str(e)}"
        return error_msg, error_msg, error_msg, "{}", "", ""


# Create the Gradio interface - simplified to only Advisor Reference
with gr.Blocks(title="Wealth Management Assistant") as demo:
    gr.Markdown("# Wealth Management Assistant")
    gr.Markdown("Google Search-powered assistant with advisor reference generation")
    
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
    
    # Three structured tabs for the new format
    with gr.Tabs():
        with gr.Tab("📋 Regulatory Overview"):
            regulatory_output = gr.Markdown(
                label="CRA Rules & Regulations with Sources",
                value="*Generate reference material to see regulatory overview*"
            )
        
        with gr.Tab("🌐 Web Search Results"):
            web_results_output = gr.Markdown(
                label="Current Web Information with URLs",
                value="*Generate reference material to see web search results*"
            )
        
        with gr.Tab("💡 Final Recommendation"):
            final_recommendation_output = gr.Markdown(
                label="Synthesis & Recommendations",
                value="*Generate reference material to see final recommendations*"
            )
    
    # Raw data for debugging (collapsible)
    with gr.Accordion("Raw Data (JSON)", open=False):
        full_json_output = gr.Code(
            label="Full Reference Data",
            language="json",
            lines=15
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
        outputs=[regulatory_output, web_results_output, final_recommendation_output, full_json_output, cra_raw_output, web_raw_output]
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
    
    # Initialize all components
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
    
    # Initialize reference generation agent
    reference_agent = ReferenceGenerationAgent()
    
    # Set up Langfuse tracing with full instrumentation
    setup_langfuse_tracer("wealth-management-gradio")
    
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