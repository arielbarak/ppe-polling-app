"""
PPE execution orchestrator.
Manages concurrent PPE executions and state.
"""

import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from app.models.ppe_types import PPEType, PPEExecution, PPEConfig, PPEDifficulty
from app.services.ppe.base import PPEProtocol
from app.services.ppe.symmetric_captcha import SymmetricCaptchaPPE
from app.services.ppe.proof_of_storage import ProofOfStoragePPE
from app.services.ppe.computational import ComputationalPPE
from app.services.ppe.social_distance import SocialDistancePPE

logger = logging.getLogger(__name__)


class PPEExecutor:
    """
    Orchestrates PPE execution between users.
    Handles:
    - PPE type selection
    - Concurrent execution limits
    - Timeout management
    - State tracking
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Registry of available PPE implementations
        self.ppe_registry: Dict[PPEType, type] = {
            PPEType.SYMMETRIC_CAPTCHA: SymmetricCaptchaPPE,
            PPEType.PROOF_OF_STORAGE: ProofOfStoragePPE,
            PPEType.COMPUTATIONAL: ComputationalPPE,
            PPEType.SOCIAL_DISTANCE: SocialDistancePPE,
        }
    
    def initiate_ppe(
        self,
        poll_id: str,
        prover_id: str,
        verifier_id: str,
        ppe_type: Optional[PPEType] = None
    ) -> PPEExecution:
        """
        Initiate a new PPE execution between two users.
        
        Args:
            poll_id: Poll identifier
            prover_id: User who will prove effort
            verifier_id: User who will verify
            ppe_type: Specific PPE type (or None to use poll default)
            
        Returns:
            PPEExecution record
        """
        # Get poll PPE configuration
        config = self.db.query(PPEConfig).filter_by(poll_id=poll_id).first()
        if not config:
            raise ValueError(f"No PPE config for poll {poll_id}")
        
        # Determine PPE type
        if ppe_type is None:
            ppe_type = PPEType(config.default_certification_type)
        
        # Validate PPE type is allowed
        if ppe_type not in config.allowed_certification_types:
            raise ValueError(f"PPE type {ppe_type} not allowed for this poll")
        
        # Check concurrent execution limit
        active_ppes = self.db.query(PPEExecution).filter(
            PPEExecution.prover_id == prover_id,
            PPEExecution.poll_id == poll_id,
            PPEExecution.status.in_(["pending", "in_progress"])
        ).count()
        
        if active_ppes >= config.max_concurrent_ppes:
            raise ValueError(f"User has {active_ppes} active PPEs (max: {config.max_concurrent_ppes})")
        
        # Create PPE instance
        ppe_impl = self._create_ppe_instance(
            ppe_type,
            PPEDifficulty(config.certification_difficulty)
        )
        
        # Generate challenge
        session_id = f"{poll_id}:{prover_id}:{verifier_id}"
        challenge = ppe_impl.generate_challenge(session_id, prover_id, verifier_id)
        
        # Create execution record
        execution = PPEExecution(
            id=str(uuid.uuid4()),
            poll_id=poll_id,
            prover_id=prover_id,
            verifier_id=verifier_id,
            ppe_type=ppe_type,
            difficulty=config.certification_difficulty,
            status="pending",
            challenge_data=challenge["challenge_data"],
            started_at=datetime.utcnow()
        )
        
        # Store verification data securely (would encrypt in production)
        # For now, store in separate secure table (omitted for brevity)
        
        self.db.add(execution)
        self.db.commit()
        
        logger.info(f"Initiated {ppe_type} PPE: {execution.id}")
        
        return execution
    
    def submit_response(
        self,
        execution_id: str,
        prover_response: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Submit prover's response to PPE challenge.
        
        Returns:
            (success, failure_reason)
        """
        execution = self.db.query(PPEExecution).filter_by(id=execution_id).first()
        if not execution:
            return False, "Execution not found"
        
        # Check timeout
        config = self.db.query(PPEConfig).filter_by(poll_id=execution.poll_id).first()
        timeout_dt = execution.started_at + timedelta(seconds=config.ppe_timeout)
        
        if datetime.utcnow() > timeout_dt:
            execution.status = "timeout"
            execution.result = False
            execution.failure_reason = "Timeout exceeded"
            self.db.commit()
            return False, "Timeout exceeded"
        
        # Update status
        execution.status = "in_progress"
        execution.prover_response = prover_response
        self.db.commit()
        
        # Create PPE instance
        ppe_impl = self._create_ppe_instance(
            PPEType(execution.ppe_type),
            PPEDifficulty(execution.difficulty)
        )
        
        # Verify response
        # Note: In production, get verification_data from secure storage
        verification_data = {}  # Would retrieve from secure store
        
        success, failure_reason = ppe_impl.verify_response(
            execution.challenge_data,
            verification_data,
            prover_response
        )
        
        # Update execution record
        execution.status = "completed"
        execution.result = success
        execution.failure_reason = failure_reason
        execution.completed_at = datetime.utcnow()
        execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
        
        self.db.commit()
        
        logger.info(f"PPE {execution_id} completed: success={success}")
        
        return success, failure_reason
    
    def get_active_ppes(self, user_id: str, poll_id: str) -> List[PPEExecution]:
        """Get all active PPEs for a user."""
        return self.db.query(PPEExecution).filter(
            PPEExecution.prover_id == user_id,
            PPEExecution.poll_id == poll_id,
            PPEExecution.status.in_(["pending", "in_progress"])
        ).all()
    
    def cleanup_expired_ppes(self, poll_id: str):
        """Mark timed-out PPEs as failed."""
        config = self.db.query(PPEConfig).filter_by(poll_id=poll_id).first()
        if not config:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(seconds=config.ppe_timeout)
        
        expired = self.db.query(PPEExecution).filter(
            PPEExecution.poll_id == poll_id,
            PPEExecution.status.in_(["pending", "in_progress"]),
            PPEExecution.started_at < cutoff_time
        ).all()
        
        for execution in expired:
            execution.status = "timeout"
            execution.result = False
            execution.failure_reason = "Timeout - no response received"
        
        self.db.commit()
        
        logger.info(f"Cleaned up {len(expired)} expired PPEs for poll {poll_id}")
    
    def _create_ppe_instance(self, ppe_type: PPEType, difficulty: PPEDifficulty) -> PPEProtocol:
        """Create PPE implementation instance."""
        ppe_class = self.ppe_registry.get(ppe_type)
        if not ppe_class:
            raise ValueError(f"Unknown PPE type: {ppe_type}")
        
        return ppe_class(difficulty=difficulty)


def get_ppe_executor(db: Session) -> PPEExecutor:
    """Factory function."""
    return PPEExecutor(db)