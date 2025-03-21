from fastapi import UploadFile
import aiofiles
import os
from app.config.settings import get_settings

settings = get_settings()

async def store_file_locally(self, file: UploadFile):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, settings.RAW_DATA_FILE_NAME)
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(2 * 1024 * 1024):  # Read in 2MB chunks
                await f.write(chunk)
        return file_path