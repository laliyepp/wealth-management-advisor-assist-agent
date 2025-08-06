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
Analyze the meeting content to extract the client's first name.
Once you have identified the first name, use it as input to the client profile tool 
to retrieve the client's profile information from the database.
Return a natural language description of the client based on the retrieved profile data.
If no first name can be identified or no profile is found, indicate this clearly in your response.
"""