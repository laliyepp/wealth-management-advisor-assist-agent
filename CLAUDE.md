# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a wealth management advisor assistant agent built with Python using the ReAct (Reasoning-Action-Observation) framework. The project implements a sophisticated AI agent that can interact with users about financial topics using knowledge base search, structured reasoning, and tool usage. It's built on the OpenAI Agent SDK with Weaviate vector database integration and Langfuse observability.

## Commands

### Running the Application

#### CLI Mode (Interactive Command Line)
```bash
python -m src.main cli
# or simply
python -m src.main
```

#### Web Interface (Gradio)
```bash
python -m src.main gradio
```

#### Knowledge Base Search Demo
```bash
python -m src.main search
```

#### Help
```bash
python -m src.main help
```

### Environment Setup
```bash
# Using uv (recommended)
uv venv
uv sync

# Traditional approach
pip install -e .
```

### Development Tools
```bash
# Code formatting and linting
uv run ruff format .
uv run ruff check .

# Testing
uv run pytest tests/

# Documentation
uv run mkdocs serve
```

## Architecture

### Core Components

- **ReAct Framework**: Reasoning-Action-Observation agent architecture
  - `src/react/agent.py`: ReAct agent implementation using OpenAI Agent SDK
  - `src/react/runner.py`: Agent execution and interaction management
  - `src/react/tools/`: Tool registry and implementations
  
- **Knowledge Base Integration**: Vector database for knowledge retrieval
  - Weaviate vector database for semantic search
  - `src/utils/tools/kb_weaviate.py`: Weaviate knowledge base client
  - Collection: `enwiki_20250520` (Wikipedia knowledge base)
  
- **Utilities Framework**: Comprehensive utility ecosystem from agent-bootcamp
  - `src/utils/`: Complete utilities package with async support, logging, environment configuration
  - `src/utils/async_utils.py`: Rate limiting and progress tracking
  - `src/utils/env_vars.py`: Pydantic-based environment configuration
  - `src/utils/langfuse/`: Observability and tracing integration
  - `src/utils/gradio/`: Web interface utilities

- **Interface Options**: Multiple interaction modes
  - CLI: Interactive command-line interface with ReAct reasoning display
  - Gradio: Web-based chat interface with streaming responses
  - Search Demo: Simple knowledge base search with JSON output (like agent-bootcamp)
  - `src/gradio_ui.py`: Web interface implementation
  - `src/search_demo.py`: Knowledge base search demo

### Key Features

- **ReAct Framework**: Structured reasoning with explicit action planning and observation
- **Knowledge Base Search**: Semantic search through Weaviate vector database
- **Observability**: Full tracing and monitoring via Langfuse integration
- **Multi-Interface Support**: CLI and web interfaces for different use cases
- **Streaming Responses**: Real-time response generation with intermediate step display
- **Modern Python Stack**: Python 3.12, uv for dependency management, ruff for code quality

### Technology Stack

#### Core Dependencies
- **OpenAI Agent SDK**: Agent framework and tool integration
- **Weaviate**: Vector database for knowledge retrieval
- **Gradio**: Web interface for interactive chat
- **Langfuse**: Observability and tracing
- **Rich**: Enhanced terminal output and progress bars

#### Development Stack
- **Python 3.12**: Modern Python with pyenv version management
- **uv**: Fast Python package installer and resolver
- **ruff**: Python linter and formatter
- **pytest**: Testing framework with async support
- **mkdocs**: Documentation generation

### Configuration

#### Environment Variables (from .env)
```bash
# OpenAI-compatible LLM
OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
OPENAI_API_KEY="..."

# Embedding model
EMBEDDING_MODEL_NAME="@cf/baai/bge-m3"
EMBEDDING_BASE_URL="https://api.cloudflare.com/client/v4/accounts/.../ai/v1"
EMBEDDING_API_KEY="..."

# Langfuse Observability
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_HOST="https://us.cloud.langfuse.com"

# Weaviate Vector Database
WEAVIATE_HTTP_HOST="...weaviate.cloud"
WEAVIATE_GRPC_HOST="grpc-...weaviate.cloud"
WEAVIATE_API_KEY="..."
WEAVIATE_HTTP_PORT="443"
WEAVIATE_GRPC_PORT="443"
WEAVIATE_HTTP_SECURE="true"
WEAVIATE_GRPC_SECURE="true"
```

#### Agent Configuration
- **Model**: `gemini-2.5-flash` (via OpenAI-compatible API)
- **Instructions**: ReAct framework with knowledge search emphasis
- **Tools**: Weaviate knowledge base search, news events (extensible)
- **Tracing**: Disabled by default for performance (can be enabled)

### Entry Points

- `src/main.py`: Main application with CLI/Gradio mode selection
- `src/gradio_ui.py`: Standalone Gradio web interface
- `src/react/`: ReAct framework implementation

### Development Workflow

1. **Environment Setup**: Use pyenv for Python 3.12, uv for dependencies
2. **Code Quality**: ruff for formatting and linting (configured in pyproject.toml)
3. **Testing**: pytest with async support for agent interactions
4. **Documentation**: mkdocs for project documentation
5. **Observability**: Langfuse integration for production monitoring

### Project Structure
```
├── .python-version          # Python 3.12.3
├── pyproject.toml          # Project configuration and dependencies
├── uv.lock                 # Locked dependencies
├── .env                    # Environment configuration
├── src/
│   ├── utils/              # Agent-bootcamp utilities
│   │   ├── async_utils.py
│   │   ├── env_vars.py
│   │   ├── langfuse/       # Observability
│   │   ├── gradio/         # Web interface utilities
│   │   └── tools/          # Knowledge base and tools
│   ├── prompts.py          # ReAct instructions
│   ├── react/              # ReAct framework
│   │   ├── agent.py        # Agent implementation
│   │   ├── runner.py       # Execution management
│   │   └── tools/          # Tool registry
│   ├── gradio_ui.py        # Web interface
│   └── main.py             # Application entry point
├── tests/                  # Test suite
└── docs/                   # Documentation
```

This architecture provides a modern, scalable foundation for building sophisticated financial advisory agents with structured reasoning, knowledge retrieval, and comprehensive observability.