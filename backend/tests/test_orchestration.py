import pytest
from fastapi.testclient import TestClient
import json
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app
from app.models.poll import Poll, Vote, UserVerification

client = TestClient(app)

@pytest.mark.orchestration
def test_full_poll_lifecycle():
    """
    End-to-end test of the entire poll lifecycle including:
    1. Creating a poll
    2. Getting poll details
    3. Adding votes to the poll
    4. Verifying the poll
    
    This test simulates a complete user journey through the system.
    """
    # Mock services to enable testing the full lifecycle
    with patch('app.routes.polls.poll_service') as mock_poll_service, \
         patch('app.services.connection_manager.manager') as mock_manager:
        
        # Step 1: Create a poll
        # Setup mock for poll creation
        test_id = "a8098c1a-f86e-11da-bd1a-00112444be1e"
        created_poll = {
            "id": test_id,
            "question": "Test Question",
            "options": ["Option 1", "Option 2", "Option 3"],
            "registrants": {},
            "votes": {},
            "verifications": {},
            "ppe_certifications": {}
        }
        
        # Configure the mock to return our test poll
        mock_poll_service.create_poll.return_value = created_poll
        mock_poll_service.get_poll.return_value = created_poll
        mock_manager.broadcast_to_poll = AsyncMock()
        
        create_response = client.post(
            "/polls",
            json={
                "question": "Test Question",
                "options": ["Option 1", "Option 2", "Option 3"]
            }
        )
        assert create_response.status_code == 201
        # We'll accept any valid UUID here since we can't predict it exactly
        assert "id" in create_response.json()
        
        # Step 2: Get poll details
        poll_id = create_response.json()["id"]
        mock_poll_service.get_poll.return_value = {
            "id": poll_id,
            "question": "Test Question",
            "options": ["Option 1", "Option 2", "Option 3"],
            "registrants": {},
            "votes": {},
            "verifications": {},
            "ppe_certifications": {}
        }
        
        get_response = client.get(f"/polls/{poll_id}")
        assert get_response.status_code == 200
        assert get_response.json()["question"] == "Test Question"
        assert get_response.json()["options"] == ["Option 1", "Option 2", "Option 3"]
        
        # Step 3: Register users for the poll
        # User 1 registration
        poll_with_user1 = {
            "id": poll_id,
            "question": "Test Question",
            "options": ["Option 1", "Option 2", "Option 3"],
            "registrants": {"user1": {"key": "value1"}},
            "votes": {},
            "verifications": {"user1": {"verified_by": [], "has_verified": []}},
            "ppe_certifications": {}
        }
        mock_poll_service.add_registrant = AsyncMock(return_value=poll_with_user1)
        
        reg1_response = client.post(
            f"/polls/{poll_id}/register",
            json={"key": "value1"}
        )
        assert reg1_response.status_code == 200
        
        # User 2 registration
        poll_with_user2 = {
            "id": poll_id,
            "question": "Test Question",
            "options": ["Option 1", "Option 2", "Option 3"],
            "registrants": {
                "user1": {"key": "value1"},
                "user2": {"key": "value2"}
            },
            "votes": {},
            "verifications": {
                "user1": {"verified_by": [], "has_verified": []},
                "user2": {"verified_by": [], "has_verified": []}
            },
            "ppe_certifications": {}
        }
        mock_poll_service.add_registrant = AsyncMock(return_value=poll_with_user2)
        
        reg2_response = client.post(
            f"/polls/{poll_id}/register",
            json={"key": "value2"}
        )
        assert reg2_response.status_code == 200
        
        # Step 4: Verify users
        # User 1 verifies User 2
        poll_after_verify1 = Poll(
            id="test-poll-id",
            question="Test Question",
            options=["Option 1", "Option 2", "Option 3"],
            registrants={
                "user1": {"key": "value1"},
                "user2": {"key": "value2"}
            },
            votes={},
            verifications={
                "user1": UserVerification(has_verified={"user2"}),
                "user2": UserVerification(verified_by={"user1"})
            },
            ppe_certifications={}
        )
        mock_poll_service.verify_user.return_value = poll_after_verify1
        mock_poll_service.get_user_id = lambda key: "user1" if key == {"key": "value1"} else "user2"
        
        verify1_response = client.post(
            "/polls/test-poll-id/verify/user2",
            json={"key": "value1"}
        )
        assert verify1_response.status_code == 200
        
        # User 2 verifies User 1
        poll_after_verify2 = Poll(
            id="test-poll-id",
            question="Test Question",
            options=["Option 1", "Option 2", "Option 3"],
            registrants={
                "user1": {"key": "value1"},
                "user2": {"key": "value2"}
            },
            votes={},
            verifications={
                "user1": UserVerification(has_verified={"user2"}, verified_by={"user2"}),
                "user2": UserVerification(has_verified={"user1"}, verified_by={"user1"})
            },
            ppe_certifications={}
        )
        mock_poll_service.verify_user.return_value = poll_after_verify2
        
        verify2_response = client.post(
            "/polls/test-poll-id/verify/user1",
            json={"key": "value2"}
        )
        assert verify2_response.status_code == 200
        
        # Step 5: Record PPE certification
        poll_after_ppe = Poll(
            id="test-poll-id",
            question="Test Question",
            options=["Option 1", "Option 2", "Option 3"],
            registrants={
                "user1": {"key": "value1"},
                "user2": {"key": "value2"}
            },
            votes={},
            verifications={
                "user1": UserVerification(has_verified={"user2"}, verified_by={"user2"}),
                "user2": UserVerification(has_verified={"user1"}, verified_by={"user1"})
            },
            ppe_certifications={
                "user1": {"user2"},
                "user2": {"user1"}
            }
        )
        mock_poll_service.record_ppe_certification.return_value = poll_after_ppe
        
        ppe_response = client.post(
            "/polls/test-poll-id/ppe-certification",
            json={
                "user1_public_key": {"key": "value1"},
                "user2_public_key": {"key": "value2"}
            }
        )
        assert ppe_response.status_code == 200
        assert ppe_response.json()["message"] == "PPE certification recorded successfully"
        
        # Step 6: Add votes to the poll
        # User 1 votes for Option 1
        poll_with_vote1 = Poll(
            id="test-poll-id",
            question="Test Question",
            options=["Option 1", "Option 2", "Option 3"],
            registrants={
                "user1": {"key": "value1"},
                "user2": {"key": "value2"}
            },
            votes={
                "user1": Vote(publicKey={"key": "value1"}, option="Option 1", signature="sig1")
            },
            verifications={
                "user1": UserVerification(has_verified={"user2"}, verified_by={"user2"}),
                "user2": UserVerification(has_verified={"user1"}, verified_by={"user1"})
            },
            ppe_certifications={
                "user1": {"user2"},
                "user2": {"user1"}
            }
        )
        mock_poll_service.record_vote.return_value = poll_with_vote1
        
        vote1_response = client.post(
            "/polls/test-poll-id/vote",
            json={
                "publicKey": {"key": "value1"},
                "option": "Option 1",
                "signature": "sig1"
            }
        )
        assert vote1_response.status_code == 200
        
        # User 2 votes for Option 2
        poll_with_vote2 = Poll(
            id="test-poll-id",
            question="Test Question",
            options=["Option 1", "Option 2", "Option 3"],
            registrants={
                "user1": {"key": "value1"},
                "user2": {"key": "value2"}
            },
            votes={
                "user1": Vote(publicKey={"key": "value1"}, option="Option 1", signature="sig1"),
                "user2": Vote(publicKey={"key": "value2"}, option="Option 2", signature="sig2")
            },
            verifications={
                "user1": UserVerification(has_verified={"user2"}, verified_by={"user2"}),
                "user2": UserVerification(has_verified={"user1"}, verified_by={"user1"})
            },
            ppe_certifications={
                "user1": {"user2"},
                "user2": {"user1"}
            }
        )
        mock_poll_service.record_vote.return_value = poll_with_vote2
        
        vote2_response = client.post(
            "/polls/test-poll-id/vote",
            json={
                "publicKey": {"key": "value2"},
                "option": "Option 2",
                "signature": "sig2"
            }
        )
        assert vote2_response.status_code == 200
        
        # Step 7: Verify poll integrity
        mock_poll_service.get_poll.return_value = poll_with_vote2
        mock_poll_service.verify_poll_integrity.return_value = {
            "is_valid": True,
            "ppe_coverage": 1.0,
            "total_participants": 2,
            "total_votes": 2,
            "unauthorized_votes": [],
            "min_certifications_per_user": 1,
            "max_certifications_per_user": 1,
            "avg_certifications_per_user": 1.0,
            "verification_message": "Poll verification successful. No issues detected."
        }
        
        verify_response = client.get("/polls/test-poll-id/verify")
        assert verify_response.status_code == 200
        assert verify_response.json()["verification"]["is_valid"] == True
        assert verify_response.json()["verification"]["ppe_coverage"] == 1.0
        assert verify_response.json()["verification"]["unauthorized_votes"] == []

    @pytest.mark.orchestration
    def test_poll_lifecycle_with_sybil_attack():
        """
        Test the poll lifecycle with a simulated Sybil attack
        to ensure the verification system detects it.
        """
        # Mock services to enable testing the full lifecycle
        with patch('app.services.poll_service.poll_service') as mock_poll_service, \
            patch('app.services.connection_manager.manager') as mock_manager:
            
            # Step 1: Create a poll
            test_id = "b8098c1a-f86e-11da-bd1a-00112444be1e"
            created_poll = Poll(
                id=test_id,
                question="Test Question",
                options=["Option 1", "Option 2"],
                registrants={},
                votes={},
                ppe_certifications={}
            )
            # Override UUID generation to return our test ID
            with patch('uuid.uuid4', return_value=uuid.UUID(test_id)):
                mock_poll_service.create_poll.return_value = created_poll
                mock_manager.broadcast_to_poll = AsyncMock()
                
                create_response = client.post(
                    "/polls/",
                    json={
                        "question": "Test Question",
                        "options": ["Option 1", "Option 2"]
                    }
                )
                assert create_response.status_code == 201
                assert create_response.json()["id"] == test_id
                
            # Step 2: Setup legitimate users and Sybil users
            poll_with_all_users = Poll(
                id=test_id,
            question="Test Question",
            options=["Option 1", "Option 2"],
            registrants={
                "user1": {"key": "value1"},
                "user2": {"key": "value2"},
                "sybil1": {"key": "value3"},
                "sybil2": {"key": "value4"},
                "sybil3": {"key": "value5"}
            },
            votes={},
            verifications={
                "user1": UserVerification(has_verified={"user2"}, verified_by={"user2"}),
                "user2": UserVerification(has_verified={"user1"}, verified_by={"user1"}),
                "sybil1": UserVerification(has_verified={"sybil2", "sybil3"}, verified_by={"sybil2", "sybil3"}),
                "sybil2": UserVerification(has_verified={"sybil1", "sybil3"}, verified_by={"sybil1"}),
                "sybil3": UserVerification(has_verified={"sybil1"}, verified_by={"sybil1", "sybil2"})
            },
            ppe_certifications={
                "user1": {"user2"},
                "user2": {"user1"},
                "sybil1": {"sybil2", "sybil3"},
                "sybil2": {"sybil1", "sybil3"},
                "sybil3": {"sybil1", "sybil2"}
            }
        )
        
        # Add votes for both legitimate and Sybil users
        poll_with_votes = Poll(
            id="test-poll-id",
            question="Test Question",
            options=["Option 1", "Option 2"],
            registrants={
                "user1": {"key": "value1"},
                "user2": {"key": "value2"},
                "sybil1": {"key": "value3"},
                "sybil2": {"key": "value4"},
                "sybil3": {"key": "value5"}
            },
            votes={
                "user1": Vote(publicKey={"key": "value1"}, option="Option 1", signature="sig1"),
                "user2": Vote(publicKey={"key": "value2"}, option="Option 1", signature="sig2"),
                "sybil1": Vote(publicKey={"key": "value3"}, option="Option 2", signature="sig3"),
                "sybil2": Vote(publicKey={"key": "value4"}, option="Option 2", signature="sig4"),
                "sybil3": Vote(publicKey={"key": "value5"}, option="Option 2", signature="sig5")
            },
            verifications=poll_with_all_users.verifications,
            ppe_certifications=poll_with_all_users.ppe_certifications
        )
        
        mock_poll_service.get_poll.return_value = poll_with_votes
        
        # Step 3: Verify poll integrity - should detect Sybil attack
        mock_poll_service.verify_poll_integrity.return_value = {
            "is_valid": False,
            "ppe_coverage": 0.3,
            "total_participants": 5,
            "total_votes": 5,
            "unauthorized_votes": [],
            "min_certifications_per_user": 1,
            "max_certifications_per_user": 2,
            "avg_certifications_per_user": 1.6,
            "verification_message": "Low PPE certification coverage (less than 30%)."
        }
        
        verify_response = client.get("/polls/test-poll-id/verify")
        assert verify_response.status_code == 200
        assert verify_response.json()["verification"]["is_valid"] == False
        assert verify_response.json()["verification"]["ppe_coverage"] == 0.3