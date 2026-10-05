from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class HealthResponse(BaseModel):
    status: str
    version: str


class DocumentInfo(BaseModel):
    filename: str
    title: Optional[str] = None
    file_type: Optional[str] = None
