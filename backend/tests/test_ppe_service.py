"""
Tests for PPE service.
"""

import pytest
from app.services.ppe_service import PPEService, PPEState


@pytest.fixture
def service():
    return PPEService()


def test_create_session(service):
    """Test session creation."""
    session = service.create_session("user1", "user2", "poll1", "session1")
    
    assert session.user1_id == "user1"
    assert session.user2_id == "user2"
    assert session.poll_id == "poll1"
    assert session.session_id == "session1"
    assert session.user1_state == PPEState.IDLE
    assert session.user2_state == PPEState.IDLE


def test_get_session(service):
    """Test session retrieval."""
    service.create_session("user1", "user2", "poll1", "session1")
    
    session = service.get_session("session1")
    assert session is not None
    assert session.session_id == "session1"


def test_get_or_create_session(service):
    """Test get or create logic."""
    # First call creates
    session1 = service.get_or_create_session("user1", "user2", "poll1", "session1")
    assert session1 is not None
    
    # Second call retrieves
    session2 = service.get_or_create_session("user1", "user2", "poll1", "session1")
    assert session1 is session2


def test_user_state_management(service):
    """Test user state management."""
    session = service.create_session("user1", "user2", "poll1", "session1")
    
    # Initial state
    assert session.get_user_state("user1") == PPEState.IDLE
    
    # Update state
    session.set_user_state("user1", PPEState.CHALLENGE_SENT)
    assert session.get_user_state("user1") == PPEState.CHALLENGE_SENT


def test_both_users_reached_state(service):
    """Test checking if both users reached a state."""
    session = service.create_session("user1", "user2", "poll1", "session1")
    
    session.set_user_state("user1", PPEState.CHALLENGE_SENT)
    assert not session.both_users_reached_state(PPEState.CHALLENGE_SENT)
    
    session.set_user_state("user2", PPEState.CHALLENGE_SENT)
    assert session.both_users_reached_state(PPEState.CHALLENGE_SENT)