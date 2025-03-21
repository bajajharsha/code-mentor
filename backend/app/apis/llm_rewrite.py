from fastapi import APIRouter, Depends, HTTPException, status

from app.controllers.llm_rewrite_controller import LlmRewriteController
from app.models.schema.llm_rewrite_schema import LlmRewrite
from app.utils.error_handler_decorator import handle_exceptions
from app.config.settings import get_settings
settings = get_settings()

router = APIRouter(tags=["llm_rewrite"])

@router.post("/llm-rewrite")
@handle_exceptions
async def llm_rewrite(
    request: LlmRewrite,
    llm_rewrite_controller = Depends(LlmRewriteController)
):
    
    return await llm_rewrite_controller.llm_rewrite(request)