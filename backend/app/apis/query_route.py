from fastapi import APIRouter, Depends, UploadFile, File, status, Form
from fastapi.responses import JSONResponse

from app.utils.security_util import get_current_user
from app.models.schema.query_schema import QueryRequest
from app.controllers.query_controller import QueryController
from app.utils.error_handler_decorator import handle_exceptions
from typing import Optional

from pydantic import EmailStr

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query")
@handle_exceptions
async def query(
    request: QueryRequest,
    current_user = Depends(get_current_user),
    query_controller = Depends(QueryController)
):
    return await query_controller.query(request)

@router.post("/stream-query")
@handle_exceptions
async def stream_query(
    request: QueryRequest,
    current_user = Depends(get_current_user),
    query_controller = Depends(QueryController)
):
    return await query_controller.stream_query(request)