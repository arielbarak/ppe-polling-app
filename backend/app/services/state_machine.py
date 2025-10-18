"""
Voting flow state machine.
Implements proper state transitions per PPE paper Protocol sequence.

States:
- UNREGISTERED: User hasn't registered
- REGISTERED: Completed registration (one-sided PPE)
- AWAITING_ASSIGNMENTS: Waiting for graph generation
- CERTIFYING: Completing peer PPEs (two-sided)
- CERTIFIED: Passed certification, can vote
- FAILED_CERTIFICATION: Failed too many PPEs
- VOTED: Already voted
- POLL_CLOSED: Poll ended
"""

from enum import Enum
from typing import Optional, Tuple
import logging
from datetime import datetime, timezone

from app.models.user import User, Poll
from app.models.certification_state import CertificationState

logger = logging.getLogger(__name__)


class PollPhase(str, Enum):
    """Poll phases from PPE paper Section 3"""
    SETUP = "setup"                      # Parameter announcement
    REGISTRATION = "registration"        # Protocol 2 (one-sided PPE)
    CERTIFICATION = "certification"      # Protocol 3 (two-sided PPE)
    VOTING = "voting"                    # Protocol 4 (response)
    TALLYING = "tallying"                # Protocol 5 (results)
    VERIFICATION = "verification"        # Protocol 6 (verify)
    CLOSED = "closed"


class UserState(str, Enum):
    """User states within a poll"""
    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    AWAITING_ASSIGNMENTS = "awaiting_assignments"
    CERTIFYING = "certifying"
    CERTIFIED = "certified"
    FAILED_CERTIFICATION = "failed_certification"
    CAN_VOTE = "can_vote"
    VOTED = "voted"
    EXCLUDED = "excluded"  # Marked as deleted node


