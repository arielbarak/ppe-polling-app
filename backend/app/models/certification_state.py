"""
Database model for user certification state.
Persists across page refreshes (Issue #5).
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Float
from sqlalchemy.sql import func
from datetime import datetime, timezone
from typing import List, Optional

from app.database import Base


class CertificationState(Base):
    """
    Tracks user's certification progress within a poll.
    
    This solves Issue #5: state persists across refreshes.
    """
    __tablename__ = "certification_states"
    
    # Primary keys
    user_id = Column(String, primary_key=True)
    poll_id = Column(String, primary_key=True)
    
    # Current state
    state = Column(String, nullable=False, default="awaiting_assignments")
    
    # PPE requirements (from graph degree)
    required_ppes = Column(Integer, nullable=False, default=0)
    completed_ppes = Column(Integer, nullable=False, default=0)
    failed_ppes = Column(Integer, nullable=False, default=0)
    
    # Maximum allowed failures (ηE * required_ppes)
    max_allowed_failures = Column(Integer, nullable=False, default=0)
    
    # PPE tracking
    assigned_ppe_partners = Column(JSON, default=list)  # List of user IDs
    completed_ppe_ids = Column(JSON, default=list)      # List of completed PPE IDs
    failed_ppe_ids = Column(JSON, default=list)         # List of failed PPE IDs
    
    # Signatures collected (for certification graph)
    collected_signatures = Column(JSON, default=dict)   # {partner_id: signature}
    
    # Certification status
    is_certified = Column(Boolean, default=False)
    certified_at = Column(DateTime, nullable=True)
    
    # Exclusion (too many failures)
    is_excluded = Column(Boolean, default=False)
    exclusion_reason = Column(String, nullable=True)
    
    # Voting
    has_voted = Column(Boolean, default=False)
    voted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<CertificationState user={self.user_id} poll={self.poll_id} state={self.state}>"
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.required_ppes == 0:
            return 0.0
        return (self.completed_ppes / self.required_ppes) * 100
    
    @property
    def remaining_ppes(self) -> int:
        """Number of PPEs still needed."""
        return max(0, self.required_ppes - self.completed_ppes)
    
    @property
    def can_still_certify(self) -> bool:
        """
        Check if user can still achieve certification.
        
        If failed_ppes > max_allowed_failures, impossible to certify.
        """
        return self.failed_ppes <= self.max_allowed_failures
    
    def update_certification_status(self):
        """
        Update is_certified and is_excluded based on current progress.
        
        Called after each PPE completion/failure.
        """
        # Check if excluded (too many failures)
        if self.failed_ppes > self.max_allowed_failures:
            self.is_excluded = True
            self.exclusion_reason = f"Failed {self.failed_ppes}/{self.required_ppes} PPEs (max allowed: {self.max_allowed_failures})"
            self.is_certified = False
            return
        
        # Check if certified (enough completions)
        if self.completed_ppes >= self.required_ppes:
            self.is_certified = True
            self.certified_at = datetime.now(timezone.utc)
            return
        
        # Still in progress
        self.is_certified = False
    
    def add_completed_ppe(self, ppe_id: str, partner_id: str, signature: str):
        """Record a successful PPE completion."""
        if ppe_id not in self.completed_ppe_ids:
            self.completed_ppe_ids.append(ppe_id)
            self.completed_ppes += 1
            self.collected_signatures[partner_id] = signature
            self.update_certification_status()
    
    def add_failed_ppe(self, ppe_id: str):
        """Record a failed PPE."""
        if ppe_id not in self.failed_ppe_ids:
            self.failed_ppe_ids.append(ppe_id)
            self.failed_ppes += 1
            self.update_certification_status()
    
    def to_dict(self) -> dict:
        """Convert to dict for API response."""
        return {
            "user_id": self.user_id,
            "poll_id": self.poll_id,
            "state": self.state,
            "required_ppes": self.required_ppes,
            "completed_ppes": self.completed_ppes,
            "failed_ppes": self.failed_ppes,
            "max_allowed_failures": self.max_allowed_failures,
            "completion_percentage": self.completion_percentage,
            "remaining_ppes": self.remaining_ppes,
            "is_certified": self.is_certified,
            "is_excluded": self.is_excluded,
            "exclusion_reason": self.exclusion_reason,
            "can_still_certify": self.can_still_certify,
            "has_voted": self.has_voted,
            "assigned_partners": len(self.assigned_ppe_partners),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }