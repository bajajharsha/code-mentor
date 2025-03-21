INTENT_SYSTEM_PROMPT = "You are an AI assistant tasked with analyzing user queries to determine their intent and characteristics."

INTENT_USER_PROMPT_TEMPLATE = """
Analyze the following user query and identify its primary intent and characteristics:

Query: "{query}"

Categorize the query into one of these categories:
1. Code understanding (requesting explanation of code functionality)
2. Code modification (asking for changes to existing code)
3. Codebase navigation (trying to find specific files or components)
4. New feature implementation (requesting to add something new)
5. Debugging (asking for help with errors)
6. General programming questions (not specific to the codebase)
7. Non-programming questions
8. Implement whole route
9. Implement whole app

Also identify:
- Does the query mention specific files, classes, or functions? if yes then list them in a list
- Does the query refer to specific code patterns or architectural concepts?
- How technically specific is the query (on a scale of 1-5)?

Provide your analysis in JSON format.
"""