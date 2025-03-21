from fastapi import APIRouter, Depends, UploadFile, File, status, Form
from fastapi.responses import JSONResponse
from app.utils.security_util import get_current_user
from app.models.schema.file_upload_schema import FileUploadRequest
from app.controllers.resync_controller import ResyncController
from app.utils.error_handler_decorator import handle_exceptions
from typing import Optional

from pydantic import EmailStr

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/resync-index")
@handle_exceptions
async def resync(
    file: UploadFile = File(...),
    email: EmailStr = Form(...),
    filepath: str = Form(...),
    is_first_time: bool = Form(...),
    resync_controller: ResyncController = Depends(),
    current_user = Depends(get_current_user)
):
    file_request = FileUploadRequest(
        email=email,
        filepath=filepath,
        is_first_time=is_first_time
    )
    response_data = await resync_controller.resync_index(file, file_request)
    return JSONResponse(
            content={
                "data": response_data,
                "statuscode": 200,
                "detail": "Resynced successfully",
                "error": "",
            },
            status_code=status.HTTP_200_OK,
        )