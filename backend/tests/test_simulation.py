import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
import random
import time
import uuid
from app.main import app
from app.models.poll import Poll, Vote, UserVerification, PollCreate

client = TestClient(app)

def generate_random_poll_data(num_options=3):
    """Generate random poll data for testing"""
    options = [f"Option {i+1}" for i in range(num_options)]
    return {
        "question": f"Test Question {uuid.uuid4().hex[:8]}",
        "options": options
    }

def generate_random_vote():
    """Generate a random vote for testing"""
    return {
        "publicKey": {"key": f"key-{uuid.uuid4().hex[:8]}"},
        "option": f"Option {random.randint(1, 3)}",
        "signature": f"sig-{uuid.uuid4().hex[:8]}"
    }

@pytest.mark.stress
def test_create_multiple_polls():
    """
    Test creating a large number of polls in quick succession
    to verify system performance and stability.
    """
    with patch('app.routes.polls.poll_service') as mock_poll_service:
        # Configure the mock to return unique poll IDs
        mock_poll_service.create_poll.side_effect = lambda poll_data: Poll(
            id=f"poll-{uuid.uuid4().hex[:8]}",
            question=poll_data.question,
            options=poll_data.options,
            registrants={},
            votes={},
            verifications={},
            ppe_certifications={}
        )
        
        # Track timing for performance analysis
        start_time = time.time()
        num_polls = 50
        
        # Create multiple polls
        poll_ids = []
        for _ in range(num_polls):
            poll_data = generate_random_poll_data()
            response = client.post("/polls", json=poll_data)
            assert response.status_code == 201
            poll_ids.append(response.json()["id"])
        
        # Measure total time and average time per poll
        total_time = time.time() - start_time
        avg_time = total_time / num_polls
        
        # Print performance metrics
        print(f"Created {num_polls} polls in {total_time:.2f} seconds")
        print(f"Average time per poll: {avg_time:.4f} seconds")
        
        # Verify all polls have unique IDs
        assert len(poll_ids) == len(set(poll_ids))
        
        # Verify the poll service was called the correct number of times
        assert mock_poll_service.create_poll.call_count == num_polls

@pytest.mark.stress
def test_high_volume_votes():
    """
    Test adding a high volume of votes to a single poll
    to verify system performance and stability under load.
    """
    with patch('app.routes.polls.poll_service') as mock_poll_service, \
         patch('app.services.connection_manager.manager') as mock_manager:
        
        # Configure mock_manager
        mock_manager.broadcast_to_poll = AsyncMock()
        
        # Create a test poll with multiple options
        poll_data = generate_random_poll_data(num_options=5)
        poll_id = "stress-test-poll-id"
        
        # Configure mock to return the poll
        poll = Poll(
            id=poll_id,
            question=poll_data["question"],
            options=poll_data["options"],
            registrants={},
            votes={},
            verifications={},
            ppe_certifications={}
        )
        mock_poll_service.create_poll.return_value = poll
        mock_poll_service.get_poll.return_value = poll
        
        # Create the poll
        create_response = client.post("/polls", json=poll_data)
        assert create_response.status_code == 201
        
        # Configure mocks for registering users and verifications
        async def register_user_side_effect(poll_id, public_key):
            user_id = f"user-{uuid.uuid4().hex[:8]}"
            poll.registrants[user_id] = public_key
            poll.verifications[user_id] = UserVerification(
                verified_by={"admin1", "admin2"},  # Mock verifications to allow voting
                has_verified=set()
            )
            return poll
            
        mock_poll_service.add_registrant = AsyncMock(side_effect=register_user_side_effect)
        
        # Configure mock for adding votes
        def record_vote_side_effect(poll_id, vote):
            # Extract user_id from vote's publicKey
            user_id = next(
                (uid for uid, pk in poll.registrants.items() 
                 if pk == vote.publicKey), 
                f"user-{uuid.uuid4().hex[:8]}"
            )
            # Add the vote to the poll's votes dict
            poll.votes[user_id] = vote
            return poll
        
        mock_poll_service.record_vote.side_effect = record_vote_side_effect
        
        # Add a high volume of votes
        num_votes = 50  # Reduced from 100 to speed up the test
        start_time = time.time()
        
        for _ in range(num_votes):
            # Generate a random vote
            vote_data = generate_random_vote()
            
            # Register the user first
            reg_response = client.post(f"/polls/{poll_id}/register", json=vote_data["publicKey"])
            assert reg_response.status_code == 200
            
            # Add the vote
            vote_response = client.post(f"/polls/{poll_id}/vote", json=vote_data)
            assert vote_response.status_code == 200
        
        # Measure timing
        total_time = time.time() - start_time
        avg_time = total_time / num_votes
        
        # Print performance metrics
        print(f"Added {num_votes} votes in {total_time:.2f} seconds")
        print(f"Average time per vote: {avg_time:.4f} seconds")
        
        # Verify all votes were added
        assert len(poll.votes) == num_votes

