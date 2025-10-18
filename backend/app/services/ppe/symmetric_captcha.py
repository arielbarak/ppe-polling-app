"""
Symmetric CAPTCHA-based PPE.
Both parties solve CAPTCHAs and exchange solutions.

From Appendix B: "Both parties engage in solving CAPTCHAs,
with MAC binding to prevent replay attacks."
"""

import random
import string
import hashlib
import hmac
from typing import Dict, Any, Tuple, Optional
import logging

from app.services.ppe.base import TwoSidedPPE
from app.models.ppe_types import PPEType, PPEDifficulty

logger = logging.getLogger(__name__)


class SymmetricCaptchaPPE(TwoSidedPPE):
    """
    Symmetric CAPTCHA PPE implementation.
    
    Protocol:
    1. Both parties receive CAPTCHA challenges
    2. Both solve their CAPTCHAs
    3. Exchange solutions with MAC binding
    4. Verify both solutions and MACs
    5. Success if both parties solve correctly
    """
    
    def __init__(
        self,
        difficulty: PPEDifficulty = PPEDifficulty.MEDIUM,
        mac_key: bytes = None
    ):
        super().__init__(
            ppe_type=PPEType.SYMMETRIC_CAPTCHA,
            difficulty=difficulty,
            completeness_sigma=0.95,  # 95% success rate for honest users
            soundness_epsilon=0.05     # 5% false positive rate
        )
        
        # MAC key for binding (should be derived from session)
        self.mac_key = mac_key or b"default_mac_key_change_in_production"
        
        # Difficulty settings
        self.difficulty_map = {
            PPEDifficulty.EASY: 4,      # 4 characters
            PPEDifficulty.MEDIUM: 6,    # 6 characters
            PPEDifficulty.HARD: 8,      # 8 characters
            PPEDifficulty.EXTREME: 10   # 10 characters
        }
    
    def generate_challenge(self, session_id: str, prover_id: str, verifier_id: str) -> Dict[str, Any]:
        """Generate single CAPTCHA challenge."""
        length = self.difficulty_map[self.difficulty]
        solution = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        
        # In production, this would generate an image
        challenge_text = self._distort_text(solution)
        
        # Generate MAC
        mac = self._compute_mac(session_id, prover_id, solution)
        
        return {
            "challenge_id": hashlib.sha256(f"{session_id}:{prover_id}".encode()).hexdigest()[:16],
            "challenge_data": {
                "text": challenge_text,
                "length": length,
                "mac": mac.hex()
            },
            "verification_data": {
                "solution": solution,
                "session_id": session_id
            }
        }
    
    def generate_mutual_challenges(
        self,
        session_id: str,
        party_a_id: str,
        party_b_id: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Generate CAPTCHAs for both parties."""
        challenge_a = self.generate_challenge(session_id, party_a_id, party_b_id)
        challenge_b = self.generate_challenge(session_id, party_b_id, party_a_id)
        
        return challenge_a, challenge_b
    
    def verify_response(
        self,
        challenge_data: Dict[str, Any],
        verification_data: Dict[str, Any],
        prover_response: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify a single CAPTCHA response."""
        user_answer = prover_response.get("answer", "")
        user_mac = prover_response.get("mac", "")
        
        correct_solution = verification_data["solution"]
        session_id = verification_data["session_id"]
        
        # Verify MAC first (prevents replay attacks)
        expected_mac = challenge_data["mac"]
        if user_mac != expected_mac:
            return False, "Invalid MAC - possible replay attack"
        
        # Verify answer (case-insensitive)
        if user_answer.strip().upper() != correct_solution.strip().upper():
            return False, "Incorrect CAPTCHA solution"
        
        return True, None
    
    def verify_mutual_responses(
        self,
        challenge_a: Dict[str, Any],
        challenge_b: Dict[str, Any],
        response_a: Dict[str, Any],
        response_b: Dict[str, Any]
    ) -> Tuple[bool, bool]:
        """Verify both parties' CAPTCHA responses."""
        success_a, reason_a = self.verify_response(
            challenge_a["challenge_data"],
            challenge_a["verification_data"],
            response_a
        )
        
        success_b, reason_b = self.verify_response(
            challenge_b["challenge_data"],
            challenge_b["verification_data"],
            response_b
        )
        
        if not success_a:
            logger.debug(f"Party A failed: {reason_a}")
        if not success_b:
            logger.debug(f"Party B failed: {reason_b}")
        
        return success_a, success_b
    
    def estimate_effort_seconds(self) -> int:
        """Estimate time to solve CAPTCHA."""
        effort_map = {
            PPEDifficulty.EASY: 10,
            PPEDifficulty.MEDIUM: 20,
            PPEDifficulty.HARD: 40,
            PPEDifficulty.EXTREME: 60
        }
        return effort_map[self.difficulty]
    
    def _distort_text(self, text: str) -> str:
        """
        Simple text distortion (in production, use image CAPTCHA).
        """
        # Add some visual noise characters
        distorted = ""
        for char in text:
            distorted += char
            if random.random() < 0.3:
                distorted += random.choice([" ", "-", "_"])
        return distorted.strip()
    
    def _compute_mac(self, session_id: str, user_id: str, data: str) -> bytes:
        """Compute HMAC for binding."""
        message = f"{session_id}:{user_id}:{data}".encode()
        return hmac.new(self.mac_key, message, hashlib.sha256).digest()