from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from app.models.schema.llm_rewrite_schema import LlmRewrite

from app.usecases.llm_rewrite_usecase import LlmRewriteUseCase

class LlmRewriteController:
    def __init__(self, llm_rewrite_usecase: LlmRewriteUseCase = Depends(LlmRewriteUseCase)):
        self.llm_rewrite_usecase = llm_rewrite_usecase
    
    async def llm_rewrite(self, request: LlmRewrite):

        response = await self.llm_rewrite_usecase.process_llm_rewrite(request)

        return JSONResponse(
            content={
                "data": response,
                "statuscode": 200,
                "detail": "Query processed successfully",
                "error": ""
            },
            status_code=status.HTTP_200_OK
        )