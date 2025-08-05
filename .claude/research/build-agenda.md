# Financial Advisory Agent Bootcamp: 4 Independent Workstreams

## Executive Summary
Extend existing **ReAct framework using OpenAI SDK Agents** to build **Meeting Intelligence** and **Strategic Advisory** capabilities. Four focused workstreams: master orchestration system with infrastructure, meeting intelligence sub-agent, and two coordinated strategic advisory sub-agents handling client analysis and investment strategy respectively.

## Available Resources
- **Existing ReAct Agent Framework**: OpenAI SDK-based implementation to extend
- **CRA Publications**: Weaviate RAG system (pre-configured)
- **Government APIs**: Statistics Canada, Bank of Canada, Twelve Data (each workstream integrates as needed)
- **Evaluation Infrastructure**: Langfuse framework for LLM-as-judge integration
- **Data Sources**: `data/transcript/`, `data/summary/`, `data/client-profile/`

---

## Workstream 1: Multi-Agent Orchestration, Evaluation, Frontend & Infrastructure

**Objective**: Build the master coordination system that orchestrates all sub-agents, evaluates responses, provides user interface through Gradio frontend, and manages all infrastructure support

### Key Areas to Explore
- **Agent Orchestration**: Master agent that coordinates Meeting Intelligence, Client Analysis, and Investment Strategy sub-agents
- **LLM-as-Judge Integration**: Langfuse evaluation framework for real-time quality assessment and compliance monitoring
- **Gradio Frontend**: User interface for transcript upload, client profile input, and comprehensive advisory output display
- **Infrastructure Support**: Data processing pipeline, caching strategies, monitoring, and deployment infrastructure

### Technical Suggestions
- **OpenAI Multi-Agent Coordination**: Master ReAct agent that calls sub-agents via function calls in logical sequence
- **Langfuse Integration**: Automated evaluation pipeline for hallucination detection, regulatory compliance, recommendation quality
- **Gradio Interface**: File upload for transcripts, form inputs for client profiles, structured multi-agent output display
- **System Infrastructure**: Redis caching, API reliability patterns, monitoring dashboards, testing frameworks

### Research References
- OpenAI Function Calling patterns for complex agent coordination
- Langfuse LLM-as-judge templates and multi-agent evaluation workflows
- Gradio documentation for financial application interfaces with multi-step workflows
- Production infrastructure patterns for agent systems (caching, monitoring, reliability)

### Deliverable Ideas
- Master orchestration system coordinating all sub-agents in logical workflow
- Integrated evaluation framework with financial compliance metrics and quality scoring
- Complete Gradio web interface for end-to-end user experience
- Production-ready infrastructure with caching, monitoring, and deployment support

---

## Workstream 2: Meeting Intelligence Sub-Agent

**Objective**: Develop specialized sub-agent for processing Canadian financial meeting transcripts and generating relevant regulatory references and explanations

### Key Areas to Explore
- **Canadian Financial NER**: Entity extraction for RRSP, TFSA, CPP, OAS, RESP terminology from transcripts
- **CRA Knowledge Integration**: Optimize existing Weaviate RAG system for regulatory document retrieval
- **Context Preservation**: Multi-session conversation memory and client relationship tracking
- **Citation Generation**: Proper CRA publication referencing with regulatory compliance

### Technical Suggestions
- **Transcript Processing**: Audio/text → Canadian financial entities → knowledge base search → cited responses
- **RAG Optimization**: Experiment with embedding models, chunk sizes, retrieval strategies for CRA documents
- **NER Implementation**: Fine-tune models or leverage John Snow Labs Finance NLP for Canadian terminology
- **API Integration**: Build CRA Weaviate client functions as needed for knowledge retrieval

### Research References
- John Snow Labs Finance NLP for Canadian financial entity recognition
- Weaviate hybrid search implementations for regulatory documents
- Canadian financial terminology datasets and meeting transcript patterns
- RAG evaluation metrics for citation accuracy and regulatory compliance

### Deliverable Ideas
- Sub-agent specialized in Canadian financial transcript analysis with high entity extraction accuracy
- Optimized CRA knowledge retrieval system with relevant regulatory document citations
- Meeting context preservation system for multi-session client relationship tracking
- Regulatory compliance validation and proper citation generation

