# Wealth Management Advisor Assistant Agent

## What This Does
An AI financial advisor that uses **ReAct reasoning** to answer wealth management questions by searching a knowledge database and providing cited, informed responses.

## The ReAct System Explained

### How ReAct Works
**ReAct** = **Reasoning** → **Action** → **Observation** → **Response**

When you ask: *"What are the tax implications of selling stocks this year?"*

1. **🧠 Reasoning**: *"The user needs current tax information about capital gains. I should search for recent tax policy on stock sales."*

2. **🔍 Action**: Calls `search_knowledgebase(keyword="capital gains tax 2024 stock sales")`

3. **👀 Observation**: Receives search results about current tax rates, holding periods, and regulations

4. **💬 Response**: Combines search results with reasoning to give a comprehensive, cited answer

### How Tools Get Their Intelligence

**The Magic of Docstrings**: Each tool's behavior comes from its function documentation:

```python
async def search_knowledgebase(self, keyword: str) -> SearchResults:
    """Search knowledge base.

    Parameters
    ----------
    keyword : str
        The search keyword to query the knowledge base.
    """
```

**What the Agent Sees**:
- **Tool Name**: `search_knowledgebase`
- **Description**: "Search knowledge base" 
- **Parameter**: `keyword` (string for "The search keyword to query the knowledge base")

**Without docstrings**, the agent would only see function names and types - losing all context about what tools do and when to use them.

### Agent Instructions

The system prompt tells the agent exactly when and how to use tools:

> *"Answer the question using the search tool. EACH TIME before invoking the function, you must explain your reasons for doing so. Be sure to mention the sources."*

This creates the **automatic search behavior** you see in conversations.

## Usage

**Web Interface (Gradio):**
```bash
python -m src.main gradio
```

**Command Line Interface:**
```bash
python -m src.main cli
```

**Knowledge Base Search Demo:**
```bash
python -m src.main search
```