#!/usr/bin/env python3
"""Simple Gradio UI to test ReferenceToolsAgent."""

import asyncio
import logging
import os
import sys
from pathlib import Path

import gradio as gr

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from react.agents.meeting_intelligence.reference_tools import ReferenceToolsAgent
from utils.tools.cp_db import client_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load client profile database
CLIENT_PROFILE_DATA_PATH = os.getenv(
    "CLIENT_PROFILE_DATA_PATH",
    "data/profile/client_profile.jsonl"
)
client_db.load_from_jsonl(CLIENT_PROFILE_DATA_PATH)
logging.info(f"Loaded {client_db.count()} client profiles from {CLIENT_PROFILE_DATA_PATH}")

# Global agent instance
agent = None

async def initialize_agent():
    """Initialize the agent once."""
    global agent
    if agent is None:
        try:
            agent = ReferenceToolsAgent()
            await agent.initialize()
            return "✅ Agent initialized successfully!"
        except Exception as e:
            return f"❌ Agent initialization failed: {str(e)}"
    return "✅ Agent already initialized"

async def test_general_query(query: str):
    """Test general query processing."""
    global agent
    if agent is None:
        init_result = await initialize_agent()
        if "failed" in init_result:
            return init_result
    
    if not query.strip():
        return "Please enter a query"
    
    try:
        result = await agent.process_query(query)
        if result["success"]:
            return f"✅ **Success**\n\n{result['final_output']}"
        else:
            return f"❌ **Failed**: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"❌ **Exception**: {str(e)}"

async def test_client_profile(meeting_content: str):
    """Test client profile extraction from meeting content."""
    global agent
    if agent is None:
        init_result = await initialize_agent()
        if "failed" in init_result:
            return init_result
    
    if not meeting_content.strip():
        return "Please enter meeting content"
    
    try:
        result = await agent.analyze_meeting_for_client_profile(meeting_content)
        if result["success"]:
            return f"✅ **Client Profile Analysis**\n\n{result['final_output']}"
        else:
            return f"❌ **Failed**: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"❌ **Exception**: {str(e)}"

async def test_stock_prices(meeting_transcript: str):
    """Test stock price extraction from meeting transcript."""
    global agent
    if agent is None:
        init_result = await initialize_agent()
        if "failed" in init_result:
            return init_result
    
    if not meeting_transcript.strip():
        return "Please enter meeting transcript"
    
    try:
        result = await agent.extract_stock_prices(meeting_transcript)
        if result["success"]:
            return f"✅ **Stock Price Analysis**\n\n{result['final_output']}"
        else:
            return f"❌ **Failed**: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"❌ **Exception**: {str(e)}"

def create_gradio_interface():
    """Create the Gradio interface."""
    
    with gr.Blocks(title="Reference Tools Agent Tester") as interface:
        gr.Markdown("# 🧪 Reference Tools Agent Tester")
        gr.Markdown("Test the ReferenceToolsAgent with client profiles and stock price tools.")
        
        with gr.Tab("General Query"):
            gr.Markdown("### Test any query - let the agent decide which tools to use")
            
            query_input = gr.Textbox(
                label="Query",
                placeholder="Ask about clients or stock prices...",
                lines=2,
                value="What client profiles are available?"
            )
            query_button = gr.Button("Process Query", variant="primary")
            query_output = gr.Markdown(label="Result")
            
            def run_general_query(query):
                return asyncio.run(test_general_query(query))
            
            query_button.click(
                fn=run_general_query,
                inputs=query_input,
                outputs=query_output
            )
            
            gr.Examples(
                examples=[
                    ["What client profiles are available?"],
                    ["Get information about client John"],
                    ["What is the current price of AAPL?"],
                    ["Show me details for client Sarah"]
                ],
                inputs=query_input
            )
        
        with gr.Tab("Client Profile Analysis"):
            gr.Markdown("### Extract client profile from meeting content")
            
            meeting_input = gr.Textbox(
                label="Meeting Content",
                placeholder="Enter meeting transcript or content...",
                lines=5,
                value="Today I met with John to discuss his investment portfolio. He mentioned wanting to diversify his holdings."
            )
            profile_button = gr.Button("Analyze Client Profile", variant="primary")
            profile_output = gr.Markdown(label="Client Profile Result")
            
            def run_client_profile(content):
                return asyncio.run(test_client_profile(content))
            
            profile_button.click(
                fn=run_client_profile,
                inputs=meeting_input,
                outputs=profile_output
            )
            
            gr.Examples(
                examples=[
                    ["Today I met with John to discuss his retirement planning."],
                    ["Sarah called about her investment concerns and risk tolerance."],
                    ["Meeting with Michael regarding his portfolio diversification strategy."]
                ],
                inputs=meeting_input
            )
        
        with gr.Tab("Stock Price Analysis"):
            gr.Markdown("### Extract stock prices from meeting transcript")
            
            transcript_input = gr.Textbox(
                label="Meeting Transcript",
                placeholder="Enter transcript with stock mentions...",
                lines=5,
                value="We discussed Apple Inc. (AAPL) and how it's performing. Also mentioned Tesla (TSLA) as a growth option."
            )
            price_button = gr.Button("Extract Stock Prices", variant="primary")
            price_output = gr.Markdown(label="Stock Price Result")
            
            def run_stock_prices(transcript):
                return asyncio.run(test_stock_prices(transcript))
            
            price_button.click(
                fn=run_stock_prices,
                inputs=transcript_input,
                outputs=price_output
            )
            
            gr.Examples(
                examples=[
                    ["Client wants to buy Apple Inc. (AAPL) and Microsoft (MSFT)."],
                    ["We discussed Tesla (TSLA), Google (GOOGL), and Amazon (AMZN)."],
                    ["Looking at tech stocks like Meta (META) and Netflix (NFLX)."]
                ],
                inputs=transcript_input
            )
        
        with gr.Tab("System Status"):
            gr.Markdown("### Agent initialization and status")
            
            init_button = gr.Button("Initialize Agent", variant="secondary")
            status_output = gr.Markdown("Agent not initialized")
            
            def run_initialize():
                return asyncio.run(initialize_agent())
            
            init_button.click(
                fn=run_initialize,
                outputs=status_output
            )
            
            gr.Markdown("""
            **Environment Variables Needed:**
            - `TWELVEDATA_API_KEY`: For stock price data
            - `CLIENT_PROFILES_PATH`: Path to client profiles JSONL file
            - `OPENAI_API_KEY`: For OpenAI models
            """)
    
    return interface

if __name__ == "__main__":
    # Check environment
    missing_vars = []
    required_vars = ["OPENAI_API_KEY"]
    optional_vars = ["TWELVEDATA_API_KEY", "CLIENT_PROFILES_PATH"]
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        print("The application may not work properly.")
    
    optional_missing = [var for var in optional_vars if not os.getenv(var)]
    if optional_missing:
        print(f"ℹ️  Optional environment variables not set: {', '.join(optional_missing)}")
        print("Some features may be limited.")
    
    print("🚀 Starting Gradio interface...")
    
    interface = create_gradio_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )