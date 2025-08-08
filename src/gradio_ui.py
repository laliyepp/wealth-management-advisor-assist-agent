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

from src.react.agents.meeting_intelligence.reference_generation import ReferenceGenerationAgent
from src.react.agents.meeting_intelligence.semantic_analysis import SemanticAnalysisAgent
from src.utils import (
    AsyncWeaviateKnowledgeBase,
    Configs,
    get_weaviate_async_client,
    setup_langfuse_tracer,
)
from src.react.agents.meeting_intelligence.reference_tools import ReferenceToolsAgent
from src.utils.tools.cp_db import client_db


load_dotenv(verbose=True)
logging.basicConfig(level=logging.INFO)

# Global variables - will be initialized in launch_gradio_app()
async_weaviate_client = None
async_openai_client = None
async_knowledgebase = None
reference_agent = None
clientprofile_agent = ReferenceToolsAgent()
semantic_agent = None

# Load client profile database
CLIENT_PROFILE_DATA_PATH = os.getenv(
    "CLIENT_PROFILE_DATA_PATH",
    "data/profile/client_profile.jsonl"
)
client_db.load_from_jsonl(CLIENT_PROFILE_DATA_PATH)
logging.info(f"Loaded {client_db.count()} client profiles from {CLIENT_PROFILE_DATA_PATH}")


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
        return error_msg, error_msg, error_msg, error_msg, "{}", "{}", "{}", "{}", "", ""
    
    if len(client_situation) > 5000:
        error_msg = "Client situation description is too long (max 5000 characters)."
        return error_msg, error_msg, error_msg, error_msg, "{}", "{}", "{}", "{}", "", ""
    
    # Initialize agent if not done already
    if not reference_agent.initialized:
        await reference_agent.initialize()

    if not clientprofile_agent.initialized:
        await  clientprofile_agent.initialize()
    
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
        
        # Generate client profile context and inject into reference data
        client_profile_context = await clientprofile_agent.analyze_meeting_for_client_profile(client_situation)
        if client_profile_context.get("success"):
            client_profile_info = client_profile_context.get("final_output", "")
            # Append to the research data for context
            reference_data["client_profile_info"] = client_profile_info


        # Format the 4 new tab sections
        
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

        # 3. Client Profile Context
        client_profile_info = reference_data.get("client_profile_info", "")
        if client_profile_info:
            client_profile_md = "## Client Profile Context\n\n"
            if isinstance(client_profile_info, str):
                client_profile_md += client_profile_info
            else:
                client_profile_md += json.dumps(client_profile_info, indent=2)
        else:
            client_profile_md = "No client profile context available."
        
        # 4. Final Recommendation
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
        
        # Extract client profile raw data from client situation
        client_profile_raw_data = {}
        # Extract client name from client_profile_info (format: "name: profile")
        extracted_name = None
        if client_profile_info and isinstance(client_profile_info, str):
            # Look for the pattern "name:" at the start of the string
            if ',' in client_profile_info:
                extracted_name = client_profile_info.split(',')[0].lower()
        
        if extracted_name:
            from src.utils.tools.cp_db import get_client_profile
            client_profile_raw_data = get_client_profile(extracted_name)
            if not client_profile_raw_data:
                client_profile_raw_data = {"error": f"No profile found for client: {extracted_name}"}
        else:
            client_profile_raw_data = {"note": "No client name detected in situation description"}
        
        # Create tab-specific raw data
        regulatory_raw_data = {"regulatory_overview": reference_data.get("regulatory_overview", [])}
        web_search_raw_data = {"web_search_results": reference_data.get("web_search_results", [])}
        final_rec_raw_data = {"final_recommendation": reference_data.get("final_recommendation", {})}
        
        # Return the formatted data for the new UI structure:
        # [regulatory_output, web_results_output, client_profile_md, final_recommendation_output, regulatory_raw, web_raw, client_profile_raw, final_rec_raw, cra_raw_output, web_raw_output]
        return (regulatory_md, web_md, client_profile_md, rec_md, 
                json.dumps(regulatory_raw_data, indent=2),
                json.dumps(web_search_raw_data, indent=2), 
                json.dumps(client_profile_raw_data, indent=2),
                json.dumps(final_rec_raw_data, indent=2),
                cra_raw_text, web_raw_text)
        
    except Exception as e:
        logging.error(f"Error generating reference: {e}")
        error_msg = f"Error: {str(e)}"
        return error_msg, error_msg, error_msg, error_msg, "{}", "{}", "{}", "{}", "", ""


