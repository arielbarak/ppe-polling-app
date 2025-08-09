from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from ..models.poll import Poll, PollCreate, Vote
from ..services.poll_service import poll_service

router = APIRouter(prefix="/polls", tags=["Polls"])

@router.post("/", response_model=Poll, status_code=status.HTTP_201_CREATED)
async def create_poll(poll_data: PollCreate):
    return poll_service.create_poll(poll_data)

@router.get("/{poll_id}", response_model=Poll)
async def get_poll(poll_id: str):
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    return poll

@router.post("/{poll_id}/register", response_model=Poll)
async def register_for_poll(poll_id: str, public_key: Dict[str, Any]):
    poll = await poll_service.add_registrant(poll_id, public_key)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    return poll

@router.post("/{poll_id}/vote", response_model=Poll)
async def submit_vote(poll_id: str, vote: Vote):
    try:
        updated_poll = poll_service.record_vote(poll_id, vote)
        return updated_poll
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
