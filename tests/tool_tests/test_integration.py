"""Integration tests for Wealth Management ReAct Agent System."""

import json
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from langfuse import get_client
from openai import AsyncOpenAI

from src.utils import (
    AsyncWeaviateKnowledgeBase,
    Configs,
    get_weaviate_async_client,
    pretty_print,
)
from src.utils.langfuse.otlp_env_setup import set_up_langfuse_otlp_env_vars
from src.react.agent import ReactAgentManager, create_react_agent
from src.react.runner import ReactRunner


load_dotenv(verbose=True)


@pytest.fixture()
def configs():
    """Load env var configs for testing."""
    return Configs.from_env_var()


@pytest_asyncio.fixture()
async def weaviate_kb(
    configs: Configs,
) -> AsyncGenerator[AsyncWeaviateKnowledgeBase, None]:
    """Weaviate knowledgebase for testing."""
    async_client = get_weaviate_async_client(
        http_host=configs.weaviate_http_host,
        http_port=configs.weaviate_http_port,
        http_secure=configs.weaviate_http_secure,
        grpc_host=configs.weaviate_grpc_host,
        grpc_port=configs.weaviate_grpc_port,
        grpc_secure=configs.weaviate_grpc_secure,
        api_key=configs.weaviate_api_key,
    )

    yield AsyncWeaviateKnowledgeBase(
        async_client=async_client, collection_name="rbc_2_cra_public_documents"
    )

    await async_client.close()


@pytest_asyncio.fixture()
async def react_agent_manager() -> AsyncGenerator[ReactAgentManager, None]:
    """ReAct agent manager for testing."""
    manager = ReactAgentManager()
    await manager.initialize("Test Wealth Management Agent")
    yield manager
    await manager.cleanup()


def test_vectorizer(weaviate_kb: AsyncWeaviateKnowledgeBase) -> None:
    """Test vectorizer integration."""
    vector = weaviate_kb._vectorize("What are diversified investment portfolios?")
    assert vector is not None
    assert len(vector) > 0
    print(f"Vector ({len(vector)} dimensions): {vector[:10]}...")


@pytest.mark.asyncio
async def test_weaviate_kb(weaviate_kb: AsyncWeaviateKnowledgeBase) -> None:
    """Test weaviate knowledgebase integration with financial query."""
    responses = await weaviate_kb.search_knowledgebase("What are ETFs and how do they work?")
    assert len(responses) > 0
    print(f"Found {len(responses)} results for ETF query")
    pretty_print(responses)


@pytest.mark.asyncio
async def test_weaviate_kb_tool_and_llm(
    weaviate_kb: AsyncWeaviateKnowledgeBase,
) -> None:
    """Test weaviate knowledgebase tool integration and LLM API with financial context."""
    query = "What are the benefits of dividend investing?"
    search_results = await weaviate_kb.search_knowledgebase(query)
    assert len(search_results) > 0

    client = AsyncOpenAI()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a wealth management advisor. Answer the question using the provided "
                "information from a knowledge base, focusing on practical financial advice."
            ),
        },
        {
            "role": "user",
            "content": f"{query}\n\nKnowledge base information:\n{
                json.dumps([_result.model_dump() for _result in search_results])
            }",
        },
    ]
    response = await client.chat.completions.create(
        model="gemini-2.5-flash", messages=messages
    )
    message = response.choices[0].message
    assert message.role == "assistant"
    assert len(message.content) > 0
    messages.append(message.model_dump())
    print("LLM Response to financial query:")
    pretty_print(messages[-1]["content"])


@pytest.mark.asyncio
async def test_react_agent_creation() -> None:
    """Test ReAct agent creation and basic functionality."""
    agent = await create_react_agent(name="Test Agent")
    assert agent is not None
    assert agent.name == "Test Agent"
    print("✓ ReAct agent created successfully")


@pytest.mark.asyncio
async def test_react_agent_manager(react_agent_manager: ReactAgentManager) -> None:
    """Test ReAct agent manager initialization and agent retrieval."""
    assert react_agent_manager.initialized
    agent = react_agent_manager.get_agent()
    assert agent is not None
    assert agent.name == "Test Wealth Management Agent"
    print("✓ ReAct agent manager working correctly")


@pytest.mark.asyncio
async def test_react_runner_query() -> None:
    """Test ReAct runner with a simple financial query."""
    agent = await create_react_agent(name="Test Financial Agent")
    runner = ReactRunner(tracing_disabled=True)
    
    query = "What is compound interest?"
    result = await runner.run_single_query(agent, query, verbose=False)
    
    assert result["success"] is True
    assert "final_output" in result
    assert len(result["final_output"]) > 0
    print(f"✓ ReAct agent successfully answered: '{query}'")
    print(f"Response: {result['final_output'][:100]}...")


@pytest.mark.asyncio
async def test_full_react_system_integration() -> None:
    """Test full ReAct system with agent manager and runner."""
    # Initialize agent manager
    manager = ReactAgentManager()
    await manager.initialize("Integration Test Agent")
    
    try:
        # Create runner
        runner = ReactRunner(tracing_disabled=True)
        
        # Test financial query
        query = "What are the key principles of portfolio diversification?"
        result = await runner.run_single_query(manager.get_agent(), query, verbose=False)
        
        # Verify results
        assert result["success"] is True
        assert "final_output" in result
        assert len(result["final_output"]) > 0
        assert len(result["items"]) > 0  # Should have tool call items
        
        print("✓ Full ReAct system integration test passed")
        print(f"Query: {query}")
        print(f"Response length: {len(result['final_output'])} characters")
        print(f"Tool interactions: {len(result['items'])}")
        
    finally:
        await manager.cleanup()


def test_langfuse() -> None:
    """Test LangFuse integration for observability."""
    set_up_langfuse_otlp_env_vars()
    langfuse_client = get_client()

    assert langfuse_client.auth_check()
    print("✓ Langfuse authentication successful")


@pytest.mark.asyncio
async def test_wealth_management_specific_queries(weaviate_kb: AsyncWeaviateKnowledgeBase) -> None:
    """Test knowledge base with wealth management specific queries."""
    financial_queries = [
        "What is asset allocation?",
        "How do mutual funds work?",
        "What are the risks of investing in stocks?",
        "What is a 401k retirement plan?",
    ]
    
    for query in financial_queries:
        responses = await weaviate_kb.search_knowledgebase(query)
        assert len(responses) > 0, f"No results found for query: {query}"
        print(f"✓ Found {len(responses)} results for: {query}")


# Integration test for environment setup
def test_environment_setup(configs: Configs) -> None:
    """Test that all required environment variables are properly configured."""
    # Test Weaviate configuration
    assert configs.weaviate_http_host
    assert configs.weaviate_api_key
    assert configs.weaviate_http_port == 443
    
    # Test embedding configuration
    assert configs.embedding_base_url
    assert configs.embedding_api_key
    
    # Test Langfuse configuration
    assert configs.langfuse_public_key
    assert configs.langfuse_secret_key
    assert configs.langfuse_host
    
    print("✓ All environment variables properly configured")