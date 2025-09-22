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

@router.get("/{poll_id}/verify")
async def get_poll_verification_data(poll_id: str):
    """
    Get full poll data with certification graph for public verification.
    This endpoint allows anyone to verify the poll's integrity without needing to register.
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    # Create the certification graph for verification
    certification_graph = {
        "nodes": [],
        "edges": []
    }
    
    # Add all registered users as nodes
    for user_id, public_key in poll.registrants.items():
        vote = poll.votes.get(user_id)
        node_data = {
            "id": user_id,
            "publicKey": public_key,
            "voted": vote is not None,
        }
        
        # Handle vote data - votes can be either Vote objects or dicts
        if vote is not None:
            if isinstance(vote, dict) and "option" in vote:
                node_data["vote"] = vote["option"]
            elif hasattr(vote, "option"):  # Vote object
                node_data["vote"] = vote.option
            else:
                node_data["vote"] = None  # Fallback for unknown vote format
                
        certification_graph["nodes"].append(node_data)
    
    # Add all PPE certifications as edges
    for user_id, certified_peers in poll.ppe_certifications.items():
        for peer_id in certified_peers:
            # Add edge only once (we don't need both directions since it's bidirectional)
            if user_id < peer_id:
                certification_graph["edges"].append({
                    "source": user_id,
                    "target": peer_id,
                    "type": "ppe_certification"
                })
    
    # Add verifications as edges
    for user_id, verifications in poll.verifications.items():
        for verifier_id in verifications.verified_by:
            certification_graph["edges"].append({
                "source": verifier_id,
                "target": user_id,
                "type": "verification"
            })
    
    # Calculate graph metrics for verification
    verification_data = poll_service.verify_poll_integrity(poll)
    
    return {
        "poll_id": poll.id,
        "question": poll.question,
        "options": poll.options,
        "total_participants": len(poll.registrants),
        "total_votes": len(poll.votes),
        "certification_graph": certification_graph,
        "verification": verification_data
    }
