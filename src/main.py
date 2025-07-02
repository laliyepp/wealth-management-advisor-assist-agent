#!/usr/bin/env python3
"""
Wealth Management Multi-Agent System

Main entry point for the agent orchestrator system.
"""

import asyncio

from agents.core.orchestrator import AgentOrchestrator
from services.database.manager import init_database


async def main():
    """Main entry point for the multi-agent system"""
    
    print("Starting Wealth Management Agent System...")
    
    try:
        # Initialize database
        init_database()
        print("Database initialized successfully")
        
        # Create and initialize the orchestrator
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize()
        print("Agent orchestrator initialized successfully")
        
        # Interactive loop
        print("\n=== Wealth Management Assistant ===")
        print("Type 'quit' or 'exit' to stop the system")
        print("Type 'help' for available commands")
        print("=" * 40)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Thank you for using the Wealth Management Assistant!")
                    break
                
                if user_input.lower() == 'help':
                    print_help()
                    continue
                
                if not user_input:
                    continue
                
                # Process the message with the orchestrator
                response = await orchestrator.process_message(user_input)
                
                # Show response with routing info
                selected_agent = response.metadata.get('selected_agent', 'unknown') if response.metadata else 'unknown'
                print(f"\nAssistant ({selected_agent}): {response.content}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Sorry, I encountered an error: {e}")
    
    except Exception as e:
        print(f"Critical error: {e}")
        return 1
    
    return 0


def print_help():
    """Print help information"""
    help_text = """
Available commands:
- help: Show this help message
- quit/exit/q: Exit the application

This is a multi-agent system that can:
✓ Route queries to specialized agents
✓ Handle general conversations and financial questions
✓ Store conversation history
✓ Use multiple LLM providers with fallback

Currently available agents:
• SimpleAgent: General assistance and basic conversations
"""
    print(help_text)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
