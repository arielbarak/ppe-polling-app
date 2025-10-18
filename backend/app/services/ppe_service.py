"""
Service for managing PPE protocol state and execution.
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json


class PPEState(str, Enum):
    """States in the PPE protocol state machine."""
    IDLE = "idle"
    CHALLENGE_SENT = "challenge_sent"
    CHALLENGE_RECEIVED = "challenge_received"
    COMMITMENT_SENT = "commitment_sent"
    COMMITMENT_RECEIVED = "commitment_received"
    SECRET_REVEALED = "secret_revealed"
    COMPLETED = "completed"
    FAILED = "failed"


class PPESession:
    """
    Represents an active PPE session between two peers.
    """
    def __init__(self, user1_id: str, user2_id: str, poll_id: str, session_id: str):
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.poll_id = poll_id
        self.session_id = session_id
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(minutes=10)
        
        # Protocol state for each user
        self.user1_state = PPEState.IDLE
        self.user2_state = PPEState.IDLE
        
        # Challenge data
        self.user1_challenge = None  # Challenge user1 sends to user2
        self.user2_challenge = None  # Challenge user2 sends to user1
        self.user1_secret = None
        self.user2_secret = None
        
        # Commitment data
        self.user1_commitment = None  # User1's commitment to user2's challenge
        self.user2_commitment = None  # User2's commitment to user1's challenge
        self.user1_solution = None
        self.user2_solution = None
        self.user1_nonce = None
        self.user2_nonce = None
        
        # Signatures
        self.user1_signature = None
        self.user2_signature = None
        
        # Completion flag
        self.is_completed = False
        self.is_failed = False
        self.failure_reason = None
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now() > self.expires_at
    
    def get_user_state(self, user_id: str) -> PPEState:
        """Get the state for a specific user."""
        if user_id == self.user1_id:
            return self.user1_state
        elif user_id == self.user2_id:
            return self.user2_state
        else:
            raise ValueError(f"User {user_id} not part of this session")
    
    def set_user_state(self, user_id: str, state: PPEState):
        """Set the state for a specific user."""
        if user_id == self.user1_id:
            self.user1_state = state
        elif user_id == self.user2_id:
            self.user2_state = state
        else:
            raise ValueError(f"User {user_id} not part of this session")
    
    def both_users_reached_state(self, state: PPEState) -> bool:
        """Check if both users have reached a certain state."""
        return self.user1_state == state and self.user2_state == state
    
    def mark_completed(self):
        """Mark the session as completed."""
        self.is_completed = True
        self.user1_state = PPEState.COMPLETED
        self.user2_state = PPEState.COMPLETED
    
    def mark_failed(self, reason: str):
        """Mark the session as failed."""
        self.is_failed = True
        self.failure_reason = reason
        self.user1_state = PPEState.FAILED
        self.user2_state = PPEState.FAILED


class PPEService:
    """
    Service for managing PPE protocol sessions.
    """
    
    def __init__(self):
        # Active sessions: {session_id: PPESession}
        self._sessions: Dict[str, PPESession] = {}
    
    def create_session(self, user1_id: str, user2_id: str, poll_id: str, 
                       session_id: str) -> PPESession:
        """
        Create a new PPE session.
        
        Args:
            user1_id: First user's ID
            user2_id: Second user's ID
            poll_id: Poll identifier
            session_id: Unique session identifier
            
        Returns:
            New PPESession object
        """
        session = PPESession(user1_id, user2_id, poll_id, session_id)
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[PPESession]:
        """Get a session by ID."""
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            # Clean up expired session
            del self._sessions[session_id]
            return None
        return session
    
    def get_or_create_session(self, user1_id: str, user2_id: str, 
                              poll_id: str, session_id: str) -> PPESession:
        """Get existing session or create new one."""
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(user1_id, user2_id, poll_id, session_id)
        return session
    
    def remove_session(self, session_id: str):
        """Remove a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Remove all expired sessions."""
        expired = [sid for sid, session in self._sessions.items() if session.is_expired()]
        for sid in expired:
            del self._sessions[sid]
    
    def get_active_sessions_for_user(self, user_id: str) -> list[PPESession]:
        """Get all active sessions involving a user."""
        return [
            session for session in self._sessions.values()
            if (session.user1_id == user_id or session.user2_id == user_id)
            and not session.is_expired()
        ]


# Singleton instance
ppe_service = PPEService()