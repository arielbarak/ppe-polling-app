"""
PPE type definitions and enums.
Based on Appendix B of PPE paper.
"""

from enum import Enum
from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from typing import Dict, Any, Optional

from app.database import Base


class PPEType(str, Enum):
    """
    Types of PPE protocols available.
    Each has different tradeoffs for security, usability, and cost.
    """
    # One-sided PPE (server verification)
    REGISTRATION_CAPTCHA = "registration_captcha"  # Simple text CAPTCHA
    
    # Two-sided PPE (peer-to-peer)
    SYMMETRIC_CAPTCHA = "symmetric_captcha"        # Both solve CAPTCHAs
    PROOF_OF_STORAGE = "proof_of_storage"          # Cloud storage verification
    HUMAN_INTERACTION = "human_interaction"        # Video/audio challenge
    SOCIAL_DISTANCE = "social_distance"            # Social graph distance
    COMPUTATIONAL = "computational"                # Proof-of-work style


class PPEDifficulty(str, Enum):
    """Difficulty levels for PPE challenges."""
    EASY = "easy"          # ~10 seconds
    MEDIUM = "medium"      # ~30 seconds
    HARD = "hard"          # ~60 seconds
    EXTREME = "extreme"    # ~120+ seconds


class PPEConfig(Base):
    """
    Configuration for PPE in a specific poll.
    
    Each poll can specify:
    - Which PPE types are allowed
    - Difficulty settings
    - Timeout values
    - Concurrent execution limits
    """
    __tablename__ = "ppe_configs"
    
    poll_id = Column(String, primary_key=True)
    
    # Registration PPE (one-sided)
    registration_ppe_type = Column(String, default=PPEType.REGISTRATION_CAPTCHA)
    registration_difficulty = Column(String, default=PPEDifficulty.MEDIUM)
    
    # Certification PPE (two-sided) - can allow multiple types
    allowed_certification_types = Column(JSON, default=list)  # List of PPEType values
    default_certification_type = Column(String, default=PPEType.SYMMETRIC_CAPTCHA)
    certification_difficulty = Column(String, default=PPEDifficulty.MEDIUM)
    
    # Timeout settings (seconds)
    ppe_timeout = Column(Integer, default=300)  # 5 minutes
    
    # Concurrent execution
    max_concurrent_ppes = Column(Integer, default=3)  # Max simultaneous PPEs per user
    
    # Security parameters from Definition 2.2
    completeness_sigma = Column(Float, default=0.95)  # σ-completeness
    soundness_epsilon = Column(Float, default=0.05)   # ε-soundness
    
    # Audit settings
    enable_audit_logging = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "poll_id": self.poll_id,
            "registration_ppe_type": self.registration_ppe_type,
            "registration_difficulty": self.registration_difficulty,
            "allowed_certification_types": self.allowed_certification_types,
            "default_certification_type": self.default_certification_type,
            "certification_difficulty": self.certification_difficulty,
            "ppe_timeout": self.ppe_timeout,
            "max_concurrent_ppes": self.max_concurrent_ppes,
            "completeness_sigma": self.completeness_sigma,
            "soundness_epsilon": self.soundness_epsilon
        }


class PPEExecution(Base):
    """
    Record of a PPE execution between two users.
    Stores all data needed for verification and audit.
    """
    __tablename__ = "ppe_executions"
    
    id = Column(String, primary_key=True)
    poll_id = Column(String, nullable=False, index=True)
    
    # Participants
    prover_id = Column(String, nullable=False, index=True)
    verifier_id = Column(String, nullable=False, index=True)
    
    # PPE details
    ppe_type = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    
    # Execution state
    status = Column(String, default="pending")  # pending, in_progress, completed, failed, timeout
    
    # Challenge and response data (encrypted/hashed)
    challenge_data = Column(JSON)
    prover_response = Column(JSON)
    verifier_response = Column(JSON)
    
    # Verification result
    result = Column(Boolean, nullable=True)  # None=pending, True=success, False=failure
    failure_reason = Column(String, nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Audit trail
    prover_ip = Column(String, nullable=True)  # Optional, for fraud detection
    verifier_ip = Column(String, nullable=True)
    prover_user_agent = Column(String, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<PPEExecution {self.id} type={self.ppe_type} status={self.status}>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "poll_id": self.poll_id,
            "prover_id": self.prover_id,
            "verifier_id": self.verifier_id,
            "ppe_type": self.ppe_type,
            "difficulty": self.difficulty,
            "status": self.status,
            "result": self.result,
            "failure_reason": self.failure_reason,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds
        }