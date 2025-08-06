# Dual-Stage Reference Synthesis Agent - MVP

## Purpose
Generate reference information for financial advisors by combining CRA regulatory knowledge with current market context.

## Architecture
```
Client Situation → Stage 1: Research Gathering → Stage 2: Reference Synthesis → Advisor Reference Material
```

## Stage 1: Research Gathering

### Separate Search Term Generation
```python
async def generate_cra_search_terms(client_situation: str) -> str:
    """Generate CRA regulatory search keywords."""
    prompt = f"""
    Client situation: {client_situation}
    
    Generate CRA regulatory search keywords (2-4 words) for official tax documents.
    Return only the keywords.
    
    Example: "RRSP contribution limits"
    """
    return await llm.complete(prompt)

async def generate_web_search_query(client_situation: str) -> str:
    """Generate web search query for current information.""" 
    prompt = f"""
    Client situation: {client_situation}
    
    Generate web search query for current Canadian financial information.
    Return natural language search query.
    
    Example: "RRSP contribution limits 2024 Canada deadline"
    """
    return await llm.complete(prompt)

async def stage1_research_gathering(client_situation: str) -> dict:
    # Generate search terms separately (different formats needed)
    cra_keywords = await generate_cra_search_terms(client_situation)
    web_query = await generate_web_search_query(client_situation)
    
    # Execute searches with different return formats
    cra_results = await cra_kb.search_knowledgebase(cra_keywords)  # Returns List[SearchResult]
    web_results = await web_search_tool(web_query)                # Returns raw text string
    
    return {
        "client_situation": client_situation,
        "cra_results": cra_results,      # Structured SearchResult objects
        "web_results": web_results,      # Unstructured text string  
        "cra_keywords": cra_keywords,
        "web_query": web_query
    }
```

## Stage 2: Reference Synthesis

### Professional Reference Generation
```python
async def stage2_reference_synthesis(research_data: dict) -> dict:
    synthesis_prompt = f"""
    CLIENT SITUATION:
    {research_data["client_situation"]}
    
    CRA REGULATORY RESEARCH:
    {format_cra_research(research_data["cra_research"])}
    
    CURRENT MARKET RESEARCH:
    {format_web_research(research_data["web_research"])}
    
    SYNTHESIZE INTO ADVISOR REFERENCE MATERIAL:
    
    1. REGULATORY_OVERVIEW: Key CRA rules, deadlines, calculations
    2. CURRENT_NUMBERS: Latest limits, rates, deadlines for 2024/2025
    3. SOURCE_REFERENCES: Specific CRA chapters/sections and reliable sources
    4. ADVISOR_NOTES: Important compliance considerations or recent changes
    
    Format as professional reference information for advisor use.
    JSON: {{"regulatory_overview": [...], "current_numbers": {...}, "source_references": [...], "advisor_notes": [...]}}
    """
    
    return await llm.complete(synthesis_prompt)
```

## Complete Implementation

```python
class AdvisorReferenceAgent:
    def __init__(self):
        self.cra_kb = AsyncWeaviateKnowledgeBase(...)
        self.llm_client = AsyncOpenAI(...)
    
    async def generate_reference(self, client_situation: str) -> dict:
        """Generate advisor reference material from client situation."""
        
        # Stage 1: Gather research from multiple sources
        research_data = await self.stage1_research_gathering(client_situation)
        
        # Stage 2: Synthesize into advisor reference format
        reference_material = await self.stage2_reference_synthesis(research_data)
        
        return reference_material
    
    async def stage1_research_gathering(self, client_situation: str) -> dict:
        # Generate search terms separately (different LLM prompts for different formats)
        cra_keywords = await self.generate_cra_search_terms(client_situation)
        web_query = await self.generate_web_search_query(client_situation)
        
        # Execute searches with different return formats
        cra_results = await self.cra_kb.search_knowledgebase(cra_keywords)  # Returns List[SearchResult]
        web_results = await self.web_search_with_tools(web_query)           # Returns raw text string
        
        return {
            "client_situation": client_situation,
            "cra_results": cra_results,      # Structured data
            "web_results": web_results,      # Unstructured text
            "cra_keywords": cra_keywords,
            "web_query": web_query
        }
    
    async def stage2_reference_synthesis(self, research_data: dict) -> dict:
        # Build reference synthesis prompt
        prompt = self.build_reference_prompt(research_data)
        
        # Generate advisor reference material
        response = await self.llm_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self.parse_reference_response(response.choices[0].message.content)
```

## Example Flow

### Input
```
"Client wants to optimize RRSP contributions for 2024. They mentioned being unsure about contribution room and deadline."
```

### Stage 1: Research Data
```python
{
    "client_situation": "Client wants to optimize RRSP contributions for 2024...",
    "cra_results": [
        {
            "source": {"title": "", "section": None},
            "highlight": {"text": ["## Chapter 1\n\nRPP contributions\n\nMarch 3, 2025, is the deadline..."]}
        }
    ],
    "web_results": "2024 RRSP contribution limit is $31,560 or 18% of earned income from 2023, whichever is less. Deadline March 3, 2025. Source: cra-arc.gc.ca",
    "cra_keywords": "RRSP contribution limits deadlines",
    "web_query": "RRSP contribution room limits 2024 Canada"
}
```

### Stage 2: Advisor Reference Material
```python
{
    "regulatory_overview": [
        "CRA Chapter 1 specifies RRSP contribution deadline of March 3, 2025 for 2024 tax year",
        "Contribution room calculated as lesser of annual maximum or 18% of previous year earned income",
        "Unused contribution room carries forward indefinitely with no expiry"
    ],
    "current_numbers": {
        "2024_maximum": "$31,560",
        "percentage_calculation": "18% of 2023 earned income", 
        "contribution_deadline": "March 3, 2025",
        "tax_year": "2024"
    },
    "source_references": [
        "CRA Chapter 1: RPP contributions - deadline requirements",
        "cra-arc.gc.ca - current annual maximums",
        "CRA Notice of Assessment - unused room calculation"
    ],
    "advisor_notes": [
        "Client can check unused room via CRA My Account portal",
        "Over-contribution penalties apply for amounts exceeding room",
        "Spousal RRSP contributions count toward contributor's limit"
    ]
}
```

## Key Benefits

1. **Professional Focus**: Information FOR advisors, not direct client advice
2. **Regulatory Authority**: CRA sources combined with current context
3. **Reference Format**: Structured for advisor decision-making
4. **Source Attribution**: Clear references for compliance
5. **Practical Notes**: Important considerations for advisor use

This design provides advisors with authoritative reference material to inform their client recommendations.