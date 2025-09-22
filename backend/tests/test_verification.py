import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.models.poll import Poll, UserVerification
from app.services.poll_service import poll_service

client = TestClient(app)

@pytest.fixture
def sample_poll_data():
    """Fixture that returns sample poll data for testing"""
    return {
        "question": "Test Question",
        "options": ["Option 1", "Option 2", "Option 3"]
    }

@pytest.fixture
def sample_poll_with_users():
    """
    Fixture that creates a sample poll with several users,
    PPE certifications, and votes for testing verification
    """
    poll = Poll(
        question="Test Question",
        options=["Option 1", "Option 2", "Option 3"]
    )
    
    # Add test users with mock public keys
    test_users = {
        "user1": {"key": "value1"},
        "user2": {"key": "value2"},
        "user3": {"key": "value3"},
        "user4": {"key": "value4"},
        "user5": {"key": "value5"},
    }
    
    poll.registrants = test_users
    
    # Add verifications
    poll.verifications = {
        "user1": UserVerification(verified_by={"user2", "user3"}, has_verified={"user2", "user4"}),
        "user2": UserVerification(verified_by={"user1", "user3"}, has_verified={"user1", "user3"}),
        "user3": UserVerification(verified_by={"user2", "user4"}, has_verified={"user1", "user2"}),
        "user4": UserVerification(verified_by={"user1", "user5"}, has_verified={"user3", "user5"}),
        "user5": UserVerification(verified_by={"user4"}, has_verified={"user4"}),
    }
    
    # Add more certifications for user5 to pass validation
    poll.ppe_certifications = {
        "user1": {"user2", "user3"},
        "user2": {"user1", "user3"},
        "user3": {"user1", "user2", "user4"},
        "user4": {"user3", "user5"},
        "user5": {"user4", "user1", "user2"}, # Add more certifications
    }
    
    # Add votes for users with sufficient verifications
    poll.votes = {
        "user1": {"option": "Option 1"},
        "user2": {"option": "Option 2"},
        "user3": {"option": "Option 3"},
        "user4": {"option": "Option 1"},
    }
    
    return poll

class TestVerificationFunctionality:
    """Tests for the poll verification functionality"""
    
    def test_verify_poll_integrity(self, sample_poll_with_users):
        """Test the poll_service.verify_poll_integrity method"""
        poll = sample_poll_with_users
        
        # Run the verification
        verification_result = poll_service.verify_poll_integrity(poll)
        
        # Check the verification result contains expected fields
        assert "total_participants" in verification_result
        assert "total_votes" in verification_result
        assert "ppe_coverage" in verification_result
        assert "min_certifications_per_user" in verification_result
        assert "avg_certifications_per_user" in verification_result
        assert "unauthorized_votes" in verification_result
        assert "is_valid" in verification_result
        assert "verification_message" in verification_result
        
        # Check the specific values
        assert verification_result["total_participants"] == 5
        assert verification_result["total_votes"] == 4
        assert verification_result["unauthorized_votes"] == []
        # In our sample poll, all users have at least 2 certifications
        assert verification_result["min_certifications_per_user"] >= 2
        assert verification_result["is_valid"] == True
    
    def test_verify_poll_integrity_with_no_participants(self):
        """Test verification with an empty poll"""
        empty_poll = Poll(
            question="Empty Poll",
            options=["Option 1", "Option 2"]
        )
        
        verification_result = poll_service.verify_poll_integrity(empty_poll)
        
        assert verification_result["total_participants"] == 0
        assert verification_result["total_votes"] == 0
        assert verification_result["is_valid"] == True  # An empty poll is technically valid
        assert "Poll has no participants" in verification_result["verification_message"]
    
    def test_verify_poll_integrity_with_unauthorized_votes(self, sample_poll_with_users):
        """Test verification with unauthorized votes"""
        poll = sample_poll_with_users
        
        # Add a vote from user5 who doesn't have enough verifications
        poll.votes["user5"] = {"option": "Option 1"}
        
        verification_result = poll_service.verify_poll_integrity(poll)
        
        assert "user5" in verification_result["unauthorized_votes"]
        assert verification_result["is_valid"] == False
        assert "unauthorized votes" in verification_result["verification_message"].lower()
    
    def test_verify_poll_integrity_with_insufficient_certifications(self, sample_poll_with_users):
        """Test verification with insufficient certifications"""
        poll = sample_poll_with_users
        
        # Remove certifications to make a user have less than 2
        poll.ppe_certifications["user5"] = set()
        poll.ppe_certifications["user4"].remove("user5")
        
        verification_result = poll_service.verify_poll_integrity(poll)
        
        assert verification_result["min_certifications_per_user"] == 0
        assert verification_result["is_valid"] == False
        assert "fewer than 2 PPE certifications" in verification_result["verification_message"]
    
    def test_generate_verification_message(self):
        """Test the _generate_verification_message method"""
        # Test successful verification message
        message = poll_service._generate_verification_message(10, 0.5, 2, [])
        assert "Poll verification successful" in message
        
        # Test low PPE coverage
        message = poll_service._generate_verification_message(10, 0.2, 2, [])
        assert "Low PPE certification coverage" in message
        
        # Test very low PPE coverage
        message = poll_service._generate_verification_message(10, 0.05, 2, [])
        assert "WARNING: Very low PPE certification coverage" in message
        
        # Test insufficient certifications
        message = poll_service._generate_verification_message(10, 0.5, 1, [])
        assert "WARNING: Some users have fewer than 2 PPE certifications" in message
        
        # Test unauthorized votes
        message = poll_service._generate_verification_message(10, 0.5, 2, ["user1"])
        assert "WARNING: 1 unauthorized votes" in message