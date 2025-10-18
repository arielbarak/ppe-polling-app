"""
Utilities for Proof of Private Effort (PPE) protocol.

Implements the cryptographic primitives needed for the symmetric CAPTCHA PPE:
- Commitment scheme (hash-based)
- Challenge generation with secrets
- Challenge verification
"""

import hashlib
import secrets
import base64
from typing import Tuple, Optional
import json


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a random secret key for challenge generation.
    
    Args:
        length: Length in bytes (default 32 = 256 bits)
        
    Returns:
        Base64-encoded secret key
    """
    secret_bytes = secrets.token_bytes(length)
    return base64.b64encode(secret_bytes).decode('utf-8')


def generate_challenge_with_secret(secret: str, session_id: str, difficulty: str = "medium") -> Tuple[str, str]:
    """
    Generate a CAPTCHA challenge deterministically from a secret.
    
    This allows the peer to later verify that the challenge was generated
    correctly for this specific session.
    
    Args:
        secret: Base64-encoded secret key
        session_id: Unique identifier for this PPE session
        difficulty: Challenge difficulty
        
    Returns:
        Tuple of (challenge_text, solution)
    """
    from .captcha_utils import generate_random_string
    
    # Create deterministic seed from secret + session_id
    seed_input = f"{secret}:{session_id}".encode('utf-8')
    seed_hash = hashlib.sha256(seed_input).digest()
    seed = int.from_bytes(seed_hash[:8], byteorder='big')
    
    # Use seed to generate deterministic challenge
    import random
    random.seed(seed)
    
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
    
    # For now, challenge text is just the solution with spaces
    challenge_text = ' '.join(solution)
    
    return challenge_text, solution


def verify_challenge_generation(secret: str, session_id: str, challenge_text: str, 
                                 expected_solution: str) -> bool:
    """
    Verify that a challenge was generated correctly using the secret.
    
    Args:
        secret: Base64-encoded secret key
        session_id: Session identifier
        challenge_text: The challenge that was presented
        expected_solution: The solution that was committed to
        
    Returns:
        True if challenge was generated correctly
    """
    # Regenerate challenge using the same secret and session
    regenerated_text, regenerated_solution = generate_challenge_with_secret(
        secret, session_id, "medium"
    )
    
    # Verify the solution matches
    return regenerated_solution.lower() == expected_solution.lower()


def create_commitment(solution: str, nonce: Optional[str] = None) -> Tuple[str, str]:
    """
    Create a cryptographic commitment to a solution.
    
    Uses hash-based commitment: commit = H(solution || nonce)
    
    Args:
        solution: The solution to commit to
        nonce: Optional nonce (generates one if not provided)
        
    Returns:
        Tuple of (commitment_hash, nonce)
    """
    if nonce is None:
        nonce = generate_secret_key(16)
    
    # Create commitment: H(solution || nonce)
    commitment_input = f"{solution.lower().strip()}:{nonce}".encode('utf-8')
    commitment = hashlib.sha256(commitment_input).hexdigest()
    
    return commitment, nonce


def verify_commitment(solution: str, nonce: str, commitment: str) -> bool:
    """
    Verify that a solution opens a commitment correctly.
    
    Args:
        solution: The revealed solution
        nonce: The revealed nonce
        commitment: The original commitment hash
        
    Returns:
        True if commitment is valid
    """
    # Recompute commitment
    commitment_input = f"{solution.lower().strip()}:{nonce}".encode('utf-8')
    recomputed = hashlib.sha256(commitment_input).hexdigest()
    
    return recomputed == commitment


def create_ppe_session_id(user1_id: str, user2_id: str, poll_id: str) -> str:
    """
    Create a unique session ID for a PPE session between two users.
    
    Args:
        user1_id: First user's ID
        user2_id: Second user's ID
        poll_id: Poll identifier
        
    Returns:
        Unique session identifier
    """
    # Sort user IDs to ensure same session ID regardless of who initiates
    sorted_ids = sorted([user1_id, user2_id])
    session_input = f"{poll_id}:{sorted_ids[0]}:{sorted_ids[1]}".encode('utf-8')
    return hashlib.sha256(session_input).hexdigest()[:16]


def verify_solution_correctness(challenge_text: str, solution: str) -> bool:
    """
    Verify that a solution correctly solves a challenge.
    
    Args:
        challenge_text: The challenge text (may contain spaces)
        solution: The proposed solution
        
    Returns:
        True if solution is correct
    """
    # Remove spaces from challenge text to get expected solution
    expected = challenge_text.replace(' ', '').lower().strip()
    provided = solution.lower().strip()
    
    return expected == provided