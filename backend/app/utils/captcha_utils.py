"""
CAPTCHA generation and validation utilities for one-sided PPE.

This implements a simple text-based CAPTCHA for registration.
More sophisticated CAPTCHAs can be added later.
"""

import random
import string
import hashlib
import time
from typing import Tuple, Dict, Optional
from datetime import datetime, timedelta


class CaptchaChallenge:
    """
    Represents a CAPTCHA challenge with associated metadata.
    """
    def __init__(self, challenge_id: str, challenge_text: str, solution_hash: str, 
                 expires_at: datetime):
        self.challenge_id = challenge_id
        self.challenge_text = challenge_text
        self.solution_hash = solution_hash
        self.expires_at = expires_at
        self.created_at = datetime.now()
    
    def is_expired(self) -> bool:
        """Check if challenge has expired."""
        return datetime.now() > self.expires_at
    
    def verify_solution(self, solution: str) -> bool:
        """Verify if provided solution matches the challenge."""
        if self.is_expired():
            return False
        solution_hash = hashlib.sha256(solution.strip().lower().encode()).hexdigest()
        return solution_hash == self.solution_hash


def generate_random_string(length: int = 6, 
                           include_digits: bool = True,
                           include_uppercase: bool = True) -> str:
    """
    Generate a random string for CAPTCHA.
    
    Args:
        length: Length of string to generate
        include_digits: Include numbers in the string
        include_uppercase: Include uppercase letters
        
    Returns:
        Random string
    """
    chars = string.ascii_lowercase
    if include_uppercase:
        chars += string.ascii_uppercase
    if include_digits:
        chars += string.digits
    
    # Avoid confusing characters
    confusing_chars = 'Il1O0'
    chars = ''.join(c for c in chars if c not in confusing_chars)
    
    return ''.join(random.choice(chars) for _ in range(length))


def generate_text_captcha(difficulty: str = "medium") -> Tuple[str, str]:
    """
    Generate a simple text-based CAPTCHA.
    
    Args:
        difficulty: "easy", "medium", or "hard"
        
    Returns:
        Tuple of (challenge_text, solution)
    """
    difficulty_settings = {
        "easy": {"length": 4, "uppercase": False, "digits": False},
        "medium": {"length": 6, "uppercase": True, "digits": True},
        "hard": {"length": 8, "uppercase": True, "digits": True}
    }
    
    settings = difficulty_settings.get(difficulty, difficulty_settings["medium"])
    
    solution = generate_random_string(
        length=settings["length"],
        include_uppercase=settings["uppercase"],
        include_digits=settings["digits"]
    )
    
    # Create visual representation with some distortion
    challenge_text = _add_visual_noise(solution)
    
    return challenge_text, solution


def _add_visual_noise(text: str) -> str:
    """
    Add visual noise to text to make it slightly harder to read programmatically.
    
    This version adds consistent spacing between ALL characters for visual clarity.
    Users should type without spaces - instructions will clarify this.
    
    Args:
        text: Original text
        
    Returns:
        Text with consistent visual spacing
    """
    # Add consistent spacing between ALL characters for visual clarity
    # Users should type without spaces
    chars = list(text)
    return ' '.join(chars)


def generate_challenge_id() -> str:
    """
    Generate a unique challenge ID.
    
    Returns:
        Unique challenge identifier
    """
    timestamp = str(time.time())
    random_str = generate_random_string(16)
    combined = f"{timestamp}{random_str}"
    return hashlib.sha256(combined.encode()).hexdigest()


def create_registration_challenge(difficulty: str = "medium",
                                  validity_minutes: int = 5) -> CaptchaChallenge:
    """
    Create a CAPTCHA challenge for registration.
    
    Args:
        difficulty: Challenge difficulty level
        validity_minutes: How long the challenge is valid for
        
    Returns:
        CaptchaChallenge object
    """
    challenge_id = generate_challenge_id()
    challenge_text, solution = generate_text_captcha(difficulty)
    
    # Hash the solution (case-insensitive)
    solution_hash = hashlib.sha256(solution.lower().encode()).hexdigest()
    
    # Set expiration
    expires_at = datetime.now() + timedelta(minutes=validity_minutes)
    
    return CaptchaChallenge(
        challenge_id=challenge_id,
        challenge_text=challenge_text,
        solution_hash=solution_hash,
        expires_at=expires_at
    )


def verify_challenge_solution(challenge: CaptchaChallenge, solution: str) -> bool:
    """
    Verify a challenge solution.
    
    Args:
        challenge: The CaptchaChallenge object
        solution: User's solution attempt
        
    Returns:
        True if solution is correct and challenge not expired
    """
    return challenge.verify_solution(solution)


# Challenge storage for the registration process
# In production, this should be in Redis or similar
_active_challenges: Dict[str, CaptchaChallenge] = {}


def store_challenge(challenge: CaptchaChallenge):
    """Store a challenge in the active challenges dict."""
    _active_challenges[challenge.challenge_id] = challenge
    
    # Clean up expired challenges
    _cleanup_expired_challenges()


def get_challenge(challenge_id: str) -> Optional[CaptchaChallenge]:
    """Retrieve a challenge by ID."""
    return _active_challenges.get(challenge_id)


def remove_challenge(challenge_id: str):
    """Remove a challenge after it's been used."""
    if challenge_id in _active_challenges:
        del _active_challenges[challenge_id]


def _cleanup_expired_challenges():
    """Remove expired challenges from storage."""
    expired_ids = [
        cid for cid, challenge in _active_challenges.items()
        if challenge.is_expired()
    ]
    for cid in expired_ids:
        del _active_challenges[cid]