class StateMachine:
    """
    Manages state transitions for voting flow.
    Based on PPE paper protocol phases.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_user_state(
        self, 
        user_id: str, 
        poll_id: str
    ) -> Tuple[UserState, Optional[str]]:
        """
        Get current state of user in poll.
        
        Returns:
            (state, reason) where reason explains why user can't vote if applicable
        """
        # Get poll and check phase
        poll = self.db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            return UserState.UNREGISTERED, "Poll not found"
        
        # Check if user registered
        user = self.db.query(User).filter_by(id=user_id, poll_id=poll_id).first()
        if not user:
            return UserState.UNREGISTERED, "Not registered for this poll"
        
        # Check poll phase
        if poll.phase == PollPhase.SETUP:
            return UserState.UNREGISTERED, "Poll not yet open for registration"
        
        if poll.phase == PollPhase.CLOSED:
            return UserState.EXCLUDED, "Poll has closed"
        
        # User is registered
        if poll.phase == PollPhase.REGISTRATION:
            return UserState.REGISTERED, "Waiting for registration to close"
        
        # Get certification state
        cert_state = self.db.query(CertificationState).filter_by(
            user_id=user_id,
            poll_id=poll_id
        ).first()
        
        if not cert_state:
            # Registration closed but no assignments yet
            if poll.phase == PollPhase.CERTIFICATION:
                return UserState.AWAITING_ASSIGNMENTS, "Waiting for PPE assignments"
            return UserState.REGISTERED, "Certification not yet started"
        
        # Check if excluded (too many failed PPEs)
        if cert_state.is_excluded:
            return UserState.EXCLUDED, f"Failed {cert_state.failed_ppes} PPEs (max allowed: {cert_state.max_allowed_failures})"
        
        # In certification phase
        if poll.phase == PollPhase.CERTIFICATION:
            if cert_state.is_certified:
                return UserState.CERTIFIED, "Waiting for voting phase to open"
            return UserState.CERTIFYING, f"Complete {cert_state.required_ppes - cert_state.completed_ppes} more PPEs"
        
        # Voting phase
        if poll.phase == PollPhase.VOTING:
            if not cert_state.is_certified:
                return UserState.FAILED_CERTIFICATION, "Did not complete certification in time"
            
            if cert_state.has_voted:
                return UserState.VOTED, "Already voted"
            
            return UserState.CAN_VOTE, None  # CAN VOTE!
        
        # Post-voting phases
        if poll.phase in [PollPhase.TALLYING, PollPhase.VERIFICATION]:
            if cert_state.has_voted:
                return UserState.VOTED, "Poll closed, vote counted"
            return UserState.EXCLUDED, "Did not vote in time"
        
        return UserState.UNREGISTERED, "Unknown state"
    
    def can_user_vote(self, user_id: str, poll_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user can vote RIGHT NOW.
        
        This is the critical function for authorization.
        
        Returns:
            (can_vote, reason_if_not)
        """
        state, reason = self.get_user_state(user_id, poll_id)
        
        if state == UserState.CAN_VOTE:
            return True, None
        
        return False, reason
    
    def transition_to_certification(self, poll_id: str) -> int:
        """
        Transition poll from REGISTRATION to CERTIFICATION phase.
        Called when registration closes.
        
        Returns:
            Number of users transitioned
        """
        logger.info(f"Transitioning poll {poll_id} to CERTIFICATION phase")
        
        poll = self.db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            raise ValueError(f"Poll {poll_id} not found")
        
        if poll.phase != PollPhase.REGISTRATION:
            raise ValueError(f"Poll is in {poll.phase} phase, expected REGISTRATION")
        
        # Update poll phase
        poll.phase = PollPhase.CERTIFICATION
        poll.certification_started_at = datetime.now(timezone.utc)
        
        # Transition all registered users to AWAITING_ASSIGNMENTS
        users = self.db.query(User).filter_by(poll_id=poll_id).all()
        
        for user in users:
            # Create certification state if doesn't exist
            cert_state = self.db.query(CertificationState).filter_by(
                user_id=user.id,
                poll_id=poll_id
            ).first()
            
            if not cert_state:
                cert_state = CertificationState(
                    user_id=user.id,
                    poll_id=poll_id,
                    state=UserState.AWAITING_ASSIGNMENTS
                )
                self.db.add(cert_state)
        
        self.db.commit()
        
        logger.info(f"Transitioned {len(users)} users to certification phase")
        return len(users)
    
    def transition_to_voting(self, poll_id: str) -> Tuple[int, int]:
        """
        Transition poll from CERTIFICATION to VOTING phase.
        Called when certification period ends.
        
        Returns:
            (num_certified, num_excluded)
        """
        logger.info(f"Transitioning poll {poll_id} to VOTING phase")
        
        poll = self.db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            raise ValueError(f"Poll {poll_id} not found")
        
        if poll.phase != PollPhase.CERTIFICATION:
            raise ValueError(f"Poll is in {poll.phase} phase, expected CERTIFICATION")
        
        # Update poll phase
        poll.phase = PollPhase.VOTING
        poll.voting_started_at = datetime.now(timezone.utc)
        
        # Count certified vs excluded users
        cert_states = self.db.query(CertificationState).filter_by(
            poll_id=poll_id
        ).all()
        
        num_certified = 0
        num_excluded = 0
        
        for cert_state in cert_states:
            if cert_state.is_certified and not cert_state.is_excluded:
                num_certified += 1
            else:
                num_excluded += 1
        
        self.db.commit()
        
        logger.info(f"Transitioned to voting: {num_certified} certified, {num_excluded} excluded")
        return num_certified, num_excluded
    
    def record_vote(self, user_id: str, poll_id: str) -> bool:
        """
        Record that user has voted.
        
        Returns:
            True if vote recorded, False if user cannot vote
        """
        can_vote, reason = self.can_user_vote(user_id, poll_id)
        
        if not can_vote:
            logger.warning(f"User {user_id} cannot vote: {reason}")
            return False
        
        # Mark as voted
        cert_state = self.db.query(CertificationState).filter_by(
            user_id=user_id,
            poll_id=poll_id
        ).first()
        
        cert_state.has_voted = True
        cert_state.voted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        logger.info(f"User {user_id} voted in poll {poll_id}")
        return True


def get_state_machine(db_session) -> StateMachine:
    """Factory function for state machine."""
    return StateMachine(db_session)