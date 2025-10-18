"""
Abstract base class for PPE implementations.
All PPE types inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import logging
from datetime import datetime

from app.models.ppe_types import PPEType, PPEDifficulty

logger = logging.getLogger(__name__)


class PPEProtocol(ABC):
    """
    Abstract base class for PPE protocols.
    
    Implements Definition 2.2 from paper:
    - σ-completeness: Honest parties succeed with probability ≥ σ
    - ε-soundness: Adversary succeeds with probability ≤ ε
    """
    
    def __init__(
        self,
        ppe_type: PPEType,
        difficulty: PPEDifficulty,
        completeness_sigma: float = 0.95,
        soundness_epsilon: float = 0.05
    ):
        self.ppe_type = ppe_type
        self.difficulty = difficulty
        self.completeness_sigma = completeness_sigma
        self.soundness_epsilon = soundness_epsilon
        
        logger.info(f"Initialized {ppe_type} PPE with difficulty={difficulty}")
    
    @abstractmethod
    def generate_challenge(self, session_id: str, prover_id: str, verifier_id: str) -> Dict[str, Any]:
        """
        Generate a challenge for the PPE.
        
        Returns:
            {
                "challenge_id": "...",
                "challenge_data": {...},  # Data for prover
                "verification_data": {...}  # Private data for verifier
            }
        """
        pass
    
    @abstractmethod
    def verify_response(
        self,
        challenge_data: Dict[str, Any],
        verification_data: Dict[str, Any],
        prover_response: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify prover's response to challenge.
        
        Returns:
            (success: bool, failure_reason: Optional[str])
        """
        pass
    
    @abstractmethod
    def estimate_effort_seconds(self) -> int:
        """
        Estimate time required for honest user to complete PPE.
        Used for timeout calculations.
        """
        pass
    
    def get_timeout_seconds(self) -> int:
        """
        Calculate timeout for this PPE.
        Default: 3x estimated effort (allows for variance).
        """
        return self.estimate_effort_seconds() * 3
    
    def validate_security_parameters(self) -> Tuple[bool, Optional[str]]:
        """
        Validate that σ and ε satisfy security requirements.
        
        From paper: σ ≥ 0.9, ε ≤ 0.1 (typical values)
        """
        if self.completeness_sigma < 0.5:
            return False, f"Completeness σ={self.completeness_sigma} too low (need ≥ 0.5)"
        
        if self.soundness_epsilon > 0.2:
            return False, f"Soundness ε={self.soundness_epsilon} too high (need ≤ 0.2)"
        
        if self.completeness_sigma + self.soundness_epsilon <= 1.0:
            return False, f"Invalid: σ + ε = {self.completeness_sigma + self.soundness_epsilon} ≤ 1"
        
        return True, None
    
    def log_execution(self, execution_id: str, success: bool, duration: float):
        """Log PPE execution for audit."""
        logger.info(
            f"PPE {execution_id} ({self.ppe_type}): "
            f"success={success}, duration={duration:.2f}s"
        )


class TwoSidedPPE(PPEProtocol):
    """
    Base class for two-sided (symmetric) PPE protocols.
    Both prover and verifier expend effort.
    """
    
    @abstractmethod
    def generate_mutual_challenges(
        self,
        session_id: str,
        party_a_id: str,
        party_b_id: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate challenges for both parties.
        
        Returns:
            (challenge_for_a, challenge_for_b)
        """
        pass
    
    @abstractmethod
    def verify_mutual_responses(
        self,
        challenge_a: Dict[str, Any],
        challenge_b: Dict[str, Any],
        response_a: Dict[str, Any],
        response_b: Dict[str, Any]
    ) -> Tuple[bool, bool]:
        """
        Verify both parties' responses.
        
        Returns:
            (a_succeeded, b_succeeded)
        """
        pass


class OneSidedPPE(PPEProtocol):
    """
    Base class for one-sided PPE protocols.
    Only prover expends effort.
    """
    
    def is_two_sided(self) -> bool:
        return False