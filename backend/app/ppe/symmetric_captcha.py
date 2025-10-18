"""
Symmetric CAPTCHA PPE implementation.

Refactored from the original implementation to use the modular interface.
"""

from .base import BasePPE, PPEType, PPEDifficulty
from typing import Tuple, Any
import hashlib
import random


class SymmetricCaptchaPPE(BasePPE):
    """
    Symmetric CAPTCHA implementation using text challenges.
    
    Both parties generate text CAPTCHAs with secrets, solve each other's
    challenges, and verify using the commitment scheme.
    """
    
    def get_type(self) -> PPEType:
        """Get PPE type identifier."""
        return PPEType.SYMMETRIC_CAPTCHA
    
    def generate_challenge_with_secret(self, secret: str, session_id: str) -> Tuple[str, str]:
        """
        Generate a text CAPTCHA challenge deterministically.
        
        Args:
            secret: Secret key for generation
            session_id: Session identifier
            
        Returns:
            Tuple of (challenge_text, solution)
        """
        # Import here to avoid circular dependency
        from ..utils.captcha_utils import generate_random_string
        
        # Create deterministic seed
        seed_input = f"{secret}:{session_id}".encode('utf-8')
        seed_hash = hashlib.sha256(seed_input).digest()
        seed = int.from_bytes(seed_hash[:8], byteorder='big')
        
        # Use seed for deterministic generation
        random.seed(seed)
        
        # Get difficulty settings
        difficulty_settings = {
            PPEDifficulty.EASY: {"length": 4, "uppercase": False, "digits": False},
            PPEDifficulty.MEDIUM: {"length": 6, "uppercase": True, "digits": True},
            PPEDifficulty.HARD: {"length": 8, "uppercase": True, "digits": True}
        }
        
        settings = difficulty_settings.get(self.difficulty, difficulty_settings[PPEDifficulty.MEDIUM])
        
        # Generate solution
        solution = generate_random_string(
            length=settings["length"],
            include_uppercase=settings["uppercase"],
            include_digits=settings["digits"]
        )
        
        # Challenge text with spaces
        challenge_text = ' '.join(solution)
        
        return challenge_text, solution
    
    def verify_challenge_generation(self, secret: str, session_id: str, 
                                    challenge_text: str, solution: str) -> bool:
        """
        Verify challenge was generated correctly.
        
        Args:
            secret: Secret key
            session_id: Session identifier
            challenge_text: The challenge presented
            solution: The claimed solution
            
        Returns:
            True if valid
        """
        # Regenerate challenge
        regenerated_text, regenerated_solution = self.generate_challenge_with_secret(
            secret, session_id
        )
        
        # Verify solution matches
        return regenerated_solution.lower() == solution.lower()
    
    def verify_solution(self, challenge_text: str, solution: str) -> bool:
        """
        Verify solution solves challenge.
        
        Args:
            challenge_text: The challenge (with spaces)
            solution: The proposed solution
            
        Returns:
            True if correct
        """
        # Remove spaces from challenge to get expected solution
        expected = challenge_text.replace(' ', '').lower().strip()
        provided = solution.lower().strip()
        
        return expected == provided
    
    def estimate_effort(self) -> float:
        """
        Estimate time to solve in seconds.
        
        Returns:
            Estimated time
        """
        difficulty_times = {
            PPEDifficulty.EASY: 5.0,
            PPEDifficulty.MEDIUM: 10.0,
            PPEDifficulty.HARD: 20.0
        }
        return difficulty_times.get(self.difficulty, 10.0)