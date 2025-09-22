import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from app.main import app
from app.models.poll import Poll, UserVerification

client = TestClient(app)

@pytest.fixture
def mock_poll_service():
    with patch('app.routes.polls.poll_service') as mock_service:
        # Setup mock returns for various poll service methods
        poll = Poll(
            id="test-poll-id",
            question="Test Question",
            options=["Option 1", "Option 2"],
            registrants={"user1": {"key": "public-key-1"}, "user2": {"key": "public-key-2"}},
            votes={"user1": {"publicKey": {"key": "public-key-1"}, "option": "Option 1", "signature": "sig1"}},
            verifications={"user1": UserVerification(verified_by={"user2"}, has_verified=set()),
                          "user2": UserVerification(verified_by={"user1"}, has_verified=set())},
            ppe_certifications={"user1": {"user2"}, "user2": {"user1"}}
        )
        
        # Configure the mock to return poll objects properly
        mock_service.create_poll.return_value = poll
        mock_service.get_poll.return_value = poll
        mock_service.get_all_polls.return_value = [poll]
        mock_service.verify_user.return_value = poll
        mock_service.record_vote.return_value = poll
        mock_service.add_registrant = AsyncMock(return_value=poll)
        
        # For verify_poll_integrity testing
        verification_result = {
            "is_valid": True,
            "ppe_coverage": 0.75,
            "known_sybil_ids": [],
            "total_participants": 2,
            "total_votes": 1,
            "unauthorized_votes": [],
            "min_certifications_per_user": 0,
            "verification_message": "Poll verification successful. No issues detected."
        }
        mock_service.verify_poll_integrity.return_value = verification_result
        
        # For record_ppe_certification
        mock_service.record_ppe_certification.return_value = poll
        
        # Mock get_user_id
        with patch('app.routes.polls.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = "mocked-user-id"
            yield mock_service

def test_get_user_verifications(mock_poll_service):
    """Test getting verification status for a user"""
    # Create public key for testing
    public_key = {"key": "test-key"}
    public_key_str = json.dumps(public_key)
    
    # Configure poll with the mocked user
    poll = Poll(
        id="test-poll-id",
        question="Test Question",
        options=["Option 1", "Option 2"],
        registrants={"mocked-user-id": {"key": "test-key"}},
        votes={},
        verifications={"mocked-user-id": UserVerification(verified_by=set(), has_verified=set())},
        ppe_certifications={}
    )
    mock_poll_service.get_poll.return_value = poll
    
    # Make the request
    response = client.get(f"/polls/test-poll-id/verifications?public_key_str={public_key_str}")
    
    # Check the response
    assert response.status_code == 200
    assert "verified_by" in response.json()
    assert "has_verified" in response.json()
    assert "can_vote" in response.json()

def test_get_user_verifications_not_registered(mock_poll_service):
    """Test getting verification status for a user who is not registered"""
    # Configure mock to return a poll without the user
    poll = Poll(
        id="test-poll-id",
        question="Test Question",
        options=["Option 1", "Option 2"],
        registrants={},  # Empty registrants
        votes={},
        verifications={},
        ppe_certifications={}
    )
    mock_poll_service.get_poll.return_value = poll
    
    # Create public key for testing
    public_key = {"key": "test-key"}
    public_key_str = json.dumps(public_key)
    
    # Make the request
    response = client.get(f"/polls/test-poll-id/verifications?public_key_str={public_key_str}")
    
    # Check the response - should be 404
    assert response.status_code == 404
    assert "detail" in response.json()

def test_get_ppe_certifications(mock_poll_service):
    """Test getting PPE certifications for a user"""
    # Create public key for testing
    public_key = {"key": "test-key"}
    public_key_str = json.dumps(public_key)
    
    # Configure mock to return a poll with certifications
    poll = Poll(
        id="test-poll-id",
        question="Test Question",
        options=["Option 1", "Option 2"],
        registrants={"mocked-user-id": {"key": "test-key"}},
        votes={},
        verifications={},
        ppe_certifications={"mocked-user-id": {"other-user-1", "other-user-2"}}
    )
    mock_poll_service.get_poll.return_value = poll
    
    # Make the request
    response = client.get(f"/polls/test-poll-id/ppe-certifications?public_key_str={public_key_str}")
    
    # Check the response
    assert response.status_code == 200
    assert "certified_peers" in response.json()
    assert "certification_count" in response.json()
    assert response.json()["certification_count"] == 2

def test_get_ppe_certifications_not_registered(mock_poll_service):
    """Test getting PPE certifications for a user who is not registered"""
    # Configure mock to return a poll without the user
    poll = Poll(
        id="test-poll-id",
        question="Test Question",
        options=["Option 1", "Option 2"],
        registrants={},  # Empty registrants
        votes={},
        verifications={},
        ppe_certifications={}
    )
    mock_poll_service.get_poll.return_value = poll
    
    # Create public key for testing
    public_key = {"key": "test-key"}
    public_key_str = json.dumps(public_key)
    
    # Make the request
    response = client.get(f"/polls/test-poll-id/ppe-certifications?public_key_str={public_key_str}")
    
    # Check the response - should be 404
    assert response.status_code == 404
    assert "detail" in response.json()

def test_record_ppe_certification(mock_poll_service):
    """Test recording a PPE certification between two users"""
    # Create certification data
    certification_data = {
        "user1_public_key": {"key": "user1-key"},
        "user2_public_key": {"key": "user2-key"}
    }
    
    # Make the request
    response = client.post("/polls/test-poll-id/ppe-certification", json=certification_data)
    
    # Check the response
    assert response.status_code == 200
    assert "message" in response.json()
    assert "PPE certification recorded successfully" in response.json()["message"]
    
    # Check that the service was called with the correct parameters
    mock_poll_service.record_ppe_certification.assert_called_once_with(
        "test-poll-id", "mocked-user-id", "mocked-user-id"
    )

def test_record_ppe_certification_missing_field(mock_poll_service):
    """Test recording a PPE certification with missing fields"""
    # Create incomplete certification data
    certification_data = {
        "user1_public_key": {"key": "user1-key"}
        # missing user2_public_key
    }
    
    # Make the request
    response = client.post("/polls/test-poll-id/ppe-certification", json=certification_data)
    
    # Check the response - should be 400
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Missing required field" in response.json()["detail"]

def test_record_ppe_certification_poll_not_found(mock_poll_service):
    """Test recording a PPE certification for a non-existent poll"""
    # Configure mock to return None for the poll
    mock_poll_service.record_ppe_certification.return_value = None
    
    # Create certification data
    certification_data = {
        "user1_public_key": {"key": "user1-key"},
        "user2_public_key": {"key": "user2-key"}
    }
    
    # Make the request
    response = client.post("/polls/nonexistent-poll/ppe-certification", json=certification_data)
    
    # Check the response - should be 404
    assert response.status_code == 404
    assert "detail" in response.json()