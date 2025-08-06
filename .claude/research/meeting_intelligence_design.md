# Meeting Intelligence Extension - Workstream 2 Implementation Plan

## Overview
Build a specialized **Meeting Intelligence Sub-Agent** that extends the existing ReAct system to process Canadian financial meeting transcripts/summaries and provide regulatory references with real-time macro context.

## Core Components (One-Day Implementation)

### 1. Meeting Intelligence Agent (`src/react/agents/meeting_intelligence.py`)
- **Semantic Entity Understanding**: Use LLM-based analysis instead of deterministic NER to identify Canadian financial concepts, regulatory topics, and client needs from meeting content
- **Context-Aware Topic Extraction**: Identify key discussion themes (retirement planning, tax optimization, investment strategies, etc.)
- **Knowledge Integration**: Leverage existing CRA Weaviate knowledge base for regulatory citations
- **Structured Output Generation**: Format insights with proper citations and metadata

### 2. Enhanced Knowledge Base Tool (`src/utils/tools/enhanced_kb_search.py`)
- **JSON Processing**: Process the existing `SearchResults` structure from Weaviate
- **Enhanced Properties**: Extract all available properties from `obj.properties` including:
  - `title` (document name)
  - `section` (document section if available) 
  - `text` (content snippet)
  - Additional metadata fields (to be discovered from schema)
- **LLM-Based Synthesis**: Use LLM to process top X search results and generate human-readable summaries with proper source attribution
- **Citation Format**: Include `source_file`, `page_start`, `page_end` in JSON output when available

### 3. API Integration Tools (`src/utils/tools/`)
- **BOC API Client** (`boc_api.py`): Bank of Canada rates, monetary policy context
- **StatCan API Client** (`statcan_api.py`): Economic indicators, employment data
- **Twelve Data Client** (`market_data.py`): TSX/Canadian market context

### 4. Research Documentation (`.claude/research/`)
- **Meeting Intelligence Design** (`meeting_intelligence_design.md`): Detailed architecture and implementation approach
- **API Integration Specs** (`api_integration_specs.md`): BOC, StatCan, Twelve Data integration patterns
- **Entity Extraction Strategy** (`semantic_entity_extraction.md`): LLM-based approach for Canadian financial concepts

## Implementation Architecture

```
Meeting Input (transcript/summary)
    ↓
Semantic Analysis (LLM identifies financial topics/entities)
    ↓
Enhanced Knowledge Search (existing CRA Weaviate with improved processing)
    ↓
LLM Synthesis (process JSON results → human-readable with citations)
    ↓
API Context Enrichment (BOC/StatCan/Twelve Data)
    ↓
Structured Meeting Intelligence Output
```

## Key Technical Approach

### Semantic Entity Extraction
- Use LLM prompts to identify Canadian financial concepts contextually
- Focus on semantic understanding rather than pattern matching
- Extract concepts like "retirement planning", "tax optimization", "RRSP contributions" based on discussion context

### Enhanced JSON Processing
- Process existing `SearchResults` from Weaviate KB
- LLM synthesizes top search results into structured summaries
- Include proper source attribution with available metadata
- Format: `{"source_file": "title", "content_summary": "...", "relevance": "..."}`

### Seamless Integration
- Extends existing `create_react_agent()` function with new tools
- Maintains compatibility with current ReAct framework
- Adds specialized prompts for meeting intelligence

## Technical Implementation Details

### Current System Analysis
Based on analysis of the existing codebase:

1. **Existing ReAct Framework**: Uses OpenAI SDK Agents with function calling
2. **Weaviate Knowledge Base**: CRA publications in collection "rbc_2_cra_public_documents"
3. **Current Search Results Structure**:
   ```python
   SearchResults = list[_SearchResult]
   _SearchResult {
       source: {
           title: str,
           section: str | None
       },
       highlight: {
           text: list[str]
       }
   }
   ```

### Meeting Intelligence Agent Implementation

#### Agent Structure
```python
class MeetingIntelligenceAgent:
    """Specialized agent for Canadian financial meeting analysis."""
    
    async def analyze_meeting(self, content: str) -> MeetingAnalysis:
        """Process meeting transcript/summary with semantic understanding."""
        
    async def extract_entities(self, content: str) -> List[FinancialEntity]:
        """Extract Canadian financial concepts using LLM analysis."""
        
    async def search_regulations(self, entities: List[FinancialEntity]) -> List[RegulatoryReference]:
        """Search CRA knowledge base for relevant regulations."""
        
    async def enrich_with_market_data(self, analysis: MeetingAnalysis) -> EnrichedAnalysis:
        """Add current market context from APIs."""
```

