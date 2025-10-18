"""
API routes for PPE protocol management.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel

from ..services.ppe_service import ppe_service, PPEState
from ..services.poll_service import poll_service
from ..utils.ppe_utils import (
    create_ppe_session_id,
    verify_challenge_generation,
    verify_commitment,
    verify_solution_correctness
)


router = APIRouter(prefix="/polls/{poll_id}/ppe", tags=["PPE"])


class InitiatePPERequest(BaseModel):
    """Request to initiate PPE with a peer."""
    user1_id: str
    user2_id: str


class PPEChallengeData(BaseModel):
    """Challenge data for PPE."""
    session_id: str
    challenge_text: str
    secret: str  # Will be revealed later


class PPECommitmentData(BaseModel):
    """Commitment data for PPE."""
    session_id: str
    commitment: str
    user_id: str


class PPERevealData(BaseModel):
    """Data for revealing secret and opening commitment."""
    session_id: str
    secret: str
    solution: str
    nonce: str
    user_id: str


class PPESignatureData(BaseModel):
    """Signature data for PPE completion."""
    session_id: str
    signature: str
    user_id: str


@router.post("/initiate")
async def initiate_ppe(poll_id: str, request: InitiatePPERequest):
    """
    Initiate a PPE session between two users.
    
    This creates the session and returns the session ID.
    The actual protocol proceeds via WebSocket.
    
    Args:
        poll_id: Poll identifier
        request: User IDs for the PPE session
        
    Returns:
        Session ID for tracking
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    # Verify both users are registered
    if request.user1_id not in poll.registrants or request.user2_id not in poll.registrants:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Both users must be registered for the poll"
        )
    
    # Create session
    session_id = create_ppe_session_id(request.user1_id, request.user2_id, poll_id)
    session = ppe_service.get_or_create_session(
        request.user1_id, request.user2_id, poll_id, session_id
    )
    
    return {
        "session_id": session_id,
        "user1_id": request.user1_id,
        "user2_id": request.user2_id,
        "message": "PPE session initiated"
    }


@router.get("/session/{session_id}")
async def get_ppe_session(poll_id: str, session_id: str):
    """
    Get the status of a PPE session.
    
    Args:
        poll_id: Poll identifier
        session_id: Session identifier
        
    Returns:
        Session status
    """
    session = ppe_service.get_session(session_id)
    
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found or expired")
    
    return {
        "session_id": session_id,
        "user1_id": session.user1_id,
        "user2_id": session.user2_id,
        "user1_state": session.user1_state,
        "user2_state": session.user2_state,
        "is_completed": session.is_completed,
        "is_failed": session.is_failed,
        "failure_reason": session.failure_reason
    }


@router.post("/complete/{session_id}")
async def complete_ppe_session(poll_id: str, session_id: str):
    """
    Mark a PPE session as completed and record the certification.
    
    This should be called after both users have successfully verified
    each other's challenges and exchanged signatures.
    
    Args:
        poll_id: Poll identifier
        session_id: Session identifier
        
    Returns:
        Success message
    """
    session = ppe_service.get_session(session_id)
    
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    
    if not session.is_completed:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Session not ready to complete"
        )
    
    # Record PPE certification in the poll
    poll = poll_service.record_ppe_certification(
        poll_id, session.user1_id, session.user2_id
    )
    
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    # Clean up session
    ppe_service.remove_session(session_id)
    
    return {
        "message": "PPE certification recorded successfully",
        "user1_id": session.user1_id,
        "user2_id": session.user2_id
    }