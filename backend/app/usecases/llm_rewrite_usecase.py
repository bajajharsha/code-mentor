from app.config.settings import get_settings
from app.services.llm_service import LLMService
from app.models.schema.llm_rewrite_schema import LlmRewrite
from fastapi import Depends

from app.prompts.llm_rewrite.rewrite_prompts import REWRITE_QUERY_TEMPLATE, REWRITE_USER_PROMPT_TEMPLATE

settings = get_settings()

class LlmRewriteUseCase:
    def __init__(self, llm_service: LLMService = Depends(LLMService)):
        self.llm_service = llm_service
        self.model_name = "claude-3-7-sonnet-20250219"

    
    async def process_llm_rewrite(self, request: LlmRewrite):
        orignal_code = request.orignal_file
        rewritten_code = request.rewritten_code

        user_prompt = REWRITE_USER_PROMPT_TEMPLATE.format(
            orignal_code = orignal_code,
            rewritten_code = rewritten_code
        )

        response = await self.llm_service.anthropic_api_call(
            model_name = self.model_name,
            system_prompt = user_prompt,
            user_prompt = user_prompt,
            user_query = REWRITE_QUERY_TEMPLATE

        )
        text = response.get("content", [])[0].get("text","")
        return text