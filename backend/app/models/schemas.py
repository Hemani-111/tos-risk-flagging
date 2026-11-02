from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    modelVersion: Optional[str] = None


class DocumentInfo(BaseModel):
    filename: str
    title: Optional[str] = None
    file_type: Optional[str] = None
