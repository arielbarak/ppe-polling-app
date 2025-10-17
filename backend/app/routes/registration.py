"""
API routes for registration with initial PPE challenges.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ..services.registration_service import registration_service


router = APIRouter(prefix="/registration", tags=["Registration"])


class ChallengeRequest(BaseModel):
    """Request model for creating a challenge."""
    poll_id: str
    difficulty: Optional[str] = None


class ChallengeValidation(BaseModel):
    """Request model for validating a challenge."""
    challenge_id: str
    solution: str


@router.post("/challenge")
async def create_challenge(request: ChallengeRequest):
    """
    Create a registration challenge for a poll.
    
    This is the first step in registration - user requests a challenge,
    solves it, and then submits registration with the solution.
    
    Args:
        request: Challenge request with poll_id and optional difficulty
        
    Returns:
        Challenge ID and challenge text
    """
    try:
        challenge_data = registration_service.create_challenge(
            poll_id=request.poll_id,
            difficulty=request.difficulty
        )
        
        return {
            "success": True,
            "challenge": challenge_data
        }
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to create challenge: {str(e)}"
        )


@router.post("/validate")
async def validate_challenge(validation: ChallengeValidation):
    """
    Validate a challenge solution.
    
    This endpoint can be used to pre-validate before submitting full registration,
    or the validation can happen during registration itself.
    
    Args:
        validation: Challenge ID and solution
        
    Returns:
        Whether the solution is valid
    """
    is_valid = registration_service.validate_challenge(
        challenge_id=validation.challenge_id,
        solution=validation.solution
    )
    
    return {
        "valid": is_valid,
        "message": "Challenge validated successfully" if is_valid else "Invalid solution or expired challenge"
    }


@router.get("/challenge/{challenge_id}")
async def get_challenge(challenge_id: str):
    """
    Get information about a challenge.
    
    This can be used to check if a challenge is still valid.
    
    Args:
        challenge_id: Challenge identifier
        
    Returns:
        Challenge information
    """
    challenge_info = registration_service.get_challenge_info(challenge_id)
    
    if not challenge_info:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Challenge not found or expired"
        )
    
    return challenge_info