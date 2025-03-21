from pydantic import BaseModel, EmailStr, Field


class FileUploadRequest(BaseModel):
    email: EmailStr
    filepath: str
    is_first_time: bool = Field(..., description="Flag indicating if this is the first time upload")