"""
Models package for PPE polling application.
"""

from .user import User, Poll
from .certification_state import CertificationState
from .proof_graph import ProofGraph, PPECertificationEdge, ParticipantNode, VoteRecord
from .graph_metrics import GraphExpansionMetrics

from sqlalchemy.orm import Session
from typing import List, Dict, Any

def get_certification_graph(db: Session, poll_id: str) -> Dict[str, Any]:
    """
    Get the certification graph for a poll.
    
    Args:
        db: Database session
        poll_id: Poll identifier
        
    Returns:
        Dictionary containing graph structure and metadata
    """
    # For now, return a basic structure since we don't have actual edge tables
    # In a real implementation, this would query the actual certification edges
    from .user import User
    
    # Get all users for this poll
    users = db.query(User).filter(User.poll_id == poll_id).all()
    
    return {
        'poll_id': poll_id,
        'nodes': [user.id for user in users],
        'edges': {},  # Empty for now - would contain actual certification relationships
        'total_edges': 0,
        'total_nodes': len(users)
    }


def get_poll_participants(db: Session, poll_id: str) -> List[Dict[str, Any]]:
    """
    Get all participants for a poll with their certification status.
    
    Args:
        db: Database session
        poll_id: Poll identifier
        
    Returns:
        List of participant information
    """
    from .user import User
    from .certification_state import CertificationState
    
    # Query users and their certification states
    participants = db.query(User, CertificationState).outerjoin(
        CertificationState,
        (User.id == CertificationState.user_id) & 
        (User.poll_id == CertificationState.poll_id)
    ).filter(User.poll_id == poll_id).all()
    
    result = []
    for user, cert_state in participants:
        participant_data = {
            'user_id': user.id,
            'poll_id': user.poll_id,
            'registration_order': user.registration_order,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'certification': None
        }
        
        if cert_state:
            participant_data['certification'] = {
                'required_ppes': cert_state.required_ppes,
                'completed_ppes': cert_state.completed_ppes,
                'failed_ppes': cert_state.failed_ppes,
                'is_certified': cert_state.is_certified,
                'is_excluded': cert_state.is_excluded,
                'has_voted': cert_state.has_voted,
                'completion_percentage': cert_state.completion_percentage,
                'last_updated': cert_state.last_updated.isoformat() if cert_state.last_updated else None
            }
        
        result.append(participant_data)
    
    return result

__all__ = [
    'User',
    'Poll', 
    'CertificationState',
    'ProofGraph',
    'PPECertificationEdge', 
    'ParticipantNode',
    'VoteRecord',
    'GraphExpansionMetrics',
    'get_certification_graph',
    'get_poll_participants'
]