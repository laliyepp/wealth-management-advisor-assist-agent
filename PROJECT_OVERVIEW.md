# PROJECT OVERVIEW - Wealth Management Advisor Assistant Agent

## Executive Summary

**Project Name**: Wealth Management Advisor Assistant Agent  
**Architecture**: ReAct (Reasoning-Action-Observation-Response) Framework  
**Primary Technology**: OpenAI SDK Agents with Weaviate Knowledge Base  
**Language**: Python 3.12+  
**Purpose**: AI-powered financial advisory system for wealth management guidance using knowledge base search and structured reasoning

## System Architecture

### Core Components

#### 1. ReAct Agent System (`src/react/`)
- **agent.py**: Core agent implementation with three types:
  - `create_react_agent()`: Knowledge base search agent using Weaviate + Twelve Data financial tools
  - `create_web_search_agent()`: Google's native Gemini API with real-time web search grounding
  - `WebSearchAgent`: Native Google Search implementation with grounding metadata
- **runner.py**: Agent execution runner with:
  - Single query execution
  - Interactive sessions
  - Streaming support
- **AgentManager**: Lifecycle management for agents supporting both ReAct and WebSearch types

#### 2. Knowledge Base Integration (`src/utils/tools/`)
- **Weaviate Vector Database** (`kb_weaviate.py`): 
  - Collection: `rbc_2_cra_public_documents` (Canadian Revenue Agency documents)
  - Hybrid search (keyword + vector)
  - Embedding model: `@cf/baai/bge-m3`
  - **AsyncWeaviateKnowledgeBase**: Async search interface with rate limiting
- **Twelve Data Financial API** (`twelve_data.py`):
  - **AsyncFinancialDataTool**: Real-time financial data retrieval
  - **get_price()**: Current stock/asset pricing
  - **get_time_series()**: Historical price data with configurable intervals
  - Rate-limited async operations with semaphore control

#### 3. User Interfaces

##### Gradio Web Interface (`src/gradio_ui.py`)
- **Simplified Single-Focus Interface**:
  - **Advisor Reference Generation**: Primary interface for client situation analysis
  - **Three-tab output structure**:
    1. **📋 Regulatory Overview**: CRA rules and regulations with sources
    2. **🌐 Web Search Results**: Current web information with exact URLs
    3. **💡 Final Recommendation**: Synthesized recommendations with reasoning and next steps
- **Features**:
  - Client situation processing with example templates
  - Real-time reference generation with progress indicators
  - Raw data viewing (JSON format and search results)
  - Google Search-powered current information retrieval

##### CLI Interface (`src/main.py`)
- Three operational modes:
  - `cli`: Interactive command-line session
  - `gradio`: Launch web interface
  - `search`: Knowledge base search demo

#### 4. Meeting Intelligence System (`src/react/agents/meeting_intelligence/`)
- **Three-stage process** (Workstream 2 design):
  1. **Semantic Analysis** (`semantic_analysis.py`):
     - Extract structured information from meeting transcripts/summaries
     - Identify Canadian financial entities (RRSP, TFSA, CPP, OAS, RESP)
     - Extract client situations and discussion topics
     - Currently in development phase
  2. **Reference Generation** (`reference_generation.py`):
     - **Stage 1 - Research**: 
       - Generate CRA search terms from client situations
       - Execute parallel knowledge base searches
       - Perform web searches for current information
     - **Stage 2 - Synthesis**:
       - Combine CRA and web results with Google Search grounding
       - Generate structured JSON reference material
       - Cross-validate information sources for accuracy and currency
- **Output format** (Updated JSON structure):
  - **regulatory_overview**: CRA rules with specific source references
  - **web_search_results**: Current information with exact URLs and relevance
  - **final_recommendation**: Synthesized answer, reasoning, and next steps

## Data Structure

### Client Profiles (`data/profile/client_profile.jsonl`)
- **Fields**: 40+ attributes including:
  - Demographics (age, citizenship, residency)
  - Financial metrics (balances, income, savings rate)
  - Risk profile (tolerance, capacity, experience)
  - Investment preferences
  - Goals and time horizons

