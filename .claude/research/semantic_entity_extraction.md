# Semantic Entity Extraction Strategy

## Overview
LLM-based extraction of Canadian financial concepts from meeting transcripts, structured as individual client agenda items for better downstream processing.

## Core Approach

### Individual Agenda Items Structure
Instead of aggregating all entities into one JSON, extract individual actionable items:

```json
{
  "client_agenda": [
    {
      "id": 1,
      "topic": "RRSP Optimization",
      "account_type": "RRSP",
      "opportunity": "Maximize remaining contribution room",
      "priority": "high",
      "regulatory_keywords": ["RRSP contribution limits", "earned income calculation"],
      "context": "Client mentioned being unsure about remaining RRSP room"
    },
    {
      "id": 2,
      "topic": "Tax-Efficient Investing",
      "account_type": "TFSA",
      "opportunity": "Move growth investments to TFSA",
      "priority": "medium", 
      "regulatory_keywords": ["TFSA contribution room", "tax-free growth"],
      "context": "Client has taxable investments generating capital gains"
    },
    {
      "id": 3,
      "topic": "First Home Purchase",
      "account_type": "FHSA",
      "opportunity": "Explore FHSA eligibility and benefits",
      "priority": "high",
      "regulatory_keywords": ["FHSA eligibility", "first-time homebuyer"],
      "context": "Client planning to buy house in 3 years"
    }
  ]
}
```

## Extraction Methodology

### Simple LLM Prompt
```python
AGENDA_EXTRACTION_PROMPT = """
Analyze this Canadian financial meeting content and extract individual client agenda items.

For each actionable topic discussed, create a separate agenda item with:
- topic: Brief description
- account_type: Relevant Canadian account (RRSP/TFSA/RESP/etc.)
- opportunity: Specific action or optimization
- priority: high/medium/low
- regulatory_keywords: 2-3 CRA search terms
- context: Supporting evidence from meeting

Meeting Content: {content}

Output as JSON array of individual agenda items.
"""
```

### Implementation
```python
class AgendaExtractor:
    async def extract_agenda_items(self, meeting_content: str) -> List[AgendaItem]:
        response = await self.llm_client.complete(
            prompt=AGENDA_EXTRACTION_PROMPT.format(content=meeting_content)
        )
        return self._parse_agenda_items(response)
```

## Benefits of Individual Items

1. **Downstream Processing**: Each LLM call handles one focused topic
2. **Parallel Processing**: Can search knowledge base for multiple items simultaneously  
3. **Prioritization**: Easy to sort and process by priority
4. **Modularity**: Each item is self-contained with its own context
5. **Scalability**: Can process items independently

## Integration Flow

```
Meeting Content → Individual Agenda Items → Parallel KB Searches → Individual Responses → Aggregated Report
```

This structure makes it much easier for subsequent LLM processing and provides cleaner separation of concerns.