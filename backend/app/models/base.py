from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union

class ApiResponse(BaseModel):
    """Base model for API responses to ensure consistent structure"""
    # Allow any fields
    class Config:
        extra = "allow"