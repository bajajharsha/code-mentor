RAG_DECISION_SYSTEM_PROMPT = """
You are an AI assistant tasked with determining the necessity of retrieval-augmented generation (RAG) 
for effectively answering user queries related to a codebase.
"""

RAG_DECISION_USER_PROMPT_TEMPLATE = """
Determine if the following user query requires retrieval-augmented generation (RAG) 
on the codebase to be answered effectively.

Consider the following when making your decision:

RAG is likely necessary if:
- The query refers to specific parts of the codebase
- The query is asking about implementation details from codebase
- The query requires understanding existing code structure
- The query is about making changes to existing code
- The query is about debugging existing code
- the query includes words like in my codebase or in my code or in my project

RAG is likely unnecessary if:
- The query is about general programming concepts
- The query is asking for implementation of a standard pattern with no reference to existing code
- The query is non-technical
- the query is about general programming concepts for example : "how can i convert uppercase to lowercase"

Example queries that might require RAG:
in all the tracing services i want to add new provider config in all one of them please do it for me and keep the provider dummy and whatever you want

When in doubt, lean toward using RAG.

Your task is to analyze the following inputs and decide if RAG is required:
Original query: "{original_query}"
Reformulated query: "{reformulated_query}"
Intent analysis: {intent_analysis}

Return your decision as "True" or "False" on whether to do rag or not followed by a brief explanation
and also tell what topk and topn would be suited provided that one chunk is around 500 tokens,
so if query demands huge changes or implementation then topk and topn should be large for that.
"""