"""
Automatic PPE partner assignment service.
Implements Protocol 3 from PPE paper.

FIXES Issue #2: No more manual "Verify User" button.
"""

import hashlib
from typing import List, Dict, Set
import logging
from sqlalchemy.orm import Session

from app.models.user import Poll, User
from app.models.certification_state import CertificationState
from app.services.state_machine import get_state_machine, PollPhase

logger = logging.getLogger(__name__)


class PPEAssignmentService:
    """
    Automatically assigns PPE partners based on certification graph.
    
    From PPE paper Protocol 3:
    "For each index i, we define Ni to be 'the neighborhood of i' in the 
    certification graph. Ni is computed from i and m using a cryptographic 
    hash H: j ∈ Ni iff H(i, j) ≤ p"
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def compute_edge_probability(
        self,
        poll_id: str
    ) -> float:
        """
        Compute edge probability p from poll parameters.
        
        From paper: p = d/m where d is expected degree, m is total nodes.
        """
        poll = self.db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            raise ValueError(f"Poll {poll_id} not found")
        
        # Get expected degree from poll config
        # This should be set when poll is created based on security params
        expected_degree = getattr(poll, 'expected_degree', 60)  # Default to 60
        
        # Count registered users
        m = self.db.query(User).filter_by(poll_id=poll_id).count()
        
        if m == 0:
            return 0.0
        
        # p = d/m
        p = expected_degree / m
        
        # Ensure p ≤ 1
        p = min(p, 1.0)
        
        logger.info(f"Poll {poll_id}: m={m}, d={expected_degree}, p={p:.4f}")
        
        return p
    
    def compute_neighborhood(
        self,
        user_index: int,
        all_user_indices: List[int],
        edge_probability: float,
        poll_session_id: str
    ) -> Set[int]:
        """
        Compute neighborhood Ni for user i.
        
        From Protocol 3: j ∈ Ni iff H(i, j) < p
        
        Args:
            user_index: Index of user i (position in shuffled list)
            all_user_indices: List of all user indices
            edge_probability: p value
            poll_session_id: Unique poll session ID (sid from paper)
            
        Returns:
            Set of neighbor indices
        """
        neighbors = set()
        
        for j in all_user_indices:
            if user_index == j:
                continue
            
            # Compute H(i, j) using SHA-256
            # Use min(i,j), max(i,j) to ensure symmetry
            min_idx = min(user_index, j)
            max_idx = max(user_index, j)
            
            # Include poll session ID to prevent cross-poll reuse
            hash_input = f"{poll_session_id}:{min_idx}:{max_idx}".encode('utf-8')
            hash_output = hashlib.sha256(hash_input).digest()
            
            # Interpret hash as binary fraction in [0, 1]
            # Take first 8 bytes, convert to float in [0, 1]
            hash_value = int.from_bytes(hash_output[:8], 'big') / (2**64)
            
            # Check if edge exists: H(i,j) < p
            if hash_value < edge_probability:
                neighbors.add(j)
        
        return neighbors
    
    def assign_ppe_partners(self, poll_id: str) -> Dict[str, List[str]]:
        """
        Assign PPE partners to all users in the poll.
        
        This is called AUTOMATICALLY when registration closes.
        No manual button needed!
        
        Returns:
            Dict mapping user_id -> list of partner user_ids
        """
        logger.info(f"Assigning PPE partners for poll {poll_id}")
        
        poll = self.db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            raise ValueError(f"Poll {poll_id} not found")
        
        # Get all registered users (shuffled order from Protocol 2)
        users = self.db.query(User).filter_by(poll_id=poll_id).order_by(User.registration_order).all()
        
        if len(users) == 0:
            logger.warning(f"No users registered for poll {poll_id}")
            return {}
        
        # Compute edge probability
        p = self.compute_edge_probability(poll_id)
        
        # Build user index mapping
        user_id_to_index = {user.id: idx for idx, user in enumerate(users)}
        index_to_user_id = {idx: user.id for idx, user in enumerate(users)}
        
        # Use poll ID as session ID if no dedicated session_id field
        session_id = getattr(poll, 'session_id', poll_id)
        
        # Compute neighborhoods for all users
        assignments = {}
        
        for i, user in enumerate(users):
            # Compute Ni (neighbors of user i)
            neighbor_indices = self.compute_neighborhood(
                user_index=i,
                all_user_indices=list(range(len(users))),
                edge_probability=p,
                poll_session_id=session_id
            )
            
            # Convert indices to user IDs
            partner_ids = [index_to_user_id[j] for j in neighbor_indices]
            assignments[user.id] = partner_ids
            
            # Store in certification state
            cert_state = self.db.query(CertificationState).filter_by(
                user_id=user.id,
                poll_id=poll_id
            ).first()
            
            if not cert_state:
                cert_state = CertificationState(
                    user_id=user.id,
                    poll_id=poll_id
                )
                self.db.add(cert_state)
            
            cert_state.assigned_ppe_partners = partner_ids
            cert_state.required_ppes = len(partner_ids)
            
            # Calculate max allowed failures (ηE from paper)
            eta_e = getattr(poll, 'eta_e', 0.125)  # Default 12.5%
            cert_state.max_allowed_failures = int(eta_e * len(partner_ids))
            
            cert_state.state = "certifying"
            
            logger.debug(f"User {user.id}: {len(partner_ids)} partners, max {cert_state.max_allowed_failures} failures")
        
        self.db.commit()
        
        logger.info(f"Assigned PPE partners to {len(users)} users")
        
        # Only transition poll to certification phase if it's not already there
        if poll.phase == PollPhase.REGISTRATION:
            state_machine = get_state_machine(self.db)
            state_machine.transition_to_certification(poll_id)
        
        return assignments
    
    def get_user_assignments(self, user_id: str, poll_id: str) -> Dict:
        """
        Get PPE assignments for a specific user.
        
        Returns:
            {
                "partners": [{"user_id": "...", "username": "...", "status": "pending"}],
                "required": 10,
                "completed": 3,
                "failed": 1,
                "remaining": 6
            }
        """
        cert_state = self.db.query(CertificationState).filter_by(
            user_id=user_id,
            poll_id=poll_id
        ).first()
        
        if not cert_state:
            return {
                "partners": [],
                "required": 0,
                "completed": 0,
                "failed": 0,
                "remaining": 0
            }
        
        # Get partner details
        partners = []
        for partner_id in cert_state.assigned_ppe_partners:
            partner_user = self.db.query(User).filter_by(id=partner_id).first()
            
            # Determine status
            if partner_id in cert_state.completed_ppe_ids:
                status = "completed"
            elif partner_id in cert_state.failed_ppe_ids:
                status = "failed"
            else:
                status = "pending"
            
            partners.append({
                "user_id": partner_id,
                "username": partner_user.username if partner_user else "Unknown",
                "status": status
            })
        
        return {
            "partners": partners,
            "required": cert_state.required_ppes,
            "completed": cert_state.completed_ppes,
            "failed": cert_state.failed_ppes,
            "remaining": cert_state.remaining_ppes
        }


def get_assignment_service(db: Session) -> PPEAssignmentService:
    """Factory function."""
    return PPEAssignmentService(db)