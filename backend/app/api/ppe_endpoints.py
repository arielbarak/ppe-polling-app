"""
Enhanced PPE API endpoints with support for multiple PPE types.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
import logging

from app.database import get_db
from app.models.ppe_types import PPEType, PPEConfig, PPEExecution
from app.services.ppe_executor import get_ppe_executor
from app.schemas.ppe import (
    InitiatePPERequest,
    InitiatePPEResponse,
    SubmitPPEResponse,
    PPEStatusResponse
)

router = APIRouter(prefix="/api/ppe", tags=["ppe"])
logger = logging.getLogger(__name__)


@router.post("/initiate", response_model=InitiatePPEResponse)
async def initiate_ppe(
    request: InitiatePPERequest,
    db: Session = Depends(get_db)
):
    """
    Initiate a new PPE between two users.
    
    Supports multiple PPE types:
    - symmetric_captcha
    - proof_of_storage
    - computational
    - social_distance
    """
    try:
        executor = get_ppe_executor(db)
        
        execution = executor.initiate_ppe(
            poll_id=request.poll_id,
            prover_id=request.prover_id,
            verifier_id=request.verifier_id,
            ppe_type=PPEType(request.ppe_type) if request.ppe_type else None
        )
        
        return InitiatePPEResponse(
            execution_id=execution.id,
            ppe_type=execution.ppe_type,
            challenge_data=execution.challenge_data,
            started_at=execution.started_at
        )
        
    except Exception as e:
        logger.error(f"Failed to initiate PPE: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit/{execution_id}")
async def submit_ppe_response(
    execution_id: str,
    response: dict,
    db: Session = Depends(get_db)
):
    """Submit response to PPE challenge."""
    try:
        executor = get_ppe_executor(db)
        
        success, failure_reason = executor.submit_response(
            execution_id=execution_id,
            prover_response=response
        )
        
        return SubmitPPEResponse(
            success=success,
            failure_reason=failure_reason,
            execution_id=execution_id
        )
        
    except Exception as e:
        logger.error(f"Failed to submit PPE response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{execution_id}", response_model=PPEStatusResponse)
async def get_ppe_status(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """Get status of PPE execution."""
    execution = db.query(PPEExecution).filter_by(id=execution_id).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="PPE execution not found")
    
    return PPEStatusResponse(
        execution_id=execution.id,
        status=execution.status,
        result=execution.result,
        failure_reason=execution.failure_reason,
        duration_seconds=execution.duration_seconds
    )


@router.get("/active/{poll_id}/{user_id}")
async def get_active_ppes(
    poll_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all active PPEs for a user in a poll."""
    executor = get_ppe_executor(db)
    active = executor.get_active_ppes(user_id, poll_id)
    
    return {
        "active_ppes": [exec.to_dict() for exec in active],
        "count": len(active)
    }


@router.get("/config/{poll_id}")
async def get_ppe_config(
    poll_id: str,
    db: Session = Depends(get_db)
):
    """Get PPE configuration for a poll."""
    config = db.query(PPEConfig).filter_by(poll_id=poll_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="PPE config not found")
    
    return config.to_dict()


@router.get("/types")
async def list_ppe_types():
    """List all available PPE types with descriptions."""
    return {
        "types": [
            {
                "type": PPEType.SYMMETRIC_CAPTCHA,
                "name": "Symmetric CAPTCHA",
                "description": "Both users solve CAPTCHAs",
                "effort": "Medium",
                "security": "High"
            },
            {
                "type": PPEType.PROOF_OF_STORAGE,
                "name": "Proof of Storage",
                "description": "Verify access to cloud storage",
                "effort": "Low",
                "security": "Medium-High"
            },
            {
                "type": PPEType.COMPUTATIONAL,
                "name": "Computational",
                "description": "Proof-of-work puzzle",
                "effort": "Variable",
                "security": "Very High"
            },
            {
                "type": PPEType.SOCIAL_DISTANCE,
                "name": "Social Network Distance",
                "description": "Reduced effort for social connections",
                "effort": "Variable (based on connection)",
                "security": "High"
            }
        ]
    }


@router.post("/cleanup/{poll_id}")
async def cleanup_expired_ppes(
    poll_id: str,
    db: Session = Depends(get_db)
):
    """Clean up expired PPE executions."""
    executor = get_ppe_executor(db)
    executor.cleanup_expired_ppes(poll_id)
    
    return {"success": True, "message": "Expired PPEs cleaned up"}


# Convenience endpoint for getting available types for a specific poll
@router.get("/available-types/{poll_id}")
async def get_available_ppe_types(
    poll_id: str,
    db: Session = Depends(get_db)
):
    """Get PPE types available for a specific poll."""
    config = db.query(PPEConfig).filter_by(poll_id=poll_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="PPE config not found")
    
    all_types = {
        PPEType.SYMMETRIC_CAPTCHA: {
            "name": "Symmetric CAPTCHA",
            "description": "Both users solve CAPTCHAs",
            "effort": "Medium",
            "security": "High"
        },
        PPEType.PROOF_OF_STORAGE: {
            "name": "Proof of Storage",
            "description": "Verify access to cloud storage",
            "effort": "Low",
            "security": "Medium-High"
        },
        PPEType.COMPUTATIONAL: {
            "name": "Computational",
            "description": "Proof-of-work puzzle",
            "effort": "Variable",
            "security": "Very High"
        },
        PPEType.SOCIAL_DISTANCE: {
            "name": "Social Network Distance",
            "description": "Reduced effort for social connections",
            "effort": "Variable (based on connection)",
            "security": "High"
        }
    }
    
    available = []
    for ppe_type in config.allowed_certification_types:
        if ppe_type in all_types:
            type_info = all_types[ppe_type].copy()
            type_info["type"] = ppe_type
            type_info["is_default"] = (ppe_type == config.default_certification_type)
            available.append(type_info)
    
    return {
        "poll_id": poll_id,
        "available_types": available,
        "default_type": config.default_certification_type
    }