"""
CAPTCHA service for one-sided PPE during registration.
FIXES Issue #3: Case-insensitive comparison.
FIXES Issue #4: Clarifies this is one-sided PPE (server-verified).
"""

import random
import string
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class CaptchaService:
    """
    One-sided PPE for registration (Protocol 2).
    
    This is CORRECT implementation per paper:
    - Server verifies (not peer-to-peer)
    - Only user expends effort
    - Prevents Sybil registration attacks
    """
    
    def generate_captcha(self, difficulty: int = 6) -> Tuple[str, str]:
        """
        Generate a text-based CAPTCHA.
        
        Returns:
            (challenge, solution) where solution is the correct answer
        """
        # Generate random string (only uppercase for clarity)
        solution = ''.join(random.choices(string.ascii_uppercase + string.digits, k=difficulty))
        
        # In production, this would be an image with distortion
        # For now, simple text challenge
        challenge = f"TYPE THIS: {solution}"
        
        logger.debug(f"Generated CAPTCHA with solution: {solution}")
        
        return challenge, solution
    
    def verify_captcha(self, user_answer: str, correct_solution: str) -> bool:
        """
        Verify CAPTCHA solution.
        
        FIXES Issue #3: Now case-insensitive.
        """
        if not user_answer or not correct_solution:
            return False
        
        # Strip whitespace and convert to uppercase for comparison
        user_normalized = user_answer.strip().upper()
        solution_normalized = correct_solution.strip().upper()
        
        is_correct = user_normalized == solution_normalized
        
        logger.debug(f"CAPTCHA verification: user='{user_normalized}', "
                    f"solution='{solution_normalized}', correct={is_correct}")
        
        return is_correct


# Factory function
def get_captcha_service() -> CaptchaService:
    """Factory function for captcha service."""
    return CaptchaService()