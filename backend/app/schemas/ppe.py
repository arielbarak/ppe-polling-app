"""
Pydantic schemas for PPE API endpoints.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class InitiatePPERequest(BaseModel):
    poll_id: str
    prover_id: str
    verifier_id: str
    ppe_type: Optional[str] = None


class InitiatePPEResponse(BaseModel):
    execution_id: str
    ppe_type: str
    challenge_data: Dict[str, Any]
    started_at: datetime


class SubmitPPEResponse(BaseModel):
    success: bool
    failure_reason: Optional[str] = None
    execution_id: str


class PPEStatusResponse(BaseModel):
    execution_id: str
    status: str
    result: Optional[bool] = None
    failure_reason: Optional[str] = None
    duration_seconds: Optional[float] = None