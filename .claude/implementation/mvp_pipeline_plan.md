# MVP Pipeline Implementation Plan

## Overview
Build a minimal viable pipeline following the dual-stage synthesis design to generate advisor reference material from client situations.

## Project Structure
```
src/
├── prompts/
│   ├── cra_search.py       # CRA search term generation prompt
│   ├── web_search.py       # Web search query generation prompt
│   └── reference_synthesis.py  # Stage 2 synthesis prompt
├── react/
│   └── agents/
│       └── reference_agent.py  # Main dual-stage agent
├── gradio_ui.py           # Modified for MVP
└── main.py                # Enhanced with MVP mode
```

## Sample Semantic Inputs (from Meeting 06)

### Input 1: RRSP Tax Optimization
```
"Michael, age 32, earns $87,000 annually in Ontario and wants to optimize his RRSP contributions for tax savings. He's already contributed $8,000 this year but has $18,600 total contribution room including carry-forward. He's paying 33% marginal tax rate and looking to maximize tax deductions."
```

### Input 2: Investment Strategy in RRSP
```
"Client has RRSP funds sitting in a savings account earning minimal returns. Looking for guidance on transitioning to a diversified ETF portfolio. Client is 32 years old with 30+ year investment horizon and moderate risk tolerance. Needs recommendations for low-cost Canadian ETF options."
```

### Input 3: TFSA vs RRSP Priority
```
"Client has both RRSP contribution room ($18,600) and unused TFSA room ($43,000). Earning $87,000 annually with 33% marginal tax rate. Wants to understand optimal contribution strategy between RRSP and TFSA for tax efficiency. Has capacity to save $500 monthly."
```

### Input 4: Common-Law Tax Planning
```
"Michael and his girlfriend have been living together for 2 years, qualifying as common-law. He earns $87,000 while she earns $45,000. Looking for tax optimization strategies including potential spousal RRSP contributions for income splitting in retirement."
```

## Implementation Steps

### 1. Create Prompts (`src/prompts/`)

#### cra_search.py
```python
CRA_SEARCH_PROMPT = """
Client situation: {client_situation}

Generate 2-4 word keywords for searching CRA regulatory documents.
Focus on specific tax topics, account types, or regulations mentioned.

Return only the keywords, no explanation.
Example: "RRSP contribution limits"
"""
```

#### web_search.py
```python
WEB_SEARCH_PROMPT = """
Client situation: {client_situation}

Generate a natural language web search query for current Canadian financial information.
Include year 2024/2025 and "Canada" for relevant results.

Return only the search query.
Example: "RRSP contribution limits 2024 Canada tax optimization"
"""
```

#### reference_synthesis.py
```python
REFERENCE_SYNTHESIS_PROMPT = """
CLIENT SITUATION:
{client_situation}

CRA REGULATORY DOCUMENTS:
{cra_results}

CURRENT WEB INFORMATION:
{web_results}

Generate advisor reference material in JSON format:

{{
  "regulatory_overview": [
    // Key CRA rules, deadlines, calculations from official documents
  ],
  "current_numbers": {{
    // Latest limits, rates, deadlines from web search
  }},
  "source_references": [
    // CRA chapters/sections and web sources used
  ],
  "advisor_notes": [
    // Important compliance considerations or planning opportunities
  ]
}}

Focus on factual information for advisor reference, not client advice.
"""
```

### 2. Create Reference Agent (`src/react/agents/reference_agent.py`)

```python
class AdvisorReferenceAgent:
    """Dual-stage agent for generating advisor reference material."""
    
    def __init__(self):
        self.cra_kb = AsyncWeaviateKnowledgeBase(...)
        self.llm_client = AsyncOpenAI(...)
    
    async def generate_reference(self, client_situation: str) -> dict:
        # Stage 1: Dual search
        research_data = await self._stage1_research(client_situation)
        
        # Stage 2: Reference synthesis
        reference = await self._stage2_synthesis(research_data)
        
        return reference
```

### 3. Enhance Gradio UI (`src/gradio_ui.py`)

Add new tab for Reference Generation:
```python
with gr.Tab("Advisor Reference"):
    situation_input = gr.Textbox(
        label="Client Situation", 
        placeholder="Describe the client's financial situation...",
        lines=3
    )
    
    generate_btn = gr.Button("Generate Reference Material")
    
    with gr.Row():
        with gr.Column():
            regulatory_output = gr.JSON(label="Regulatory Overview")
        with gr.Column():
            sources_output = gr.JSON(label="Sources & Notes")
```

### 4. Update Main Entry Point (`src/main.py`)

Add MVP mode:
```python
elif args.mode == "gradio":
    # Enhanced with reference agent
    from .gradio_ui import launch_gradio_app_with_reference
    launch_gradio_app_with_reference()
```

## MVP Features

### Core Functionality
1. Natural language client situation input
2. Automated CRA + web search
3. Structured reference material output
4. Source attribution

### Excluded (Not MVP)
- Confidence scoring
- Complex data structures
- Multiple agent types
- Advanced error handling