"""
Tests for voting flow state machine.
CRITICAL for Issue #7.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock

from app.database import Base
from app.services.state_machine import StateMachine, PollPhase, UserState
from app.models.user import Poll, User
from app.models.certification_state import CertificationState


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_poll(test_db):
    """Create a sample poll in certification phase."""
    poll = Poll(
        id="test_poll_1",
        question="Test question?",
        phase=PollPhase.CERTIFICATION,
        expected_degree=10,
        eta_e=0.125,
        eta_v=0.025
    )
    test_db.add(poll)
    test_db.commit()
    return poll


@pytest.fixture
def sample_user(test_db, sample_poll):
    """Create a sample user."""
    user = User(
        id="user_1", 
        poll_id=sample_poll.id,
        registration_order=0
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def certified_user(test_db, sample_poll):
    """Create a certified user."""
    user = User(
        id="user_certified", 
        poll_id=sample_poll.id,
        registration_order=1
    )
    test_db.add(user)
    
    cert_state = CertificationState(
        user_id=user.id,
        poll_id=sample_poll.id,
        required_ppes=10,
        completed_ppes=10,
        failed_ppes=0,
        is_certified=True
    )
    test_db.add(cert_state)
    test_db.commit()
    
    return user


class TestStateMachine:
    
    def test_can_vote_when_certified_and_voting_phase(self, test_db, sample_poll, certified_user):
        """
        CRITICAL TEST for Issue #7.
        User should be able to vote when:
        1. Poll is in VOTING phase
        2. User is certified
        3. User hasn't voted yet
        """
        # Transition poll to voting
        sample_poll.phase = PollPhase.VOTING
        test_db.commit()
        
        # Check if user can vote
        state_machine = StateMachine(test_db)
        can_vote, reason = state_machine.can_user_vote(certified_user.id, sample_poll.id)
        
        assert can_vote is True, f"User should be able to vote but got: {reason}"
        assert reason is None
    
    def test_cannot_vote_when_not_certified(self, test_db, sample_poll):
        """User cannot vote if not certified."""
        user = User(
            id="user_2", 
            poll_id=sample_poll.id,
            registration_order=2
        )
        test_db.add(user)
        
        cert_state = CertificationState(
            user_id=user.id,
            poll_id=sample_poll.id,
            required_ppes=10,
            completed_ppes=5,  # Not enough
            is_certified=False
        )
        test_db.add(cert_state)
        test_db.commit()
        
        # Transition to voting
        sample_poll.phase = PollPhase.VOTING
        test_db.commit()
        
        state_machine = StateMachine(test_db)
        can_vote, reason = state_machine.can_user_vote(user.id, sample_poll.id)
        
        assert can_vote is False
        assert "not complete" in reason.lower() or "certification" in reason.lower()
    
    def test_cannot_vote_when_excluded(self, test_db, sample_poll):
        """User cannot vote if excluded (too many failures)."""
        user = User(
            id="user_3", 
            poll_id=sample_poll.id,
            registration_order=3
        )
        test_db.add(user)
        
        cert_state = CertificationState(
            user_id=user.id,
            poll_id=sample_poll.id,
            required_ppes=10,
            completed_ppes=8,
            failed_ppes=5,  # Too many
            max_allowed_failures=2,
            is_excluded=True,
            is_certified=False
        )
        test_db.add(cert_state)
        test_db.commit()
        
        sample_poll.phase = PollPhase.VOTING
        test_db.commit()
        
        state_machine = StateMachine(test_db)
        can_vote, reason = state_machine.can_user_vote(user.id, sample_poll.id)
        
        assert can_vote is False
        assert "failed" in reason.lower() or "excluded" in reason.lower()
    
    def test_cannot_vote_twice(self, test_db, sample_poll, certified_user):
        """User cannot vote twice."""
        # Mark as voted
        cert_state = test_db.query(CertificationState).filter_by(
            user_id=certified_user.id,
            poll_id=sample_poll.id
        ).first()
        cert_state.has_voted = True
        test_db.commit()
        
        sample_poll.phase = PollPhase.VOTING
        test_db.commit()
        
        state_machine = StateMachine(test_db)
        can_vote, reason = state_machine.can_user_vote(certified_user.id, sample_poll.id)
        
        assert can_vote is False
        assert "already voted" in reason.lower()
    
    def test_state_transitions(self, test_db, sample_poll):
        """Test phase transitions work correctly."""
        state_machine = StateMachine(test_db)
        
        # Create users
        for i in range(5):
            user = User(
                id=f"user_{i}", 
                poll_id=sample_poll.id,
                registration_order=i
            )
            test_db.add(user)
        test_db.commit()
        
        # Transition to certification
        sample_poll.phase = PollPhase.REGISTRATION
        test_db.commit()
        
        num_transitioned = state_machine.transition_to_certification(sample_poll.id)
        assert num_transitioned == 5
        
        # Check poll phase updated
        test_db.refresh(sample_poll)
        assert sample_poll.phase == PollPhase.CERTIFICATION
        
        # Check certification states created
        cert_states = test_db.query(CertificationState).filter_by(
            poll_id=sample_poll.id
        ).all()
        assert len(cert_states) == 5
    
    def test_record_vote_success(self, test_db, sample_poll, certified_user):
        """Test recording a vote works."""
        sample_poll.phase = PollPhase.VOTING
        test_db.commit()
        
        state_machine = StateMachine(test_db)
        success = state_machine.record_vote(certified_user.id, sample_poll.id)
        
        assert success is True
        
        # Check that user is marked as voted
        cert_state = test_db.query(CertificationState).filter_by(
            user_id=certified_user.id,
            poll_id=sample_poll.id
        ).first()
        assert cert_state.has_voted is True
        assert cert_state.voted_at is not None
    
    def test_get_user_state_detailed(self, test_db, sample_poll, certified_user):
        """Test getting detailed user state."""
        sample_poll.phase = PollPhase.VOTING
        test_db.commit()
        
        state_machine = StateMachine(test_db)
        user_state, reason = state_machine.get_user_state(certified_user.id, sample_poll.id)
        
        assert user_state == UserState.CAN_VOTE
        assert reason is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])