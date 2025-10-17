"""
Service for handling poll registration with initial PPE.
"""

from typing import Dict, Any, Optional
from ..utils.captcha_utils import (
    create_registration_challenge,
    get_challenge,
    store_challenge,
    remove_challenge,
    CaptchaChallenge
)


class RegistrationService:
    """
    Handles registration challenges and validation.
    """
    
    def __init__(self):
        self.default_difficulty = "medium"
        self.challenge_validity_minutes = 5
    
    def create_challenge(self, poll_id: str, difficulty: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a registration challenge for a poll.
        
        Args:
            poll_id: Poll identifier
            difficulty: Challenge difficulty (None uses default)
            
        Returns:
            Dictionary with challenge_id and challenge_text
        """
        effective_difficulty = difficulty or self.default_difficulty
        
        challenge = create_registration_challenge(
            difficulty=effective_difficulty,
            validity_minutes=self.challenge_validity_minutes
        )
        
        # Store the challenge
        store_challenge(challenge)
        
        return {
            "challenge_id": challenge.challenge_id,
            "challenge_text": challenge.challenge_text,
            "expires_at": challenge.expires_at.isoformat(),
            "poll_id": poll_id
        }
    
    def validate_challenge(self, challenge_id: str, solution: str) -> bool:
        """
        Validate a challenge solution.
        
        Args:
            challenge_id: Challenge identifier
            solution: User's solution
            
        Returns:
            True if valid, False otherwise
        """
        challenge = get_challenge(challenge_id)
        
        if not challenge:
            return False
        
        # Verify solution
        is_valid = challenge.verify_solution(solution)
        
        # Remove challenge after validation attempt (use once)
        remove_challenge(challenge_id)
        
        return is_valid
    
    def get_challenge_info(self, challenge_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a challenge without revealing the solution.
        
        Args:
            challenge_id: Challenge identifier
            
        Returns:
            Dictionary with challenge info or None if not found
        """
        challenge = get_challenge(challenge_id)
        
        if not challenge:
            return None
        
        return {
            "challenge_id": challenge.challenge_id,
            "challenge_text": challenge.challenge_text,
            "is_expired": challenge.is_expired(),
            "created_at": challenge.created_at.isoformat(),
            "expires_at": challenge.expires_at.isoformat()
        }


# Singleton instance
registration_service = RegistrationService()