---

## Workstream 3: Client Analysis & Risk Assessment Sub-Agent

**Objective**: Develop specialized sub-agent for comprehensive client profile analysis, risk assessment, and investment suitability determination

### Key Areas to Explore
- **Client Profile Processing**: Risk tolerance analysis, investment experience evaluation, financial goals extraction
- **Risk Assessment Framework**: Age-based profiling, regulatory suitability requirements, compliance validation
- **Suitability Analysis**: Investment appropriateness, regulatory constraints, client-specific limitations
- **Profile Standardization**: Consistent client profile formats for downstream investment strategy processing

### Technical Suggestions
- **Profile Analysis Pipeline**: Client data → risk profiling → suitability assessment → standardized profile output
- **Risk Assessment Models**: Quantitative risk scoring, qualitative preference analysis, regulatory compliance checking
- **Suitability Framework**: Canadian investment regulations, provincial variations, client constraint validation
- **Data Validation**: Client profile completeness checking, missing information identification

### Research References
- Canadian investment regulation and suitability requirements by province
- Risk profiling methodologies and quantitative assessment frameworks
- Regulatory compliance requirements for investment advice in Canada
- Client profile standardization patterns in financial advisory systems

### Deliverable Ideas
- Sub-agent specialized in comprehensive client profile analysis and risk assessment
- Standardized risk scoring and suitability determination system
- Regulatory compliance validation for investment appropriateness
- Structured client profile output format for investment strategy integration

---

## Workstream 4: Investment Strategy & Portfolio Management Sub-Agent

**Objective**: Develop specialized sub-agent for generating Canadian-focused investment recommendations and portfolio allocation strategies based on client analysis

### Key Areas to Explore
- **Portfolio Construction**: Canadian-specific asset allocation, tax-efficient account placement (RRSP, TFSA, taxable)
- **Market Data Integration**: Real-time economic indicators from BoC, StatCan, and market data for context
- **Investment Logic**: Modern Portfolio Theory implementation, Canadian market focus, currency considerations
- **Tax Optimization**: Provincial tax implications, account type optimization, capital gains strategies

### Technical Suggestions
- **Recommendation Engine**: Client profile → market context → portfolio allocation → tax optimization → final strategy
- **Market Data APIs**: Integrate BoC, StatCan, Twelve Data as needed for economic and market context
- **Canadian Focus**: TSX market data, CAD currency considerations, Canadian sector concentrations
- **Investment Analytics**: Risk/return calculations, diversification analysis, performance projections

### Research References
- Modern Portfolio Theory and Canadian market implementation patterns
- Bank of Canada and Statistics Canada economic indicators for investment context
- Twelve Data API for Canadian market focus and TSX integration
- Tax-efficient investment strategies for Canadian account types

### Deliverable Ideas
- Sub-agent specialized in Canadian investment strategy and portfolio construction
- Market-informed recommendation engine with real-time economic context
- Tax-efficient portfolio allocation considering Canadian account types
- Performance analysis and risk-adjusted recommendation generation

---

## Integration & Coordination

### System Architecture Flow
1. **Workstream 1** (Master Orchestration) receives user input via Gradio interface
2. **Workstream 2** (Meeting Intelligence) processes transcripts and provides regulatory context
3. **Workstream 3** (Client Analysis) analyzes client profiles and determines suitability
4. **Workstream 4** (Investment Strategy) generates recommendations based on client analysis and market data
5. **Workstream 1** aggregates all outputs, evaluates quality, and presents comprehensive results

### Common Standards
- **OpenAI Function Calling**: Standard interface for agent-to-agent communication
- **JSON Schemas**: Consistent data formats, especially client profile structure between Workstreams 3 & 4
- **Error Handling**: Standardized error responses and fallback behaviors
- **Logging Format**: Unified logging for Langfuse evaluation and monitoring

### Success Validation
Each workstream demonstrates standalone functionality with mock data before integration. Final validation: Gradio interface → transcript + client profile input → orchestrated processing through all sub-agents → comprehensive advisory output with quality evaluation and regulatory compliance.