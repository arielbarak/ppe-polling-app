"""
Tests for PPE utility functions.
"""

import pytest
from app.utils.ppe_utils import (
    generate_secret_key,
    generate_challenge_with_secret,
    verify_challenge_generation,
    create_commitment,
    verify_commitment,
    create_ppe_session_id,
    verify_solution_correctness
)


def test_generate_secret_key():
    """Test secret key generation."""
    secret1 = generate_secret_key()
    secret2 = generate_secret_key()
    
    assert secret1 != secret2
    assert len(secret1) > 0


def test_generate_challenge_deterministic():
    """Test that challenge generation is deterministic."""
    secret = generate_secret_key()
    session_id = "test_session"
    
    challenge1, solution1 = generate_challenge_with_secret(secret, session_id)
    challenge2, solution2 = generate_challenge_with_secret(secret, session_id)
    
    assert solution1 == solution2


def test_verify_challenge_generation():
    """Test challenge verification."""
    secret = generate_secret_key()
    session_id = "test_session"
    
    challenge, solution = generate_challenge_with_secret(secret, session_id)
    
    # Correct verification
    assert verify_challenge_generation(secret, session_id, challenge, solution)
    
    # Wrong solution
    assert not verify_challenge_generation(secret, session_id, challenge, "wrong")


def test_commitment_scheme():
    """Test commitment creation and verification."""
    solution = "test123"
    
    # Create commitment
    commitment, nonce = create_commitment(solution)
    
    # Verify with correct solution
    assert verify_commitment(solution, nonce, commitment)
    
    # Verify with wrong solution
    assert not verify_commitment("wrong", nonce, commitment)
    
    # Verify with wrong nonce
    assert not verify_commitment(solution, "wrong_nonce", commitment)


def test_create_ppe_session_id():
    """Test PPE session ID generation."""
    user1 = "user1"
    user2 = "user2"
    poll_id = "poll123"
    
    # Should be same regardless of order
    session1 = create_ppe_session_id(user1, user2, poll_id)
    session2 = create_ppe_session_id(user2, user1, poll_id)
    
    assert session1 == session2


def test_verify_solution_correctness():
    """Test solution verification."""
    challenge = "a b c 1 2 3"
    
    # Correct solution
    assert verify_solution_correctness(challenge, "abc123")
    assert verify_solution_correctness(challenge, "ABC123")  # Case insensitive
    assert verify_solution_correctness(challenge, " abc123 ")  # Strips spaces
    
    # Wrong solution
    assert not verify_solution_correctness(challenge, "wrong")