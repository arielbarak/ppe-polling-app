"""
Tests for verification service.
"""

import pytest
from app.services.verification_service import VerificationService
from app.models.poll import Poll, Vote


@pytest.fixture
def verification_service():
    return VerificationService()


@pytest.fixture
def valid_poll():
    """Create a valid poll for testing."""
    poll = Poll(
        id="test-poll",
        question="Test?",
        options=["A", "B"]
    )
    
    # Add participants
    poll.registrants = {
        f"user{i}": {"kty": "EC", "x": f"x{i}", "y": f"y{i}"}
        for i in range(5)
    }
    
    # Add complete certifications (everyone certified by everyone)
    poll.ppe_certifications = {
        f"user{i}": {f"user{j}" for j in range(5) if j != i}
        for i in range(5)
    }
    
    return poll


def test_verify_basic_structure(verification_service, valid_poll):
    """Test basic structure verification."""
    result = verification_service.verify_poll_comprehensive(valid_poll)
    
    assert "total_participants" in result.metrics
    assert result.metrics["total_participants"] == 5


def test_detect_no_certifications(verification_service):
    """Test detection of missing certifications."""
    poll = Poll(
        id="test-poll",
        question="Test?",
        options=["A", "B"]
    )
    poll.registrants = {"user1": {}, "user2": {}}
    poll.ppe_certifications = {}
    
    result = verification_service.verify_poll_comprehensive(poll)
    
    assert len(result.warnings) > 0


def test_verify_connected_graph(verification_service, valid_poll):
    """Test graph connectivity verification."""
    result = verification_service.verify_poll_comprehensive(valid_poll)
    
    assert "connectivity" in result.analysis
    assert result.analysis["connectivity"]["is_connected"]