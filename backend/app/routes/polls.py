from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List
import json

from ..models.poll import Poll, PollCreate, Vote
from ..services.poll_service import poll_service, get_user_id

router = APIRouter(prefix="/polls", tags=["Polls"])

@router.post("/", response_model=Poll, status_code=status.HTTP_201_CREATED)
async def create_poll(poll_data: PollCreate):
    """Create a new poll"""
    return poll_service.create_poll(poll_data)

@router.get("/{poll_id}", response_model=Poll)
async def get_poll(poll_id: str):
    """Get poll details by ID"""
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    return poll

@router.post("/{poll_id}/register", response_model=Poll)
async def register_for_poll(poll_id: str, public_key: Dict[str, Any]):
    """Register a user for a poll using their public key"""
    poll = await poll_service.add_registrant(poll_id, public_key)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    return poll

@router.post("/{poll_id}/verify/{user_id}", response_model=Poll)
async def verify_user(poll_id: str, user_id: str, verifier_key: Dict[str, Any]):
    """Verify a user for a specific poll"""
    try:
        verifier_id = get_user_id(verifier_key)
        return poll_service.verify_user(poll_id, verifier_id, user_id)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

@router.post("/{poll_id}/vote", response_model=Poll)
async def submit_vote(poll_id: str, vote: Vote):
    """Submit a vote for a poll"""
    try:
        return poll_service.record_vote(poll_id, vote)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

@router.get("/", response_model=List[Poll])
async def get_all_polls():
    """Get all available polls"""
    return poll_service.get_all_polls()

@router.post("/userid", response_model=str)
async def get_userid(public_key: Dict[str, Any]):
    """Get a user's ID from their public key"""
    return get_user_id(public_key)

@router.get("/{poll_id}/verifications")
async def get_user_verifications(
    poll_id: str, 
    public_key_str: str
):
    """Get verification status for a specific user using their public key"""
    public_key = json.loads(public_key_str)
    user_id = get_user_id(public_key)
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    if user_id not in poll.registrants:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not registered for this poll")
    
    verifications = poll.verifications.get(user_id)
    if not verifications:
        return {
            "verified_by": [],
            "has_verified": [],
            "can_vote": False,
            "verification_count": 0
        }
    
    return {
        "verified_by": list(verifications.verified_by),
        "has_verified": list(verifications.has_verified),
        "can_vote": poll.can_vote(user_id),
        "verification_count": len(verifications.verified_by)
    }

@router.post("/{poll_id}/ppe-certification")
async def record_ppe_certification(
    poll_id: str, 
    certification_data: Dict[str, Any]
):
    """Record a PPE certification between two users"""
    try:
        user1_key = certification_data["user1_public_key"]
        user2_key = certification_data["user2_public_key"]
        
        user1_id = get_user_id(user1_key)
        user2_id = get_user_id(user2_key)
        
        poll = poll_service.record_ppe_certification(poll_id, user1_id, user2_id)
        if not poll:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
        
        return {"message": "PPE certification recorded successfully"}
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except KeyError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Missing required field: {e}")

@router.get("/{poll_id}/ppe-certifications")
async def get_ppe_certifications(
    poll_id: str, 
    public_key_str: str
):
    """Get PPE certifications for a specific user"""
    public_key = json.loads(public_key_str)
    user_id = get_user_id(public_key)
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    if user_id not in poll.registrants:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not registered for this poll")
    
    certifications = poll.get_ppe_certifications(user_id)
    
    return {
        "certified_peers": list(certifications),
        "certification_count": len(certifications)
    }