### Meeting Data (`data/summary/` and `data/transcript/`)
- **Summaries**: Markdown files with:
  - Meeting recap points
  - Action items
  - Quick takeaways
- **Transcripts**: VTT format meeting recordings
- **Topics**: Canadian tax optimization, retirement planning, estate planning, investment strategies

## Technology Stack

### Core Dependencies
- **LLM Framework**: 
  - `openai>=1.95.1`: OpenAI SDK
  - `openai-agents>=0.2.4`: Agent framework
  - `google-genai>=0.1.0`: Google's native Gemini API for web search grounding
  - Model: `gemini-2.5-flash` (configurable)
- **Vector Database**: `weaviate-client>=4.15.4`
- **Financial Data**: `httpx>=0.24.0` for Twelve Data API integration
- **Web Framework**: `gradio>=5.35.0`
- **Async Support**: `nest-asyncio>=1.6.0`
- **Observability**: `langfuse>=3.1.3`

### Development Tools
- **Testing**: `pytest`, `pytest-asyncio`
- **Linting**: `ruff>=0.12.2`
- **Documentation**: `mkdocs`, `mkdocstrings`
- **Package Management**: `uv` (UV package manager)

## Configuration & Environment

### Required Environment Variables
```bash
# AI Model Configuration
OPENAI_API_KEY=<gemini-api-key>  # Used for both OpenAI-compatible and native Gemini API access
AGENT_LLM_MODEL=gemini-2.5-flash

# Weaviate Configuration
WEAVIATE_HTTP_HOST=<host>
WEAVIATE_HTTP_PORT=443
WEAVIATE_HTTP_SECURE=true
WEAVIATE_GRPC_HOST=<host>
WEAVIATE_GRPC_PORT=443
WEAVIATE_GRPC_SECURE=true
WEAVIATE_API_KEY=<api-key>

# Embedding Service
EMBEDDING_BASE_URL=<url>
EMBEDDING_API_KEY=<key>

# Financial Data API
TWELVE_DATA_API_TOKEN=<api-key>
TWELVEDATA_BASE_URL=https://api.twelvedata.com

# Langfuse Observability
LANGFUSE_PUBLIC_KEY=pk-lf-<key>
LANGFUSE_SECRET_KEY=sk-lf-<key>
LANGFUSE_HOST=https://us.cloud.langfuse.com

# Optional
GRADIO_SERVER_PORT=7860
```

### Configuration Management (`src/utils/env_vars.py`)
- Pydantic-based configuration model
- Automatic validation of environment variables
- Type-safe access to configs

## Testing Framework

### Test Coverage (`tests/tool_tests/test_integration.py` + various `test_*.py`)
- **Unit Tests**: 
  - Vectorizer functionality
  - Environment configuration
- **Integration Tests**:
  - Weaviate knowledge base search
  - ReAct agent creation and execution
  - Web search agent with Google Gemini API
  - Twelve Data financial API integration
  - Full system integration
  - Langfuse authentication
- **Domain-specific Tests**:
  - Wealth management queries
  - Financial concept searches
  - Real-time financial data retrieval
  - Web search result validation

## Project Management

### Build Agenda (`BUILD-AGENDA.md`)
- **4 Workstreams**:
  1. Multi-Agent Orchestration & Infrastructure
  2. Meeting Intelligence Sub-Agent
  3. Client Analysis & Risk Assessment Sub-Agent
  4. Investment Strategy & Portfolio Management Sub-Agent

### Agent Hierarchy (`.claude/prompts/`)
- **MASTER.md**: Master agent coordination guide
- **project.md**: Project-specific context
- Specialized prompts for:
  - Client profile generation/evaluation
  - Transcript summarization
  - Exploration and planning

## Key Features

### 1. ReAct Framework Implementation
- **Reasoning**: Agent explains reasoning before tool calls
- **Action**: Execute knowledge base or web searches
- **Observation**: Process search results
- **Response**: Synthesize comprehensive answers with citations

