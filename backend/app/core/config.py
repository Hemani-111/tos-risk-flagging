import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "project name"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000
    
    UPLOAD_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_ALLOWED_EXTENSIONS_STR: str = ".pdf,.docx,.txt"
    
    # Document retention in seconds (default: 1 hour)
    DOCUMENT_RETENTION_SECONDS: int = 3600
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
