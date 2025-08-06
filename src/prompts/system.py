"""System prompts for the Wealth Management ReAct agent and advisor reference generation."""

# ============================================================================
# MAIN REACT AGENT
# ============================================================================

REACT_INSTRUCTIONS = """\
Answer the question using the search tool. \
EACH TIME before invoking the function, you must explain your reasons for doing so. \
Be sure to mention the sources in your response. \
If the search tool did not return intended results, try again. \
For best performance, divide complex queries into simpler sub-queries. \
Do not make up information. \
For facts that might change over time, you must use the search tool to retrieve the \
most up-to-date information.
"""

# ============================================================================
# REFERENCE AGENT - STAGE 1: SEARCH TERM GENERATION
# ============================================================================

# Generate CRA search keywords from client situation
CRA_SEARCH_TERM_GENERATION = """
Client situation: {client_situation}

Generate 1-3 search queries for CRA regulatory documents based on the topics mentioned.
Each query should be 2-4 words focusing on specific tax topics, account types, or regulations.
If only one topic is relevant, provide one query. If multiple topics, provide up to 3 queries.

Return each query on a new line, no explanations or numbering.
Example output for single topic:
RRSP contribution limits

Example output for multiple topics:
RRSP contribution limits
spousal RRSP rules
pension income splitting
"""

# Generate web search queries from client situation
WEB_SEARCH_QUERY_GENERATION = """
Client situation: {client_situation}

Generate 1-2 web search queries for current Canadian financial information based on the topics mentioned.
Each query should be natural language including "Canada" and relevant time period if mentioned.
If only one topic needs current info, provide one query. If multiple topics, provide up to 2 queries.

Return each query on a new line, no explanations or numbering.
Example output for single topic:
RRSP contribution limits Canada current rates

Example output for multiple topics:
RRSP spousal attribution rules Canada
pension income splitting Canada tax benefits
"""

# Execute web search using LLM
WEB_SEARCH_EXECUTION = """Search the web for current information about: {query}

Please find and summarize 3-5 relevant search results. For each result, include:
- The key information or finding
- The source website
Focus on Canadian financial regulations, tax rules, and current rates.

Format as:
1. [Key finding from source 1]
2. [Key finding from source 2]
3. [Key finding from source 3]
Sources: [list source domains]"""

# ============================================================================
# REFERENCE AGENT - STAGE 2: SYNTHESIS
# ============================================================================

REFERENCE_SYNTHESIS = """
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