#### Key Features
1. **Semantic Understanding**: Use LLM to understand context rather than pattern matching
2. **Regulatory Citation**: Automatic linking to relevant CRA publications
3. **Market Context**: Real-time economic indicators for informed advice
4. **Structured Output**: JSON format with proper source attribution

### Enhanced Knowledge Base Search

#### Current Implementation Analysis
The existing `AsyncWeaviateKnowledgeBase.search_knowledgebase()` returns:
- Limited to `title`, `section`, and truncated `text`
- No page or document metadata
- Raw search results without synthesis

#### Enhancement Strategy
1. **Expanded Property Extraction**: Discover and extract all available properties from Weaviate objects
2. **LLM-Powered Synthesis**: Process multiple search results into coherent summaries
3. **Enhanced Citation Format**: Include document references with page numbers when available
4. **Relevance Scoring**: LLM-based relevance assessment for search results

### API Integration Architecture

#### Government Data Sources
1. **Bank of Canada API**: 
   - Key interest rates
   - Monetary policy updates
   - Economic forecasts

2. **Statistics Canada API**:
   - Employment statistics
   - Inflation data
   - Economic indicators

3. **Twelve Data API**:
   - TSX market data
   - Canadian equity performance
   - Sector analysis

#### Integration Pattern
```python
async def get_market_context(self, topics: List[str]) -> MarketContext:
    """Fetch relevant market data based on meeting topics."""
    context = {}
    
    if "interest_rates" in topics:
        context["boc_rates"] = await self.boc_client.get_current_rates()
    
    if "employment" in topics:
        context["employment"] = await self.statcan_client.get_employment_stats()
    
    if "investments" in topics:
        context["market_data"] = await self.twelve_data_client.get_tsx_overview()
    
    return MarketContext(**context)
```

## Expected Output Format

### Meeting Intelligence Analysis
```json
{
  "meeting_summary": {
    "key_topics": ["retirement_planning", "rrsp_optimization", "tax_strategy"],
    "client_needs": ["increase_rrsp_contributions", "tax_loss_harvesting"],
    "regulatory_considerations": ["rrsp_contribution_limits", "cra_withholding_tax"]
  },
  "regulatory_references": [
    {
      "topic": "rrsp_contribution_limits",
      "source_file": "Income Tax Guide for RRSP Contributors",
      "section": "Contribution Limits",
      "content_summary": "Annual RRSP contribution limits are based on 18% of previous year's earned income...",
      "relevance_score": 0.95,
      "page_reference": "pages 12-15"
    }
  ],
  "market_context": {
    "boc_overnight_rate": "4.25%",
    "current_inflation": "3.2%",
    "tsx_performance": "+2.1% YTD",
    "last_updated": "2025-01-08T10:30:00Z"
  },
  "action_items": [
    "Review client's current RRSP contribution room",
    "Consider tax-loss harvesting opportunities before year-end",
    "Explore high-yield savings options for emergency fund"
  ]
}
```

## Implementation Timeline (One Day)

### Phase 1: Core Agent (3 hours)
- Create `MeetingIntelligenceAgent` class
- Implement semantic entity extraction using LLM prompts
- Basic integration with existing ReAct framework

### Phase 2: Enhanced Knowledge Search (2 hours)
- Enhance existing Weaviate search tool
- Implement LLM-based result synthesis
- Add proper citation formatting

### Phase 3: API Integration (2 hours)
- Implement BOC, StatCan, Twelve Data clients
- Create market context enrichment functionality
- Add error handling and rate limiting

### Phase 4: Integration & Testing (1 hour)
- Integrate all components into existing agent system
- Test with sample meeting transcripts
- Validate output format and citations

## Success Criteria

1. **Semantic Understanding**: Agent correctly identifies Canadian financial concepts from meeting content
2. **Regulatory Citations**: Proper attribution to CRA documents with source references
3. **Market Context**: Real-time economic data integrated appropriately
4. **Structured Output**: JSON format with human-readable summaries and proper citations
5. **Seamless Integration**: Works within existing ReAct framework without disruption

## Next Steps

1. Implement core Meeting Intelligence Agent
2. Enhance knowledge base search with LLM synthesis
3. Add API integration tools
4. Test with real meeting transcripts
5. Refine output format based on user feedback

This design provides a foundation for building intelligent meeting analysis capabilities that leverage semantic understanding and real-time market context while maintaining compatibility with the existing system architecture.