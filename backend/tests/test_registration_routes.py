"""
Tests for registration API routes.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_create_challenge(client):
    """Test challenge creation endpoint."""
    response = client.post(
        "/registration/challenge",
        json={
            "poll_id": "test-poll-1",
            "difficulty": "medium"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "challenge" in data
    assert "challenge_id" in data["challenge"]
    assert "challenge_text" in data["challenge"]


def test_validate_challenge_invalid(client):
    """Test validation with invalid challenge."""
    response = client.post(
        "/registration/validate",
        json={
            "challenge_id": "invalid-id",
            "solution": "wrong"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


def test_get_challenge_info(client):
    """Test getting challenge info."""
    # Create challenge first
    create_response = client.post(
        "/registration/challenge",
        json={"poll_id": "test-poll-1"}
    )
    challenge_id = create_response.json()["challenge"]["challenge_id"]
    
    # Get info
    response = client.get(f"/registration/challenge/{challenge_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["challenge_id"] == challenge_id


def test_get_challenge_info_not_found(client):
    """Test getting info for non-existent challenge."""
    response = client.get("/registration/challenge/invalid-id")
    assert response.status_code == 404


def test_registration_with_challenge_validation(client):
    """Test full registration flow with challenge."""
    # Create poll
    poll_response = client.post(
        "/polls/",
        json={
            "question": "Test Poll",
            "options": ["Option 1", "Option 2"]
        }
    )
    poll_id = poll_response.json()["id"]
    
    # Request challenge
    challenge_response = client.post(
        "/registration/challenge",
        json={"poll_id": poll_id}
    )
    challenge = challenge_response.json()["challenge"]
    
    # Try to register without solving challenge (should fail)
    register_response = client.post(
        f"/polls/{poll_id}/register",
        json={
            "public_key": {"kty": "EC", "crv": "P-256", "x": "test_x", "y": "test_y"},
            "challenge_id": challenge["challenge_id"],
            "challenge_solution": "wrong_solution"
        }
    )
    
    assert register_response.status_code == 400