"""
Tests for CAPTCHA utility functions.
"""

import pytest
import time
from datetime import datetime, timedelta
from app.utils.captcha_utils import (
    generate_random_string,
    generate_text_captcha,
    generate_challenge_id,
    create_registration_challenge,
    verify_challenge_solution,
    store_challenge,
    get_challenge,
    remove_challenge,
    CaptchaChallenge
)


def test_generate_random_string():
    """Test random string generation."""
    # Basic generation
    s = generate_random_string(length=6)
    assert len(s) == 6
    
    # No confusing characters
    confusing = 'Il1O0'
    assert all(c not in confusing for c in s)


def test_generate_random_string_options():
    """Test random string with different options."""
    # Only lowercase
    s = generate_random_string(length=10, include_digits=False, include_uppercase=False)
    assert len(s) == 10
    assert s.islower()
    assert not any(c.isdigit() for c in s)


def test_generate_text_captcha():
    """Test CAPTCHA generation."""
    challenge_text, solution = generate_text_captcha("easy")
    
    assert solution is not None
    assert len(solution) >= 4
    assert challenge_text is not None


def test_generate_text_captcha_difficulties():
    """Test different difficulty levels."""
    easy_text, easy_sol = generate_text_captcha("easy")
    medium_text, medium_sol = generate_text_captcha("medium")
    hard_text, hard_sol = generate_text_captcha("hard")
    
    assert len(easy_sol) == 4
    assert len(medium_sol) == 6
    assert len(hard_sol) == 8


def test_generate_challenge_id():
    """Test challenge ID generation."""
    id1 = generate_challenge_id()
    time.sleep(0.01)
    id2 = generate_challenge_id()
    
    # Should be unique
    assert id1 != id2
    assert len(id1) == 64  # SHA256 hex


def test_create_registration_challenge():
    """Test challenge creation."""
    challenge = create_registration_challenge("medium", validity_minutes=5)
    
    assert challenge.challenge_id is not None
    assert challenge.challenge_text is not None
    assert challenge.solution_hash is not None
    assert challenge.expires_at > datetime.now()
    assert not challenge.is_expired()


def test_challenge_expiration():
    """Test challenge expiration."""
    # Create challenge with very short validity
    challenge = create_registration_challenge("easy", validity_minutes=0)
    
    # Should be expired immediately (or very soon)
    time.sleep(0.1)
    # Manually set expiration to past
    challenge.expires_at = datetime.now() - timedelta(minutes=1)
    assert challenge.is_expired()


def test_verify_challenge_solution():
    """Test solution verification."""
    challenge = create_registration_challenge("medium")
    
    # Get the actual solution by regenerating with same pattern
    # (In real use, solution is never exposed)
    # For testing, we'll manually create a challenge with known solution
    from app.utils.captcha_utils import CaptchaChallenge
    import hashlib
    
    known_solution = "test123"
    solution_hash = hashlib.sha256(known_solution.lower().encode()).hexdigest()
    
    test_challenge = CaptchaChallenge(
        challenge_id="test_id",
        challenge_text="t e s t 1 2 3",
        solution_hash=solution_hash,
        expires_at=datetime.now() + timedelta(minutes=5)
    )
    
    # Correct solution
    assert verify_challenge_solution(test_challenge, "test123")
    assert verify_challenge_solution(test_challenge, "TEST123")  # Case insensitive
    
    # Wrong solution
    assert not verify_challenge_solution(test_challenge, "wrong")


def test_challenge_storage():
    """Test challenge storage and retrieval."""
    challenge = create_registration_challenge("medium")
    
    # Store
    store_challenge(challenge)
    
    # Retrieve
    retrieved = get_challenge(challenge.challenge_id)
    assert retrieved is not None
    assert retrieved.challenge_id == challenge.challenge_id
    
    # Remove
    remove_challenge(challenge.challenge_id)
    assert get_challenge(challenge.challenge_id) is None


def test_challenge_single_use():
    """Test that challenges are single-use."""
    from app.utils.captcha_utils import CaptchaChallenge
    import hashlib
    
    solution = "test123"
    solution_hash = hashlib.sha256(solution.lower().encode()).hexdigest()
    
    challenge = CaptchaChallenge(
        challenge_id="test_single_use",
        challenge_text="test",
        solution_hash=solution_hash,
        expires_at=datetime.now() + timedelta(minutes=5)
    )
    
    store_challenge(challenge)
    
    # First verification
    from app.services.registration_service import registration_service
    result1 = registration_service.validate_challenge(challenge.challenge_id, solution)
    assert result1 is True
    
    # Second verification should fail (challenge removed)
    result2 = registration_service.validate_challenge(challenge.challenge_id, solution)
    assert result2 is False