"""
Utilities for Proof of Private Effort (PPE) protocol.

Now uses the modular PPE factory system.
"""

import hashlib
import secrets
import base64
from typing import Tuple, Optional
import json

from ..ppe.factory import ppe_factory
from ..ppe.base import PPEType, PPEDifficulty


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


def generate_challenge_with_secret(secret: str, session_id: str, 
                                   ppe_type: str = "symmetric_captcha",
                                   difficulty: str = "medium") -> Tuple[str, str]:
    """
    Generate a challenge deterministically from a secret.
    
    Uses the PPE factory to support multiple challenge types.
    
    Args:
        secret: Base64-encoded secret key
        session_id: Unique identifier for this PPE session
        ppe_type: Type of PPE mechanism to use
        difficulty: Challenge difficulty
        
    Returns:
        Tuple of (challenge_data, solution)
    """
    try:
        ppe_type_enum = PPEType(ppe_type)
        difficulty_enum = PPEDifficulty(difficulty)
    except ValueError:
        # Fallback to defaults
        ppe_type_enum = PPEType.SYMMETRIC_CAPTCHA
        difficulty_enum = PPEDifficulty.MEDIUM
    
    # Create PPE instance
    ppe = ppe_factory.create(ppe_type_enum, difficulty_enum)
    
    # Generate challenge
    return ppe.generate_challenge_with_secret(secret, session_id)


def verify_challenge_generation(secret: str, session_id: str, challenge_text: str, 
                                expected_solution: str, ppe_type: str = "symmetric_captcha") -> bool:
    """
    Verify that a challenge was generated correctly using the secret.
    
    Args:
        secret: Base64-encoded secret key
        session_id: Session identifier
        challenge_text: The challenge that was presented
        expected_solution: The solution that was committed to
        ppe_type: Type of PPE mechanism
        
    Returns:
        True if challenge was generated correctly
    """
    try:
        ppe_type_enum = PPEType(ppe_type)
    except ValueError:
        ppe_type_enum = PPEType.SYMMETRIC_CAPTCHA
    
    ppe = ppe_factory.create(ppe_type_enum)
    return ppe.verify_challenge_generation(secret, session_id, challenge_text, expected_solution)


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


def verify_solution_correctness(challenge_text: str, solution: str, 
                                ppe_type: str = "symmetric_captcha") -> bool:
    """
    Verify that a solution correctly solves a challenge.
    
    Args:
        challenge_text: The challenge text
        solution: The proposed solution
        ppe_type: Type of PPE mechanism
        
    Returns:
        True if solution is correct
    """
    try:
        ppe_type_enum = PPEType(ppe_type)
    except ValueError:
        ppe_type_enum = PPEType.SYMMETRIC_CAPTCHA
    
    ppe = ppe_factory.create(ppe_type_enum)
    return ppe.verify_solution(challenge_text, solution)


# Keep existing commitment and session functions unchanged