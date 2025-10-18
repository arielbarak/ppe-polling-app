"""
Base interface for PPE mechanisms.

All PPE implementations must inherit from BasePPE and implement
the required methods. This allows the system to support multiple
proof-of-effort types.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional
from enum import Enum


class PPEDifficulty(str, Enum):
    """Standard difficulty levels for PPE mechanisms."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class PPEType(str, Enum):
    """Types of PPE mechanisms available."""
    SYMMETRIC_CAPTCHA = "symmetric_captcha"
    PROOF_OF_WORK = "proof_of_work"
    PROOF_OF_STORAGE = "proof_of_storage"
    AUDIO_CAPTCHA = "audio_captcha"
    IMAGE_RECOGNITION = "image_recognition"


class BasePPE(ABC):
    """
    Base class for all PPE mechanisms.
    
    Each PPE type must implement these methods to be compatible
    with the system.
    """
    
    def __init__(self, difficulty: PPEDifficulty = PPEDifficulty.MEDIUM):
        """
        Initialize PPE mechanism.
        
        Args:
            difficulty: Challenge difficulty level
        """
        self.difficulty = difficulty
        self.ppe_type = self.get_type()
    
    @abstractmethod
    def get_type(self) -> PPEType:
        """
        Get the PPE type identifier.
        
        Returns:
            PPEType enum value
        """
        pass
    
    @abstractmethod
    def generate_challenge_with_secret(self, secret: str, session_id: str) -> Tuple[Any, str]:
        """
        Generate a challenge deterministically from a secret.
        
        This is used in the symmetric PPE protocol where both parties
        generate challenges that can later be verified.
        
        Args:
            secret: Secret key for generation
            session_id: Unique session identifier
            
        Returns:
            Tuple of (challenge_data, solution)
            challenge_data can be any serializable format
        """
        pass
    
    @abstractmethod
    def verify_challenge_generation(self, secret: str, session_id: str, 
                                    challenge_data: Any, solution: str) -> bool:
        """
        Verify that a challenge was generated correctly using the secret.
        
        Args:
            secret: The secret key
            session_id: Session identifier
            challenge_data: The challenge that was presented
            solution: The claimed solution
            
        Returns:
            True if challenge was generated correctly
        """
        pass
    
    @abstractmethod
    def verify_solution(self, challenge_data: Any, solution: str) -> bool:
        """
        Verify that a solution correctly solves a challenge.
        
        Args:
            challenge_data: The challenge data
            solution: The proposed solution
            
        Returns:
            True if solution is correct
        """
        pass
    
    @abstractmethod
    def estimate_effort(self) -> float:
        """
        Estimate the computational/human effort required to solve.
        
        Returns:
            Estimated time in seconds
        """
        pass
    
    def get_client_config(self) -> Dict[str, Any]:
        """
        Get configuration to send to client.
        
        Returns:
            Dictionary with client-side configuration
        """
        return {
            "type": self.ppe_type.value,
            "difficulty": self.difficulty.value,
            "estimated_effort": self.estimate_effort()
        }
    
    def serialize_challenge(self, challenge_data: Any) -> Dict[str, Any]:
        """
        Serialize challenge data for transmission.
        
        Override if custom serialization needed.
        
        Args:
            challenge_data: Challenge to serialize
            
        Returns:
            Serializable dictionary
        """
        return {
            "type": self.ppe_type.value,
            "data": challenge_data
        }
    
    def deserialize_challenge(self, serialized: Dict[str, Any]) -> Any:
        """
        Deserialize challenge data from transmission.
        
        Override if custom deserialization needed.
        
        Args:
            serialized: Serialized challenge dictionary
            
        Returns:
            Challenge data in native format
        """
        return serialized.get("data")


class PPEMetadata:
    """
    Metadata about a PPE mechanism for display and selection.
    """
    def __init__(self, 
                 ppe_type: PPEType,
                 name: str,
                 description: str,
                 requires_human: bool,
                 supports_batch: bool = False,
                 client_library_required: bool = False):
        self.ppe_type = ppe_type
        self.name = name
        self.description = description
        self.requires_human = requires_human
        self.supports_batch = supports_batch
        self.client_library_required = client_library_required
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.ppe_type.value,
            "name": self.name,
            "description": self.description,
            "requires_human": self.requires_human,
            "supports_batch": self.supports_batch,
            "client_library_required": self.client_library_required
        }