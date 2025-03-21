from pydantic import BaseModel, EmailStr, Field


class QueryRequest(BaseModel):
    user_query : str
    current_file_content : str
    current_file_path: str
    email: EmailStr
    workspace_name: str