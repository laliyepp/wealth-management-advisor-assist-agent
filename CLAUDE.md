# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a wealth management advisor assistant agent built with Python. The project implements a conversational AI agent that can interact with users about financial topics using multi-provider LLM integration. It supports OpenAI, Anthropic, and OpenRouter APIs with intelligent fallback mechanisms and configurable model selection.

## Commands

### Running the Application
```bash
python src/main.py
```

### Testing
```bash
pytest tests/
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### Core Components

- **Agent System**: Modular agent architecture with base classes and implementations
  - `src/agent/base.py`: Abstract base classes for agents, messages, and responses with LLM provider interface
  - `src/agent/simple_agent.py`: Main agent implementation with multi-provider LLM support and fallback logic
  - `src/agent/llm_providers.py`: LLM provider abstraction layer with concrete implementations for OpenAI, Anthropic, and OpenRouter
  
- **Configuration Management**: Settings handled via Pydantic with environment variable support
  - `src/config/settings.py`: Application settings with multi-provider API key management and model configuration
  - Supports `.env` file for configuration
  - Provider selection and fallback chain configuration
  
- **Database Layer**: SQLAlchemy-based data persistence
  - `src/data/database.py`: Database manager with session handling, backup, and utility methods
  - `src/data/models.py`: Database models for conversation history storage
  - Default: SQLite database (`agent.db`)

### Key Features

- **Multi-Provider LLM Integration**: Supports OpenAI, Anthropic, and OpenRouter APIs with configurable models
- **Intelligent Fallback System**: Primary provider with configurable fallback chain for resilience
- **Model Flexibility**: Different models per provider (e.g., DeepSeek via OpenRouter, Claude via Anthropic)
- **Conversation History**: Persistent storage of user interactions
- **Interactive CLI**: Command-line interface with help system
- **Database Management**: Full CRUD operations with backup capabilities
- **Modular Design**: Extensible agent system and provider architecture for adding new capabilities

### Configuration

#### LLM Provider Configuration
The system supports multiple LLM providers with fallback mechanisms:

**API Keys** (all optional):
- `OPENAI_API_KEY`: OpenAI API access
- `ANTHROPIC_API_KEY`: Anthropic Claude API access  
- `OPENROUTER_API_KEY`: OpenRouter API access (supports hundreds of models)

**Provider Selection**:
- `LLM_PROVIDER`: Primary provider (`openai`, `anthropic`, `openrouter`) - defaults to `openrouter`
- `FALLBACK_PROVIDERS`: Comma-separated fallback providers - defaults to `openai`

**Model Configuration**:
- `OPENAI_MODEL`: OpenAI model - defaults to `gpt-3.5-turbo`
- `ANTHROPIC_MODEL`: Anthropic model - defaults to `claude-3-sonnet-20240229`
- `OPENROUTER_MODEL`: OpenRouter model - defaults to `deepseek/deepseek-chat-v3-0324:free`

**General Settings**:
- `TEMPERATURE`: Model temperature (0.0-1.0) - defaults to `0.7`
- `MAX_TOKENS`: Maximum response tokens - defaults to `2048`
- `DATABASE_URL`: Database connection string - defaults to SQLite

#### Provider Architecture
- **BaseLLMProvider**: Abstract interface for all LLM providers
- **OpenAIProvider**: Direct OpenAI API integration
- **AnthropicProvider**: Anthropic Claude API integration
- **OpenRouterProvider**: OpenRouter API integration (supports 100+ models)
- **LLMProviderFactory**: Factory pattern for provider instantiation
- **Fallback Logic**: Automatic failover when primary provider fails

### Entry Points

- `src/main.py`: Main application entry point with async CLI loop
- Interactive commands: `help`, `quit`/`exit`/`q`
- Database initialization happens automatically on startup
- Provider initialization with fallback chain setup occurs during agent creation

## Multi-Agent System Expansion Plan

### Overview
Evolution from single-agent to multi-agent system where a master agent orchestrates specialized sub-agents for different tasks.

### High-Level Architecture

#### Current State
- Single `SimpleAgent` processes all user requests directly
- Existing `BaseAgent` provides solid foundation for expansion

#### Target Architecture
**Master Agent (Orchestrator)**
- Inherits from existing `BaseAgent`
- Receives user requests and routes to appropriate sub-agents
- Aggregates responses from multiple sub-agents
- Maintains conversation context across agent interactions

**Agent Registry**
- Central registry tracking available sub-agents
- Maps agent capabilities to specific domains/tasks
- Handles agent discovery and instantiation

**Sub-Agent Framework**
- All sub-agents inherit from `BaseAgent` (reusing existing infrastructure)
- Each sub-agent declares its capabilities/domains
- Sub-agents can be invoked independently or in combination

**Task Routing System**
- Master agent analyzes incoming requests
- Routes tasks to appropriate sub-agent(s) based on content/intent
- Handles multi-agent workflows when tasks require multiple agents

#### Architecture Flow
```
User → MasterAgent → AgentRegistry → SubAgent → Response → MasterAgent → User
```

### Implementation Plan

#### Phase 1: Core Multi-Agent Infrastructure
1. **Create Agent Registry**
   - `AgentRegistry` class to track available sub-agents
   - Agent capability mapping (what each agent can handle)
   - Agent factory for instantiation

2. **Build Master Agent**
   - `MasterAgent` class extending `BaseAgent`
   - Task routing logic to determine which sub-agent to use
   - Result aggregation from multiple sub-agents

3. **Extend Base Agent**
   - Add agent capability declaration
   - Add agent registration mechanism
   - Maintain existing LLM provider integration

4. **Update Main Entry Point**
   - Replace `SimpleAgent` with `MasterAgent`
   - Initialize agent registry and register sub-agents
   - Keep existing CLI interface

### Design Patterns & Best Practices

#### Industry References
- **Microsoft AutoGen Framework**: Orchestrator pattern with specialized agents
- **LangChain Multi-Agent Systems**: Agent composition with central coordinator
- **CrewAI Framework**: Master-worker pattern for collaborative AI systems
- **Enterprise Service Mesh**: Similar to Kubernetes microservices management

#### Real-World Applications
- **Goldman Sachs**: Multi-agent trading strategy systems
- **BlackRock**: Agent-based portfolio management
- **Robinhood**: Multi-agent fraud detection and compliance
- **Wealthfront**: Automated financial planning with specialized agents

#### Key Benefits
1. **Separation of Concerns**: Each agent has single responsibility
2. **Scalability**: Easy to add new specialized agents
3. **Maintainability**: Changes to one agent don't affect others
4. **Testability**: Each agent can be tested independently
5. **Modularity**: Agents can be developed by different teams

### Implementation Notes
- Maintains existing code structure through composition rather than major refactoring
- Preserves all current LLM provider integration and fallback mechanisms
- Keeps existing CLI interface and user experience
- Builds upon proven architectural patterns used in production financial AI systems