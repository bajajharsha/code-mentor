from pydantic import BaseModel, EmailStr, Field


class LlmRewrite(BaseModel):
    orignal_file : str
    rewritten_code : str