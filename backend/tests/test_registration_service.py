"""
Tests for registration service.
"""

import pytest
from app.services.registration_service import RegistrationService


@pytest.fixture
def service():
    """Create a fresh registration service."""
    return RegistrationService()


def test_create_challenge(service):
    """Test challenge creation."""
    challenge = service.create_challenge("test-poll-1")
    
    assert "challenge_id" in challenge
    assert "challenge_text" in challenge
    assert "expires_at" in challenge
    assert challenge["poll_id"] == "test-poll-1"


def test_create_challenge_with_difficulty(service):
    """Test challenge creation with custom difficulty."""
    easy_challenge = service.create_challenge("test-poll-1", difficulty="easy")
    hard_challenge = service.create_challenge("test-poll-2", difficulty="hard")
    
    # Just verify they're created successfully
    assert easy_challenge["challenge_id"] is not None
    assert hard_challenge["challenge_id"] is not None


def test_validate_challenge_invalid_id(service):
    """Test validation with invalid challenge ID."""
    result = service.validate_challenge("invalid-id", "any-solution")
    assert result is False


def test_get_challenge_info(service):
    """Test retrieving challenge info."""
    challenge = service.create_challenge("test-poll-1")
    
    info = service.get_challenge_info(challenge["challenge_id"])
    
    assert info is not None
    assert info["challenge_id"] == challenge["challenge_id"]
    assert "is_expired" in info
    assert "created_at" in info


def test_get_challenge_info_invalid(service):
    """Test getting info for non-existent challenge."""
    info = service.get_challenge_info("invalid-id")
    assert info is None