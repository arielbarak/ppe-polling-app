from typing import Dict, Optional, Any
import json
import hashlib
from ..models.poll import Poll, PollCreate, Vote
from ..services.connection_manager import manager
from ..utils.crypto_utils import verify_signature

_polls_db: Dict[str, Poll] = {}

def get_user_id(public_key_jwk: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(public_key_jwk, sort_keys=True).encode()).hexdigest()

class PollService:
    def create_poll(self, poll_data: PollCreate) -> Poll:
        new_poll = Poll(**poll_data.dict())
        _polls_db[new_poll.id] = new_poll
        return new_poll

    def get_poll(self, poll_id: str) -> Optional[Poll]:
        return _polls_db.get(poll_id)

    async def add_registrant(self, poll_id: str, public_key_jwk: Dict[str, Any]) -> Optional[Poll]:
        poll = self.get_poll(poll_id)
        if not poll: return None
        
        user_id = get_user_id(public_key_jwk)
        if user_id not in poll.registrants:
            poll.registrants[user_id] = public_key_jwk
            print(f"User {user_id[:10]}... registered for poll {poll_id}")
            
            # Broadcast that a new user has registered
            await manager.broadcast_to_poll(
                json.dumps({"type": "user_registered", "userId": user_id}),
                poll_id
            )
        
        return poll

    def record_vote(self, poll_id: str, vote: Vote) -> Optional[Poll]:
        poll = self.get_poll(poll_id)
        if not poll: raise ValueError("Poll not found")
        user_id = get_user_id(vote.publicKey)
        if user_id in poll.votes:
            raise ValueError("User has already voted.")
        message_to_verify = f"{poll.id}:{vote.option}"
        if not verify_signature(vote.publicKey, message_to_verify, vote.signature):
            raise ValueError("Invalid signature.")
        poll.votes[user_id] = vote
        return poll

poll_service = PollService()
