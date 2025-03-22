from app.services.pinecone_service import PineconeService
from app.services.llm_service import LLMService
from fastapi import Depends
import json

from app.prompts.query_analysis.preprocess_prompts import PREPROCESS_SYSTEM_PROMPT, PREPROCESS_USER_PROMPT_TEMPLATE
from app.prompts.query_analysis.intent_analysis_prompts import INTENT_SYSTEM_PROMPT, INTENT_USER_PROMPT_TEMPLATE
from app.prompts.query_analysis.reformulate_prompts import REFORMULATE_SYSTEM_PROMPT, REFORMULATE_USER_PROMPT_TEMPLATE
from app.prompts.query_analysis.rag_decision_prompts import RAG_DECISION_SYSTEM_PROMPT, RAG_DECISION_USER_PROMPT_TEMPLATE


ps = PineconeService()

from typing import Dict, Any, Tuple


class QueryAnalysisPipeline:
    def __init__(self, llm_service : LLMService = Depends(LLMService)):
        self.llm_service = llm_service
        


    async def preprocess_user_input(self, raw_input: str) -> Dict[str, Any]:
        
        user_prompt = PREPROCESS_USER_PROMPT_TEMPLATE.format(raw_input = raw_input)
        
        response = await self.llm_service.openai_api_call(
            model_name="gpt-4-turbo",
            system_prompt=PREPROCESS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_format={"type": "json_object"}
        )
        
        try:
            content = response["choices"][0]["message"]["content"]
            parsed_content = json.loads(content)
            return parsed_content
        except (json.JSONDecodeError, KeyError) as e:
            return {
                "user_query": "How do I fix the issue in my code?",
                "context": raw_input,
                "error": ""
            }
        
    async def analyze_intent(self, query: str) -> Dict[str, Any]:
        
        user_prompt = INTENT_USER_PROMPT_TEMPLATE.format(query = query)
        
        response = await self.llm_service.openai_api_call(
            model_name="gpt-4-turbo",
            system_prompt = INTENT_SYSTEM_PROMPT,
            user_prompt = user_prompt,
            response_format={"type": "json_object"}
        )
        
        return response["choices"][0]["message"]["content"]
    
    async def reformulate_query(self, query: str, intent_analysis: Dict[str, Any]) -> str:
        
        prompt = REFORMULATE_USER_PROMPT_TEMPLATE.format(
            query = query,
            intent_analysis = intent_analysis
        )
        
        response = await self.llm_service.openai_api_call(
            model_name = "gpt-4-turbo",
            system_prompt = REFORMULATE_SYSTEM_PROMPT,
            user_prompt = prompt,
            response_format={"type": "json_object"}
        )
        return response["choices"][0]["message"]["content"]
    
    async def make_rag_decision(
        self, 
        original_query: str, 
        reformulated_query: str, 
        intent_analysis: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Decide if RAG is necessary and provide reasoning."""

        prompt = RAG_DECISION_USER_PROMPT_TEMPLATE.format(
            original_query = original_query,
            reformulated_query = reformulated_query,
            intent_analysis = intent_analysis
        )
        
        response = await self.llm_service.openai_api_call(
            model_name = "gpt-4-turbo",
            system_prompt = RAG_DECISION_SYSTEM_PROMPT,
            user_prompt = prompt
        )
        
        decision_text = response["choices"][0]["message"]["content"]
        use_rag = "True" in decision_text.split(" ")[0]
        
        return use_rag, decision_text
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process the full pipeline and return results."""

        preprocess_query = await self.preprocess_user_input(query)
        # Stage 1: Intent Analysis
        intent_analysis = await self.analyze_intent(query)
        
        # Stage 2: Query Reformulation
        reformulated_query = await self.reformulate_query(preprocess_query, intent_analysis)
        
        # Stage 3: RAG Decision
        use_rag, reasoning = await self.make_rag_decision(query, reformulated_query, intent_analysis)
        
        return {
            "original_query": query,
            "preprocess_query": preprocess_query,
            "intent_analysis": json.loads(intent_analysis),
            "reformulated_query": json.loads(reformulated_query),
            "use_rag": use_rag,
            "reasoning": reasoning
        }