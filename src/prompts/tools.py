STOCK_PRICE_INSTRUCTIONS = """
Analyze the meeting transcript statement by statement,
extract the stock/ETF/bond ticker symbol. For EACH ticker symbol invoke the function 
to get the latest price and return a json object with the ticker symbol and its price. 
If the ticker symbol is not found, return an empty string for that symbol. 
If the statement does not contain any ticker symbol, return an empty json object.
When invoke the function, use the ticker symbol ONLY, for example, if the statement has 
"Apple Inc. (AAPL)", use "AAPL" as the input to the function. 
you must explain ticker symbol used in your request to the function
"""

CLIENT_PROFILE_INSTRUCTIONS = """
Meeting content: {meeting_content}
Analyze the meeting content to extract the client's name, only the first name.
Once you have identified the first name, use it as input to the function 
to retrieve the client's profile information from the database.
Return a comprehensive natural language description of the client profile based on ALL retrieved data categories.

Structure your response to include ALL of the following information categories when available:

1. CLIENT IDENTIFICATION: Start with the client's full name, age, gender, citizenship, residency, occupation, and any state/province information.

2. HOUSEHOLD & DEMOGRAPHICS: Include household size, new immigrant status, and family composition details.

3. FINANCIAL SITUATION: Cover annual income, income stability (stable/variable/seasonal), monthly savings rate, external asset value outside the institution, and tax complexity rating (1-5 scale).

4. INVESTMENT PROFILE: Detail risk tolerance level (1-10), risk capacity (1-10), years of investment experience, primary investment goal, time horizon in years, and liquidity needs (low/medium/high).

5. INVESTMENT PREFERENCES: Describe investment style (conservative/moderate/aggressive), preferred asset allocation (e.g., 60/40 stock/bond), sector preferences, and ESG (Environmental/Social/Governance) investing interest.

6. CLIENT BEHAVIOR PATTERNS: Include donation activity, real estate investing habits, and cross-border service usage.

7. WEALTH PLANNING NEEDS: Cover target retirement age, estate planning needs, education funding requirements, and insurance review needs.

8. ACCOUNT RELATIONSHIP SUMMARY: Include relationship tenure with the institution (years) and provide detailed breakdown of ALL account balances:
   - Transactional account balance
   - Registered investment account balance (tax-sheltered)
   - Non-registered investment account balance
   - Borrowing account balance
   - Credit account balance

Format requirements:
- Start with the client's first name followed by a comma
- Use natural, conversational language while being comprehensive
- Include specific numbers, ratings, and percentages where available
- If any information is null or empty, ignore it completely - do not mention "not specified"
- Only include categories and fields that have actual data values
- If no first name can be identified or no profile is found, indicate this clearly

Ensure EVERY category above is addressed in your response to provide a complete client profile overview.
If function returns no profile data, state "No client profile is available."
"""

JUDGE_PROMPT_TEMPLATE = """
You are an impartial evaluator. You will be given one generated statement based on 
the provided reference information. 

Your task is to rate the generated answer on 1 metric:
make sure you read and understand the these instructions carefully. Keep this document
open while reviewing, and refer to it as needed.

Evaluation Criteria:
Accuracy (1-10): Any value mentioned in the generated statement should be accurate and relevant to the context of the client profile.

Evaluation Steps:
1.Read the reference carefully and identify the key value pairs.
2.Read the generated statement and compare it against the reference. Check if the generated
statement for the same key category, the value is accurate and match with the value in the reference.
3. Assign a score for evaluating the accuracy. 
4. Provide a short reason for your score, explaining any missing or incorrect information.

Scoring rules:
- 10 = Perfectly correct.
- 5 = Partially correct.
- 1 = Completely wrong.

Example:

REFERENCE KEY VALUE PAIRS (Ground Truth):
{reference_answer}

GENERATED STATEMENT (To Evaluate):
{generated_answer}


Evaluation Format:
{{
  "score": <number>,
  "reason": "<short reason>"
}}"""