async def analyze_meeting_content(file_type: str, meeting_selection: str, progress=gr.Progress()):
    """Analyze meeting content using semantic analysis agent to extract Canadian tax topics."""
    if not meeting_selection or not file_type:
        return "Please select both file type and meeting."
    
    # Initialize semantic agent if not done already
    if not semantic_agent.initialized:
        await semantic_agent.initialize()
    
    progress(0.2, desc="Loading meeting file...")
    
    try:
        # Construct file path based on selection
        if file_type == "Summary":
            file_path = f"data/summary/{meeting_selection}.md"
        else:  # Transcript
            file_path = f"data/transcript/{meeting_selection}.vtt"
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        progress(0.5, desc="Analyzing content for Canadian tax topics...")
        
        # Extract topics using semantic analysis agent
        result = await semantic_agent.extract_topics(content)
        
        progress(0.8, desc="Formatting results...")
        
        if result.get("success", True):
            topics_output = result.get("final_output", "[]")
            
            # Parse and format topics nicely
            try:
                import json
                topics_list = json.loads(topics_output)
                if isinstance(topics_list, list) and topics_list:
                    formatted_topics = "## Canadian Tax Topics Identified:\n\n"
                    for i, topic in enumerate(topics_list, 1):
                        formatted_topics += f"{i}. {topic}\n"
                    formatted_topics += f"\n**Total Topics Found:** {len(topics_list)}"
                else:
                    formatted_topics = "No Canadian tax-related topics found in this meeting content."
            except json.JSONDecodeError:
                # If not valid JSON, display raw output
                formatted_topics = f"## Extracted Topics:\n\n{topics_output}"
            
            # Also show file info
            file_info = f"**File Analyzed:** {file_path}\n**File Type:** {file_type}\n**Content Length:** {len(content)} characters\n\n"
            
            return file_info + formatted_topics, content[:2000] + ("..." if len(content) > 2000 else "")
        else:
            error_msg = f"Error analyzing content: {result.get('error', 'Unknown error')}"
            return error_msg, ""
            
    except FileNotFoundError:
        error_msg = f"File not found: {file_path}"
        return error_msg, ""
    except Exception as e:
        logging.error(f"Error analyzing meeting content: {e}")
        error_msg = f"Error: {str(e)}"
        return error_msg, ""


