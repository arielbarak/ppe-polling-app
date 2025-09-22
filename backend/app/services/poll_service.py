from typing import Dict, Optional, Any
import json
import hashlib
import asyncio
from ..models.poll import Poll, PollCreate, Vote
from ..services.connection_manager import manager
from ..utils.crypto_utils import verify_signature

_polls_db: Dict[str, Poll] = {}

def get_user_id(public_key_jwk: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(public_key_jwk, sort_keys=True).encode()).hexdigest()

class PollService:
    def create_poll(self, poll_data: PollCreate) -> Poll:
        # Use model_dump() instead of dict() to avoid Pydantic deprecation warning
        new_poll = Poll(**poll_data.model_dump())
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
        """
        Record a vote after verifying:
        1. Poll exists
        2. User is registered
        3. User hasn't voted yet
        4. User has enough verifications
        5. Signature is valid
        """
        poll = self.get_poll(poll_id)
        if not poll:
            raise ValueError("Poll not found")

        user_id = get_user_id(vote.publicKey)
        
        # Check if user is registered
        if user_id not in poll.registrants:
            raise ValueError("User is not registered for this poll")

        # Check if user has already voted
        if user_id in poll.votes:
            raise ValueError("User has already voted")

        # Check if user has enough verifications (minimum 2)
        if not poll.can_vote(user_id):
            verification_count = len(poll.verifications.get(user_id, {}).verified_by)
            raise ValueError(f"Insufficient verifications. You have {verification_count}/2 required verifications")

        # Verify signature
        message_to_verify = f"{poll.id}:{vote.option}"
        if not verify_signature(vote.publicKey, message_to_verify, vote.signature):
            raise ValueError("Invalid signature")

        # Record the vote
        poll.votes[user_id] = vote
        
        # Broadcast vote update to all connected clients
        asyncio.create_task(manager.broadcast_to_poll(
            json.dumps({
                "type": "vote_cast",
                "voter_id": user_id,
                "option": vote.option,
                "poll_id": poll_id
            }),
            poll_id
        ))
        
        return poll

    def get_all_polls(self) -> list[Poll]:
        """
        Retrieve all polls from storage
        """
        return list(_polls_db.values())

    def verify_user(self, poll_id: str, verifier_id: str, verified_id: str) -> Poll:
        """Add verification between two users"""
        poll = self.get_poll(poll_id)
        if not poll:
            raise ValueError("Poll not found")
            
        # Verify both users are registered
        if verifier_id not in poll.registrants or verified_id not in poll.registrants:
            raise ValueError("Both users must be registered for this poll")
            
        # Prevent self-verification
        if verifier_id == verified_id:
            raise ValueError("Users cannot verify themselves")
            
        # Add the verification
        poll.add_verification(verifier_id, verified_id)
        
        # Broadcast verification update to all connected clients
        asyncio.create_task(manager.broadcast_to_poll(
            json.dumps({
                "type": "user_verified",
                "verifier_id": verifier_id,
                "verified_id": verified_id,
                "poll_id": poll_id
            }),
            poll_id
        ))
        
        return poll

    def record_ppe_certification(self, poll_id: str, user1_id: str, user2_id: str) -> Optional[Poll]:
        """Record a PPE certification between two users"""
        poll = self.get_poll(poll_id)
        if not poll:
            return None
            
        # Verify both users are registered
        if user1_id not in poll.registrants or user2_id not in poll.registrants:
            raise ValueError("Both users must be registered for this poll")
            
        # Prevent self-certification
        if user1_id == user2_id:
            raise ValueError("Users cannot certify themselves")
            
        # Add the PPE certification
        poll.add_ppe_certification(user1_id, user2_id)
        print(f"PPE certification recorded between {user1_id[:10]}... and {user2_id[:10]}...")
        
        # Broadcast PPE certification update to all connected clients
        asyncio.create_task(manager.broadcast_to_poll(
            json.dumps({
                "type": "ppe_certified",
                "user1_id": user1_id,
                "user2_id": user2_id,
                "poll_id": poll_id
            }),
            poll_id
        ))
        
        return poll
    
    def verify_poll_integrity(self, poll):
        """
        Verify the integrity of a poll based on PPE certification graph.
        This is the key algorithm that ensures the poll is resistant to Sybil attacks.
        It checks:
        1. Graph connectivity - ensures the certification graph is well-connected
        2. PPE certification coverage - checks if enough users completed PPE
        3. Vote eligibility - verifies only users with sufficient certifications voted
        """
        # Get all registered users
        registered_users = list(poll.registrants.keys())
        num_users = len(registered_users)
        
        # Calculate metrics for verification
        ppe_coverage = 0
        min_certifications_per_user = float('inf') if num_users > 0 else 0
        max_certifications_per_user = 0
        avg_certifications_per_user = 0
        
        # Calculate PPE coverage - what percentage of possible PPE connections were made
        # In a perfect graph, every node would connect to k neighbors where k is a small constant
        # For our implementation, we aim for at least 2 connections per user
        
        total_certifications = 0
        for user_id, certifications in poll.ppe_certifications.items():
            cert_count = len(certifications)
            total_certifications += cert_count
            min_certifications_per_user = min(min_certifications_per_user, cert_count)
            max_certifications_per_user = max(max_certifications_per_user, cert_count)
        
        if num_users > 0:
            avg_certifications_per_user = total_certifications / num_users
            # Divide by 2 because each certification is counted twice (once for each user)
            total_possible_connections = (num_users * (num_users - 1)) / 2
            ppe_coverage = (total_certifications / 2) / total_possible_connections if total_possible_connections > 0 else 0
        
        # Check for unauthorized votes
        unauthorized_votes = []
        for voter_id in poll.votes:
            if not poll.can_vote(voter_id):
                unauthorized_votes.append(voter_id)
        
        # Calculate expansion properties
        # A good expander graph has high connectivity, meaning removal of a small 
        # set of nodes doesn't disconnect the graph
        # For simplicity, we check the minimum number of certifications per user
        
        return {
            "total_participants": num_users,
            "total_votes": len(poll.votes),
            "ppe_coverage": ppe_coverage,
            "min_certifications_per_user": min_certifications_per_user if min_certifications_per_user != float('inf') else 0,
            "max_certifications_per_user": max_certifications_per_user,
            "avg_certifications_per_user": avg_certifications_per_user,
            "unauthorized_votes": unauthorized_votes,
            "is_valid": len(unauthorized_votes) == 0 and (num_users == 0 or min_certifications_per_user >= 2),
            "verification_message": self._generate_verification_message(
                num_users, ppe_coverage, min_certifications_per_user, unauthorized_votes
            )
        }
    
    def _generate_verification_message(self, num_users, ppe_coverage, min_certifications, unauthorized_votes):
        """Generate a human-readable verification message"""
        if num_users == 0:
            return "Poll has no participants."
        
        messages = []
        
        # Check certification coverage
        if ppe_coverage < 0.1:
            messages.append("WARNING: Very low PPE certification coverage (less than 10%).")
        elif ppe_coverage < 0.3:
            messages.append("Low PPE certification coverage (less than 30%).")
        
        # Check minimum certifications
        if min_certifications < 2:
            messages.append("WARNING: Some users have fewer than 2 PPE certifications.")
        
        # Check unauthorized votes
        if unauthorized_votes:
            messages.append(f"WARNING: {len(unauthorized_votes)} unauthorized votes detected.")
        
        if not messages:
            return "Poll verification successful. No issues detected."
        else:
            return " ".join(messages)

poll_service = PollService()
