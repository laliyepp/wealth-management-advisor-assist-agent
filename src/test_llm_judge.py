#!/usr/bin/env python3
"""Test script for LLMJudgeAgent."""

import asyncio
import logging
import os
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.react.agents.meeting_intelligence.llm_judge import LLMJudgeAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Sample meeting content for testing
SAMPLE_MEETING_CONTENT_1 = """
Meeting with John Smith on 2024-01-15.

John mentioned he's 45 years old and works as a software engineer. He's looking to diversify his investment portfolio 
and is interested in retiring around age 65. He has about $150,000 in savings and contributes $2,000 monthly.
John prefers moderate risk investments and is interested in a 70/30 stock-bond allocation.
He mentioned he has some real estate investments and is interested in ESG funds.
John also mentioned he needs to start planning for his children's education expenses.
"""

SAMPLE_MEETING_CONTENT_2 = """
Met with Sarah Johnson today. She's a marketing manager in her 30s who wants investment advice.
Sarah is very risk-averse and prefers conservative investments. She has $50,000 to invest
and wants to focus on bonds and stable funds. She mentioned she's planning to buy a house in 5 years.
"""

async def test_llm_judge_agent():
    """Test the LLMJudgeAgent with different scenarios."""
    print("🧪 Testing LLMJudgeAgent...")
    
    # Create judge agent
    judge = LLMJudgeAgent()
    
    try:
        # Initialize agent
        print("📋 Initializing LLM judge agent...")
        await judge.initialize()
        print("✅ Judge agent initialized successfully")
        
        # Test cases with different scenarios
        test_cases = [
            {
                "name": "Test 1: Existing client (John)",
                "meeting_content": SAMPLE_MEETING_CONTENT_1,
                "client_name": "John",
                "description": "Testing with client that should exist in database"
            },
            {
                "name": "Test 2: Non-existing client (Sarah)", 
                "meeting_content": SAMPLE_MEETING_CONTENT_2,
                "client_name": "Sarah",
                "description": "Testing with client that may not exist in database"
            },
            {
                "name": "Test 3: Empty meeting content",
                "meeting_content": "",
                "client_name": "John",
                "description": "Testing with empty meeting content"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 {test_case['name']}")
            print(f"Description: {test_case['description']}")
            print(f"Client: {test_case['client_name']}")
            print(f"Meeting content length: {len(test_case['meeting_content'])} chars")
            
            try:
                # Run evaluation
                result = await judge.evaluate_client_profile_extraction(
                    meeting_content=test_case['meeting_content'],
                    client_name=test_case['client_name']
                )
                
                # Display results
                if result.success:
                    print(f"✅ Success!")
                    print(f"📊 Score: {result.score}/10")
                    print(f"💭 Reason: {result.reason}")
                    print(f"👤 Client: {result.client_name}")
                    
                    # Show generated vs reference (truncated)
                    if len(result.generated_answer or '') > 100:
                        print(f"🤖 Generated (first 100 chars): {result.generated_answer[:100]}...")
                    else:
                        print(f"🤖 Generated: {result.generated_answer or 'N/A'}")
                    
                    if len(result.reference_answer or '') > 100:
                        print(f"📚 Reference (first 100 chars): {result.reference_answer[:100]}...")
                    else:
                        print(f"📚 Reference: {result.reference_answer or 'N/A'}")
                        
                else:
                    print(f"❌ Failed: {result.error or 'Unknown error'}")
                    print(f"💭 Reason: {result.reason or 'N/A'}")
                    
            except Exception as e:
                print(f"❌ Test exception: {str(e)}")
        
        # Test with actual database check
        print(f"\n🔍 Test 4: Database connectivity check")
        try:
            from src.utils.tools.cp_db import client_db, get_client_profile
            
            print(f"Database loaded: {client_db.is_loaded()}")
            print(f"Profile count: {client_db.count()}")
            
            if client_db.count() > 0:
                profile_names = client_db.get_profile_names()
                print(f"Available profiles: {profile_names[:3]}..." if len(profile_names) > 3 else f"Available profiles: {profile_names}")
                
                # Try with first available profile
                if profile_names:
                    first_name = profile_names[0].split()[0]  # Get first name
                    print(f"\n🔍 Test 5: Real client evaluation ({first_name})")
                    
                    # Create realistic meeting content for this client
                    realistic_meeting = f"""
                    Meeting with {first_name} today. We discussed their investment goals and current financial situation.
                    {first_name} wants to review their portfolio allocation and risk tolerance.
                    They mentioned concerns about retirement planning and diversification.
                    """
                    
                    result = await judge.evaluate_client_profile_extraction(
                        meeting_content=realistic_meeting,
                        client_name=first_name
                    )
                    
                    if result.success:
                        print(f"✅ Real client evaluation successful!")
                        print(f"📊 Score: {result.score}/10")
                        print(f"💭 Reason: {result.reason}")
                    else:
                        print(f"❌ Real client evaluation failed: {result.error or 'Unknown'}")
            
        except ImportError as e:
            print(f"⚠️ Database import error: {e}")
        except Exception as e:
            print(f"⚠️ Database test error: {e}")
        
    except Exception as e:
        print(f"❌ Judge agent initialization or testing failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    finally:
        # Cleanup
        try:
            await judge.close()
            print("\n🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {str(e)}")

async def test_judge_components():
    """Test individual components of the judge agent."""
    print("\n🔧 Testing judge components...")
    
    judge = LLMJudgeAgent()
    
    # Test reference data formatting
    sample_reference_data = {
        "client_identification": {
            "full_name": "John Smith",
            "age": 45,
            "gender": "M",
            "citizenship": "USA",
            "residency": "USA",
            "occupation": "Software Engineer"
        },
        "financial_situation": {
            "annual_income": 120000,
            "income_stability": "stable",
            "monthly_savings_rate": 2000,
            "external_asset_value": 150000,
            "tax_complexity_rating": 3
        },
        "investment_profile": {
            "risk_tolerance": 6,
            "risk_capacity": 7,
            "investment_experience_years": 10,
            "primary_goal": "retirement",
            "time_horizon_years": 20,
            "liquidity_needs": "medium"
        }
    }
    
    formatted_ref = judge._format_reference_data(sample_reference_data)
    print(f"📄 Formatted reference data: {formatted_ref}")
    
    # Test prompt preparation
    generated_answer = "John Smith is a 45-year-old software engineer looking for retirement planning."
    prompt = judge._prepare_evaluation_prompt(generated_answer, formatted_ref)
    print(f"\n📝 Sample evaluation prompt length: {len(prompt)} chars")
    print(f"Prompt preview: {prompt[:200]}...")
    
    # Test JSON parsing
    sample_json_responses = [
        '{"score": 8, "reason": "Good match with minor details missing"}',
        'Score: 6\nReason: Partially correct information',
        'The score is 7 out of 10 because the answer covers most key points but lacks financial details.',
        '{"score": "9", "reason": "Nearly perfect match"}'  # Score as string
    ]
    
    print(f"\n🔍 Testing JSON parsing:")
    for i, response in enumerate(sample_json_responses, 1):
        parsed = judge._parse_json_response(response)
        print(f"Test {i}: {parsed}")

if __name__ == "__main__":
    print("🚀 Starting LLMJudgeAgent tests...\n")
    asyncio.run(test_llm_judge_agent())
    asyncio.run(test_judge_components())