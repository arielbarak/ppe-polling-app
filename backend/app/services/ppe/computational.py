"""
Computational PPE (Proof-of-Work style).

From Appendix B: "Time-locked computational puzzles that require
CPU effort, similar to hashcash or proof-of-work."

Useful for:
- Uniform cost across all users
- No external dependencies
- Adjustable difficulty
"""

import hashlib
import time
from typing import Dict, Any, Tuple, Optional
import logging

from app.services.ppe.base import PPEProtocol
from app.models.ppe_types import PPEType, PPEDifficulty

logger = logging.getLogger(__name__)


class ComputationalPPE(PPEProtocol):
    """
    Computational proof-of-work PPE.
    
    Protocol:
    1. Verifier generates challenge: find nonce such that H(challenge||nonce) < target
    2. Prover searches for valid nonce
    3. Prover submits nonce
    4. Verifier verifies hash meets target
    
    Similar to Bitcoin mining but with adjustable difficulty.
    """
    
    def __init__(
        self,
        difficulty: PPEDifficulty = PPEDifficulty.MEDIUM,
        hash_algorithm: str = "sha256"
    ):
        super().__init__(
            ppe_type=PPEType.COMPUTATIONAL,
            difficulty=difficulty,
            completeness_sigma=0.99,  # Deterministic, always succeeds if done
            soundness_epsilon=0.01    # Very hard to cheat
        )
        
        self.hash_algorithm = hash_algorithm
        
        # Difficulty = number of leading zero bits required
        self.difficulty_bits_map = {
            PPEDifficulty.EASY: 16,      # ~65k hashes
            PPEDifficulty.MEDIUM: 18,    # ~260k hashes
            PPEDifficulty.HARD: 20,      # ~1M hashes
            PPEDifficulty.EXTREME: 22    # ~4M hashes
        }
    
    def generate_challenge(self, session_id: str, prover_id: str, verifier_id: str) -> Dict[str, Any]:
        """
        Generate computational challenge.
        
        Challenge: Find nonce such that H(session_id||prover_id||nonce) has
        required number of leading zero bits.
        """
        difficulty_bits = self.difficulty_bits_map[self.difficulty]
        
        challenge_string = f"{session_id}:{prover_id}:{verifier_id}:{time.time()}"
        
        # Target: hash must be less than this value
        target = 2 ** (256 - difficulty_bits)
        
        return {
            "challenge_id": hashlib.sha256(challenge_string.encode()).hexdigest()[:16],
            "challenge_data": {
                "challenge_string": challenge_string,
                "difficulty_bits": difficulty_bits,
                "target_hex": hex(target),
                "algorithm": self.hash_algorithm,
                "instructions": f"Find nonce where SHA256({challenge_string}||nonce) has {difficulty_bits} leading zero bits"
            },
            "verification_data": {
                "challenge_string": challenge_string,
                "target": target,
                "difficulty_bits": difficulty_bits
            }
        }
    
    def verify_response(
        self,
        challenge_data: Dict[str, Any],
        verification_data: Dict[str, Any],
        prover_response: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify prover found valid nonce.
        """
        nonce = prover_response.get("nonce", "")
        
        if not nonce:
            return False, "No nonce provided"
        
        # Reconstruct hash
        challenge_string = verification_data["challenge_string"]
        target = verification_data["target"]
        
        hash_input = f"{challenge_string}||{nonce}".encode()
        hash_output = hashlib.sha256(hash_input).digest()
        hash_value = int.from_bytes(hash_output, 'big')
        
        # Check if hash meets target
        if hash_value >= target:
            return False, f"Hash doesn't meet target (need {verification_data['difficulty_bits']} zero bits)"
        
        # Verify nonce is reasonable (not too large, prevents abuse)
        try:
            nonce_int = int(nonce)
            if nonce_int < 0 or nonce_int > 2**64:
                return False, "Invalid nonce range"
        except ValueError:
            return False, "Nonce must be integer"
        
        return True, None
    
    def estimate_effort_seconds(self) -> int:
        """
        Estimate time to solve computational puzzle.
        Assumes ~1M hashes/second (typical CPU).
        """
        difficulty_bits = self.difficulty_bits_map[self.difficulty]
        expected_hashes = 2 ** difficulty_bits
        hashes_per_second = 1_000_000  # 1M hashes/sec
        
        estimated_seconds = expected_hashes / hashes_per_second
        
        return int(estimated_seconds)
    
    @staticmethod
    def solve_challenge(challenge_string: str, target: int, max_nonce: int = 2**32) -> Optional[str]:
        """
        Helper: Solve computational challenge (for testing).
        
        This would run on prover's machine.
        """
        for nonce in range(max_nonce):
            hash_input = f"{challenge_string}||{nonce}".encode()
            hash_output = hashlib.sha256(hash_input).digest()
            hash_value = int.from_bytes(hash_output, 'big')
            
            if hash_value < target:
                return str(nonce)
            
            if nonce % 100000 == 0:
                logger.debug(f"Tried {nonce} nonces...")
        
        return None  # No solution found