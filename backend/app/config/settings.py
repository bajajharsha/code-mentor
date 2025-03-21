import os
from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Auth App"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Database settings
    MONGODB_URL: str
    DB_NAME: str
    
    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    PINECONE_API_KEY: str
    GROQ_API_KEY: str
    LLAMA_CLOUD_API_KEY: str
    COHERE_API_KEY: str
    ZILLIS_API_KEY: str
    JINA_API_KEY: str
    UNSTRUCTURED_API_KEY: str
    GEMINI_API_KEY: str
    OPENAI_API_KEY: str
    TOGETHERAI_API_KEY: str
    VOYAGEAI_API_KEY: str

    PINECONE_CREATE_INDEX_URL: str
    PINECONE_API_VERSION: str
    PINECONE_EMBED_URL: str
    PINECONE_UPSERT_URL: str
    PINECONE_RERANK_URL: str
    PINECONE_QUERY_URL: str
    PINECONE_LIST_INDEXES_URL: str
    COHERE_BASE_URL: str
    JINA_BASE_URL: str
    TOGETHERAI_BASE_URL: str
    VOYAGEAI_BASE_URL: str
    ANTHROPIC_API_KEY: str

    MULTI_CHUNK_QUERIES_COUNT: int = 20
    MIN_CHUNKS_FOR_MULTI_QUERY: int = 3
    MAX_CHUNKS_FOR_MULTI_QUERY: int = 6
    LLM_REQUEST_DELAY: float = 0.7
    UPLOAD_DIR: str = "uploads/"
    RAW_DATA_FILE_NAME: str = "raw_dataset.json"
    GT_DATA_FILE_NAME: str = "rag_dataset.json"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "RAG_Playground"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com/v1"

    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()