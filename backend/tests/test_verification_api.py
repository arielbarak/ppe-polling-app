import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.models.poll import Poll, UserVerification
from app.services.poll_service import poll_service, _polls_db

client = TestClient(app)

@pytest.fixture
def setup_test_poll():
    """Fixture that creates a test poll and adds it to the database for API testing"""
    # Clear existing polls
    _polls_db.clear()
    
    # Create a sample poll
    poll = Poll(
        id="test-poll-id",
        question="Test Question",
        options=["Option 1", "Option 2", "Option 3"]
    )
    
    # Add test users with mock public keys
    test_users = {
        "user1": {"key": "value1"},
        "user2": {"key": "value2"},
        "user3": {"key": "value3"},
        "user4": {"key": "value4"},
    }
    
    poll.registrants = test_users
    
    # Add verifications - make sure each user has at least 2
    poll.verifications = {
        "user1": UserVerification(verified_by={"user2", "user3"}, has_verified={"user2"}),
        "user2": UserVerification(verified_by={"user1", "user3"}, has_verified={"user1"}),
        "user3": UserVerification(verified_by={"user1", "user2"}, has_verified={"user1", "user2"}),
        "user4": UserVerification(verified_by={"user1", "user2"}, has_verified=set()),
    }
    
    # Add PPE certifications
    poll.ppe_certifications = {
        "user1": {"user2", "user3"},
        "user2": {"user1", "user3"},
        "user3": {"user1", "user2"},
        "user4": {"user1", "user2"},  # Add enough certifications for user4
    }
    
    # Add votes for users with sufficient verifications
    poll.votes = {
        "user1": {"option": "Option 1"},
        "user2": {"option": "Option 2"},
        "user3": {"option": "Option 3"},
    }
    
    # Add to mock database
    _polls_db[poll.id] = poll
    
    return poll

class TestVerificationAPI:
    """Integration tests for the verification API endpoint"""
    
    def test_get_poll_verification_data(self, setup_test_poll):
        """Test the GET /polls/{poll_id}/verify endpoint"""
        poll = setup_test_poll
        response = client.get(f"/polls/{poll.id}/verify")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["poll_id"] == poll.id
        assert data["question"] == poll.question
        assert data["options"] == poll.options
        assert data["total_participants"] == len(poll.registrants)
        assert data["total_votes"] == len(poll.votes)
        assert "certification_graph" in data
        assert "verification" in data
        
        # Check certification graph structure
        graph = data["certification_graph"]
        assert "nodes" in graph
        assert "edges" in graph
        
        # Check nodes
        assert len(graph["nodes"]) == len(poll.registrants)
        for node in graph["nodes"]:
            assert "id" in node
            assert "voted" in node
            if node["voted"]:
                assert "vote" in node
            assert "publicKey" in node
        
        # Check edges
        for edge in graph["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "type" in edge
            assert edge["type"] in ["ppe_certification", "verification"]
        
        # Check verification data
        verification = data["verification"]
        assert verification["total_participants"] == len(poll.registrants)
        assert verification["total_votes"] == len(poll.votes)
        assert verification["is_valid"] == True
    
    def test_get_poll_verification_data_nonexistent_poll(self):
        """Test the verification endpoint with a non-existent poll ID"""
        response = client.get("/polls/non-existent-id/verify")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Poll not found"
    
    def test_get_poll_verification_data_with_unauthorized_votes(self, setup_test_poll):
        """Test the verification endpoint with unauthorized votes"""
        poll = setup_test_poll
        
        # Remove verifications to make user4 unauthorized
        poll.verifications["user4"] = UserVerification(verified_by={"user1"}, has_verified=set())
        
        # Add a vote from user4 who doesn't have enough verifications
        poll.votes["user4"] = {"option": "Option 1"}
        
        response = client.get(f"/polls/{poll.id}/verify")
        
        assert response.status_code == 200
        data = response.json()
        
        verification = data["verification"]
        assert "user4" in verification["unauthorized_votes"]
        assert verification["is_valid"] == False