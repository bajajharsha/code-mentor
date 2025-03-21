from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from app.models.schema.file_upload_schema import FileUploadRequest

from app.usecases.resync_usecase import ResyncUseCase

class ResyncController:
    def __init__(self, resync_usecase: ResyncUseCase = Depends(ResyncUseCase)):
        self.resync_usecase = resync_usecase

    async def resync_index(
        self, 
        file,
        file_request : FileUploadRequest
    ):
        return await self.resync_usecase.resync_index(file, file_request)