### 2. Multi-Source Information Retrieval
- **CRA Knowledge Base**: Regulatory document repository with hybrid search
- **Real-time Web Search**: Google's native Gemini API with search grounding
- **Financial Market Data**: Twelve Data API for current prices and time series
- **Cross-validation**: Compare multiple sources for accuracy and currency

### 3. Reference Generation
- Process client financial situations
- Generate search terms for regulatory and web searches
- Parallel execution across multiple information sources
- Structured JSON output with exact source citations

### 4. Observability & Tracing
- Langfuse integration for LLM observability
- OpenTelemetry support
- Trace ID generation for request tracking
- Performance monitoring

## Development Workflow

### Running the Application
```bash
# Install dependencies
uv sync

# Run CLI interface
python -m src.main cli

# Launch web interface
python -m src.main gradio

# Run search demo
python -m src.main search
```

### Testing
```bash
# Run all tests
pytest

# Run integration tests
pytest -m integration_test

# Run with coverage
pytest --cov=src
```

### Code Quality
```bash
# Format and lint code
ruff format .
ruff check . --fix

# Type checking (if configured)
mypy src/
```

## Future Enhancements (from BUILD-AGENDA.md)

1. **Enhanced Multi-Agent Coordination**
   - Master orchestrator for complex workflows
   - Sub-agent communication protocols
   - Task delegation optimization

2. **Advanced Meeting Intelligence**
   - Canadian financial NER improvements
   - Multi-session context preservation
   - Enhanced citation generation

3. **Portfolio Management Features**
   - Real-time market data integration (Bank of Canada, Statistics Canada)
   - Tax optimization strategies
   - Modern Portfolio Theory implementation

4. **Production Infrastructure**
   - Redis caching layer
   - API reliability patterns
   - Monitoring dashboards
   - Deployment automation

## Security Considerations

- No hardcoded credentials (all via environment variables)
- API key validation for Weaviate and embedding services
- Langfuse key format validation
- Secure HTTPS/gRPC connections

## Performance Optimization

- Async/await throughout for concurrent operations
- Rate limiting with semaphores
- Connection pooling for database clients
- Configurable timeouts and retries
- Parallel search execution in reference generation

## Documentation

- Comprehensive docstrings (NumPy style)
- Type hints throughout codebase
- README with usage examples
- CLAUDE.md for AI assistant guidance
- Inline comments for complex logic

## Recent Major Updates

### Google Search Integration (Latest)
- **Native Gemini API Integration**: Replaced mimic web search with Google's official Gemini API
- **Search Grounding**: Real-time web search with grounding metadata for exact source URLs
- **WebSearchAgent**: Dedicated agent class using `google-genai>=0.1.0` with search tools
- **URL Resolution**: Proper handling of redirect URLs with actual source information

### Financial Data Integration  
- **Twelve Data API**: Integrated real-time financial market data via `AsyncFinancialDataTool`
- **ReAct Agent Enhancement**: Added `get_price()` and `get_time_series()` as available tools
- **Rate Limiting**: Implemented semaphore-based concurrent request management
- **Test Coverage**: Created comprehensive integration tests for financial data retrieval

### UI/UX Improvements
- **Simplified Interface**: Consolidated to single Advisor Reference focus (removed chat tabs)
- **Three-Tab Output**: Structured display with Regulatory Overview, Web Results, and Final Recommendations
- **Enhanced Data Display**: Raw search results viewing with JSON and source formatting
- **Progress Indicators**: Real-time feedback during reference generation process

### Architecture Modernization
- **Agent Manager Compatibility**: Updated to support both ReAct and WebSearch agent types  
- **Cross-Validation Logic**: Compare RAG vs web search results for accuracy validation
- **Prompt System Reorganization**: Updated system prompts for new multi-source workflow
- **Error Handling**: Improved resilience across web search and financial API integrations

## License & Authors

- License: MIT
- Primary development by: Developer team
- AI assistance framework: Claude Code integration