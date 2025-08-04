"""ReAct agent runner implementation."""

import asyncio
import logging
from typing import Any, Dict, Optional

from agents import RunConfig, Runner

from ..utils import pretty_print


class ReactRunner:
    """Runner for executing ReAct agent interactions."""
    
    def __init__(self, tracing_disabled: bool = False):
        """Initialize the ReAct runner.
        
        Args:
            tracing_disabled: Whether to disable tracing for faster execution
        """
        self.run_config = RunConfig(tracing_disabled=tracing_disabled)
        
    async def run_single_query(
        self, 
        agent: Any, 
        query: str, 
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Run a single query through the ReAct agent.
        
        Args:
            agent: The ReAct agent instance
            query: User query to process
            verbose: Whether to print intermediate steps
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            response = await Runner.run(
                agent,
                input=query,
                run_config=self.run_config,
            )
            
            if verbose:
                # Print intermediate items (tool calls, etc.)
                for item in response.new_items:
                    pretty_print(item.raw_item)
                    print()
                
                # Print final output
                pretty_print(response.final_output)
            
            return {
                "final_output": response.final_output,
                "items": [item.raw_item for item in response.new_items],
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logging.error(f"Error running ReAct agent query: {e}")
            return {
                "final_output": f"Error processing query: {str(e)}",
                "items": [],
                "success": False,
                "error": str(e)
            }
    
    async def run_interactive_session(
        self, 
        agent: Any,
        welcome_message: str = "ReAct Agent Ready. Ask me anything!",
        timeout_seconds: int = 60
    ) -> None:
        """Run an interactive session with the ReAct agent.
        
        Args:
            agent: The ReAct agent instance
            welcome_message: Welcome message to display
            timeout_seconds: Timeout for user input
        """
        print(f"\n{welcome_message}")
        print("Type 'quit' or 'exit' to end the session.\n")
        
        while True:
            try:
                # Get user input with timeout
                user_input = await asyncio.wait_for(
                    asyncio.to_thread(input, "You: "),
                    timeout=timeout_seconds,
                )
                
                # Check for exit commands
                if not user_input.strip() or user_input.lower() in {"quit", "exit"}:
                    print("Ending session. Goodbye!")
                    break
                
                # Process the query
                print("\nAgent:")
                result = await self.run_single_query(agent, user_input, verbose=True)
                
                if not result["success"]:
                    print(f"Error: {result['error']}")
                
                print("\n" + "="*50 + "\n")
                
            except asyncio.TimeoutError:
                print(f"\nNo input received within {timeout_seconds} seconds. Ending session.")
                break
            except KeyboardInterrupt:
                print("\nSession interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break
    
    async def run_streamed_query(
        self, 
        agent: Any, 
        query: str,
        verbose: bool = True
    ) -> None:
        """Run a query with streaming output.
        
        Args:
            agent: The ReAct agent instance
            query: User query to process
            verbose: Whether to print streaming events
        """
        try:
            from ..utils import oai_agent_stream_to_gradio_messages
            
            result_stream = Runner.run_streamed(
                agent, 
                input=query, 
                run_config=self.run_config
            )
            
            async for event in result_stream.stream_events():
                if verbose:
                    event_parsed = oai_agent_stream_to_gradio_messages(event)
                    if len(event_parsed) > 0:
                        pretty_print(event_parsed)
                        
        except Exception as e:
            logging.error(f"Error in streamed query: {e}")
            if verbose:
                print(f"Streaming error: {e}")


# Convenience function for quick agent execution
async def run_react_agent(query: str, agent_name: str = "ReAct Agent") -> Dict[str, Any]:
    """Convenience function to quickly run a ReAct agent query.
    
    Args:
        query: The query to process
        agent_name: Name for the agent
        
    Returns:
        Response dictionary
    """
    from .agent import create_react_agent
    
    agent = await create_react_agent(name=agent_name)
    runner = ReactRunner()
    
    return await runner.run_single_query(agent, query, verbose=False)