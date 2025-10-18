"""
Vote endpoints with proper authorization checks.
FIXES Issue #7: Now properly checks if user can vote.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.database import get_db
from app.services.state_machine import get_state_machine
from app.models.vote import Vote
from app.schemas.vote import VoteRequest, VoteResponse

router = APIRouter(prefix="/api/polls/{poll_id}/vote", tags=["voting"])
logger = logging.getLogger(__name__)


@router.post("", response_model=VoteResponse)
async def cast_vote(
    poll_id: str,
    vote_request: VoteRequest,
    db: Session = Depends(get_db)
):
    """
    Cast a vote in the poll.
    
    FIXED: Now properly checks certification state and poll phase.
    """
    user_id = vote_request.user_id  # TODO: Get from auth token
    
    # CRITICAL FIX: Use state machine to check if user can vote
    state_machine = get_state_machine(db)
    can_vote, reason = state_machine.can_user_vote(user_id, poll_id)
    
    if not can_vote:
        logger.warning(f"Vote denied for user {user_id}: {reason}")
        raise HTTPException(
            status_code=403,
            detail=f"Cannot vote: {reason}"
        )
    
    # Validate vote content
    # ... (your existing validation logic)
    
    # Record the vote
    vote = Vote(
        user_id=user_id,
        poll_id=poll_id,
        response=vote_request.response,
        signature=vote_request.signature
    )
    db.add(vote)
    
    # CRITICAL: Mark user as voted in state machine
    success = state_machine.record_vote(user_id, poll_id)
    if not success:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to record vote")
    
    db.commit()
    
    logger.info(f"Vote recorded for user {user_id} in poll {poll_id}")
    
    return VoteResponse(
        success=True,
        message="Vote recorded successfully",
        vote_id=vote.id
    )


@router.get("/status")
async def get_vote_status(
    poll_id: str,
    user_id: str,  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """
    Check if user can vote and get detailed status.
    
    This helps debug Issue #7.
    """
    state_machine = get_state_machine(db)
    
    # Get detailed state
    user_state, reason = state_machine.get_user_state(user_id, poll_id)
    can_vote, vote_reason = state_machine.can_user_vote(user_id, poll_id)
    
    return {
        "can_vote": can_vote,
        "user_state": user_state,
        "reason": reason or vote_reason,
        "poll_id": poll_id,
        "user_id": user_id
    }