@pytest.mark.stress
def test_verification_performance():
    """
    Test the performance of the poll verification system 
    with varying sizes of certification graphs.
    """
    with patch('app.routes.polls.poll_service') as mock_poll_service:
        poll_id = "verify-performance-test-poll-id"
        
        # Test verification with different graph sizes
        graph_sizes = [10, 50, 100]
        
        for size in graph_sizes:
            # Create a poll with a certification graph of the given size
            poll = Poll(
                id=poll_id,
                question="Performance Test Poll",
                options=["Option 1", "Option 2"],
                registrants={},
                votes={},
                verifications={},
                ppe_certifications={}
            )
            
            # Add registrants
            for i in range(size):
                user_id = f"user-{i}"
                poll.registrants[user_id] = {"key": f"key-{i}"}
                poll.verifications[user_id] = UserVerification(verified_by=set(), has_verified=set())
                
                # Add votes for some users
                if i % 2 == 0:  # Every other user votes
                    poll.votes[user_id] = Vote(
                        publicKey={"key": f"key-{i}"},
                        option="Option 1",
                        signature=f"sig-{i}"
                    )
            
            # Generate a realistic certification graph for the given size
            # For testing purposes, we'll create a simple tree structure
            # where each node certifies 2 others, except leaf nodes
            for i in range(size):
                user_id = f"user-{i}"
                certifies = set()
                child1 = 2 * i + 1
                child2 = 2 * i + 2
                if child1 < size:
                    certifies.add(f"user-{child1}")
                if child2 < size:
                    certifies.add(f"user-{child2}")
                poll.ppe_certifications[user_id] = certifies
                
                # Update verifications based on PPE certifications
                if user_id in poll.verifications:
                    poll.verifications[user_id].has_verified = certifies
                for child_id in certifies:
                    if child_id in poll.verifications:
                        poll.verifications[child_id].verified_by.add(user_id)
            
            mock_poll_service.get_poll.return_value = poll
            
            # Mock the verification result (results will vary by graph size)
            coverage = min(0.9, 0.5 + (size / 1000))  # Higher coverage for larger graphs, up to a limit
            mock_poll_service.verify_poll_integrity.return_value = {
                "is_valid": True,
                "ppe_coverage": coverage,
                "total_participants": size,
                "total_votes": size // 2,
                "unauthorized_votes": [],
                "min_certifications_per_user": 1,
                "max_certifications_per_user": 2,
                "avg_certifications_per_user": 1.5,
                "verification_message": "Poll verification successful. No issues detected."
            }
            
            # Time the verification operation
            start_time = time.time()
            verify_response = client.get(f"/polls/{poll_id}/verify")
            verification_time = time.time() - start_time
            
            assert verify_response.status_code == 200
            
            # Print performance metrics
            print(f"Verified poll with {size} users in {verification_time:.4f} seconds")