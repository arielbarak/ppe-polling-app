"""
Certification state API endpoints.
FIXES Issue #5: State persistence.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from app.database import get_db
from app.models.certification_state import CertificationState
from app.services.ppe_assignment_service import get_assignment_service

router = APIRouter(prefix="/api/polls/{poll_id}/certification", tags=["certification"])


@router.get("/state")
async def get_certification_state(
    poll_id: str,
    user_id: str,  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """
    Get user's certification state.
    
    FIXES Issue #5: Frontend can restore state on refresh.
    """
    cert_state = db.query(CertificationState).filter_by(
        user_id=user_id,
        poll_id=poll_id
    ).first()
    
    if not cert_state:
        return {
            "exists": False,
            "message": "No certification state found"
        }
    
    return {
        "exists": True,
        "state": cert_state.to_dict()
    }


@router.get("/assignments")
async def get_ppe_assignments(
    poll_id: str,
    user_id: str,  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """
    Get PPE partner assignments.
    
    FIXES Issue #2: Frontend auto-loads assignments, no button needed.
    """
    assignment_service = get_assignment_service(db)
    assignments = assignment_service.get_user_assignments(user_id, poll_id)
    
    return assignments


@router.post("/complete-ppe")
async def complete_ppe(
    poll_id: str,
    user_id: str,
    partner_id: str,
    ppe_id: str,
    signature: str,
    db: Session = Depends(get_db)
):
    """Record PPE completion."""
    cert_state = db.query(CertificationState).filter_by(
        user_id=user_id,
        poll_id=poll_id
    ).first()
    
    if not cert_state:
        raise HTTPException(status_code=404, detail="Certification state not found")
    
    cert_state.add_completed_ppe(ppe_id, partner_id, signature)
    db.commit()
    
    return {
        "success": True,
        "state": cert_state.to_dict()
    }


@router.post("/fail-ppe")
async def fail_ppe(
    poll_id: str,
    user_id: str,
    ppe_id: str,
    db: Session = Depends(get_db)
):
    """Record PPE failure."""
    cert_state = db.query(CertificationState).filter_by(
        user_id=user_id,
        poll_id=poll_id
    ).first()
    
    if not cert_state:
        raise HTTPException(status_code=404, detail="Certification state not found")
    
    cert_state.add_failed_ppe(ppe_id)
    db.commit()
    
    return {
        "success": True,
        "state": cert_state.to_dict()
    }