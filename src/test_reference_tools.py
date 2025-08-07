#!/usr/bin/env python3
"""Test script for ReferenceToolsAgent."""

import asyncio
import logging
import os
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.react.agents.meeting_intelligence.reference_tools import ReferenceToolsAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_reference_tools_agent():
    """Test the ReferenceToolsAgent."""
    print("🧪 Testing ReferenceToolsAgent...")
    
    # Create agent
    agent = ReferenceToolsAgent()
    
    try:
        # Initialize agent
        print("📋 Initializing agent...")
        await agent.initialize()
        print("✅ Agent initialized successfully")
        
        # Test queries
        test_queries = [
            "What client profiles are available?",
            "Get information about client John",
            "What is the current price of AAPL?",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            try:
                result = await agent.process_query(query)
                if result["success"]:
                    print(f"✅ Success: {result['final_output'][:200]}...")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {str(e)}")
    
    finally:
        # Cleanup
        try:
            await agent.close()
            print("\n🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_reference_tools_agent())