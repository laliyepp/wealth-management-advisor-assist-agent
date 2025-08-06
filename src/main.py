#!/usr/bin/env python3
"""
Wikipedia Knowledge Search Agent

A ReAct-powered agent for searching and answering questions using Wikipedia knowledge base.
"""

import argparse
import asyncio
import logging
import sys

from dotenv import load_dotenv

from .react.agent import ReactAgentManager
from .react.runner import ReactRunner
from .utils import set_up_logging, setup_langfuse_tracer


load_dotenv(verbose=True)


async def main_cli():
    """Main CLI entry point for the ReAct agent system."""
    
    print("Starting Wikipedia Knowledge Search Agent...")
    
    # Set up logging
    set_up_logging()
    
    # Set up Langfuse tracing with full instrumentation
    setup_langfuse_tracer("wealth-management-cli")
    
    try:
        # Initialize the ReAct agent
        agent_manager = ReactAgentManager()
        await agent_manager.initialize("Wikipedia Search Agent")
        print("ReAct agent initialized successfully")
        
        # Create runner
        runner = ReactRunner(tracing_disabled=False)
        
        # Run interactive session
        await runner.run_interactive_session(
            agent_manager.get_agent(),
            welcome_message="=== Wealth Management ReAct Assistant ===\nI'm a ReAct-powered agent that can help with financial questions using knowledge search.",
            timeout_seconds=60
        )
        
    except Exception as e:
        print(f"Critical error: {e}")
        logging.error(f"Critical error in main: {e}")
        return 1
    finally:
        # Cleanup
        if 'agent_manager' in locals():
            await agent_manager.cleanup()
    
    return 0


def main_gradio():
    """Launch the Gradio web interface."""
    from .gradio_ui import launch_gradio_app
    
    print("Starting Wealth Management Agent Web Interface...")
    launch_gradio_app()


def main_search():
    """Launch the Knowledge Base Search Demo."""
    from .search_demo import demo
    
    print("Starting Knowledge Base Search Demo...")
    demo.launch(server_name="0.0.0.0")


def print_help():
    """Print help information."""
    help_text = """
Wealth Management ReAct Agent System

Usage:
  python -m src.main [mode]

Modes:
  cli     - Run interactive command-line interface (default)
  gradio  - Launch web interface with Gradio
  search  - Launch knowledge base search demo
  help    - Show this help message

Features:
✓ ReAct (Reasoning-Action-Observation) framework
✓ Knowledge base search using Weaviate
✓ Financial question answering
✓ Interactive CLI and web interfaces
✓ Structured thinking and tool usage

Examples:
  python -m src.main cli        # Start CLI interface
  python -m src.main gradio     # Start web interface
  python -m src.main search     # Start search demo
"""
    print(help_text)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Wealth Management ReAct Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["cli", "gradio", "search", "help"],
        default="cli",
        help="Operation mode: cli (default), gradio, search, or help"
    )
    
    args = parser.parse_args()
    
    if args.mode == "help":
        print_help()
        return 0
    elif args.mode == "gradio":
        main_gradio()
        return 0
    elif args.mode == "search":
        main_search()
        return 0
    elif args.mode == "cli":
        return asyncio.run(main_cli())
    else:
        print(f"Unknown mode: {args.mode}")
        print_help()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)