# Create the Gradio interface with Meeting Intelligence and Advisor Reference
with gr.Blocks(title="Wealth Management Assistant") as demo:
    gr.Markdown("# Wealth Management Assistant")
    gr.Markdown("AI-powered assistant with meeting intelligence and advisor reference generation")
    
    # Main application tabs
    with gr.Tabs():
        # Semantic Analysis Tab  
        with gr.Tab("🧠 Semantic Analysis"):
            gr.Markdown("### Semantic Analysis of Meeting Content")
            gr.Markdown("Extract Canadian tax-related topics from meeting transcripts and summaries")
            
            with gr.Row():
                with gr.Column():
                    # File type selection
                    file_type_dropdown = gr.Dropdown(
                        choices=["Summary", "Transcript"],
                        label="Content Type",
                        value="Summary",
                        info="Choose between processed summary or raw transcript"
                    )
                    
                    # Meeting selection
                    meeting_dropdown = gr.Dropdown(
                        choices=[
                            "meeting_06_canadian_tax_optimization",
                            "meeting_07_toronto_real_estate_investment", 
                            "meeting_08_canadian_estate_planning",
                            "meeting_09_investment_risk_assessment",
                            "meeting_10_retirement_planning_canadian"
                        ],
                        label="Meeting Selection", 
                        value="meeting_06_canadian_tax_optimization",
                        info="Select meeting from 06 to 10"
                    )
                    
                    analyze_btn = gr.Button("🔍 Analyze Meeting Content", variant="primary")
            
            # Output areas
            with gr.Row():
                with gr.Column():
                    topics_output = gr.Markdown(
                        label="Extracted Canadian Tax Topics",
                        value="*Select a meeting and click analyze to see extracted topics*"
                    )
            
            # Raw content preview (collapsible)
            with gr.Accordion("📄 Content Preview", open=False):
                content_preview = gr.Textbox(
                    label="Meeting Content (First 2000 chars)",
                    lines=15,
                    show_copy_button=True,
                    interactive=False
                )
            
            # Connect the analyze button
            analyze_btn.click(
                fn=analyze_meeting_content,
                inputs=[file_type_dropdown, meeting_dropdown],
                outputs=[topics_output, content_preview]
            )
        
        # Advisor Reference Tab
        with gr.Tab("📋 Advisor Reference"):
            gr.Markdown("### Generate Reference Material from Client Situations")
            
            # Input section for Advisor Reference
            with gr.Row():
                with gr.Column(scale=3):
                    advisor_situation_input = gr.Textbox(
                        label="Client Situation",
                        placeholder="Describe the client's financial situation and needs...",
                        lines=5,
                        value="Michael has $18,600 RRSP room and wants to maximize his $1,300 annual tax savings at 33% marginal rate. Currently contributing $8,000/year."
                    )
                    
                    # Examples for advisor reference
                    advisor_examples = [
                        "Michael has $18,600 RRSP room and wants to maximize his $1,300 annual tax savings at 33% marginal rate. Currently contributing $8,000/year.",
                        "RRSP funds sitting in savings account earning minimal returns. Need ETF portfolio recommendations for 30+ year horizon with 6-7% target returns.",
                        "Michael has $18,600 RRSP room and $43,000 TFSA room. Earning $87,000 with $500/month savings capacity. Need optimal RRSP vs TFSA strategy.",
                        "Common-law couple: Michael ($87,000) and girlfriend ($45,000). Looking for spousal RRSP strategies to optimize retirement income splitting."
                    ]
                    
                    gr.Examples(
                        examples=advisor_examples,
                        inputs=advisor_situation_input,
                        label="Example Situations"
                    )
                    
                    advisor_generate_btn = gr.Button("Generate Reference Material", variant="primary")
            
            # Three structured tabs for the advisor reference format
            with gr.Tabs():
                with gr.Tab("📋 Regulatory Overview"):
                    regulatory_output = gr.Markdown(
                        label="CRA Rules & Regulations with Sources",
                        value="*Generate reference material to see regulatory overview*"
                    )
                    # Raw data for regulatory tab
                    with gr.Accordion("Raw Data (JSON)", open=False):
                        regulatory_raw_output = gr.Code(
                            label="Regulatory Raw Data",
                            language="json",
                            lines=15
                        )
                
                with gr.Tab("🌐 Web Search Results"):
                    web_results_output = gr.Markdown(
                        label="Current Web Information with URLs",
                        value="*Generate reference material to see web search results*"
                    )
                    # Raw data for web search tab
                    with gr.Accordion("Raw Data (JSON)", open=False):
                        web_search_raw_output = gr.Code(
                            label="Web Search Raw Data",
                            language="json",
                            lines=15
                        )

                with gr.Tab("💼 Client Profile Context"):
                    client_profile_output = gr.Markdown(
                        label="Client Profile Context",
                        value="*Generate reference material to see client profile context*"
                    )
                    # Raw data for client profile tab
                    with gr.Accordion("Raw Data (JSON)", open=False):
                        client_profile_raw_output = gr.Code(
                            label="Client Profile Raw Data",
                            language="json",
                            lines=15
                        )
                
                with gr.Tab("💡 Final Recommendation"):
                    final_recommendation_output = gr.Markdown(
                        label="Synthesis & Recommendations",
                        value="*Generate reference material to see final recommendations*"
                    )
                    # Raw data for final recommendation tab
                    with gr.Accordion("Raw Data (JSON)", open=False):
                        final_rec_raw_output = gr.Code(
                            label="Final Recommendation Raw Data",
                            language="json",
                            lines=15
                        )
            
            # Add raw search results section - moved inside Advisor Reference tab
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
            
            # Connect the advisor generate button
            advisor_generate_btn.click(
                fn=generate_reference,
                inputs=[advisor_situation_input],
                outputs=[regulatory_output, web_results_output, client_profile_output, final_recommendation_output, 
                        regulatory_raw_output, web_search_raw_output, client_profile_raw_output, final_rec_raw_output,
                        cra_raw_output, web_raw_output]
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
    global async_weaviate_client, async_knowledgebase, async_openai_client, reference_agent, semantic_agent
    
    # Load client profiles into in-memory database
    client_profile_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "data", "profile", "client_profile.jsonl"
    )
    client_db.load_from_jsonl(client_profile_path)
    
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
    
    # Initialize semantic analysis agent
    semantic_agent = SemanticAnalysisAgent()
    
    # Reload client profile database
    CLIENT_PROFILE_DATA_PATH = os.getenv(
        "CLIENT_PROFILE_DATA_PATH", 
        "data/profile/client_profile.jsonl"
    )
    client_db.load_from_jsonl(CLIENT_PROFILE_DATA_PATH)
    logging.info(f"Reloaded {client_db.count()} client profiles from {CLIENT_PROFILE_DATA_PATH}")
    
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