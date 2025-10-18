"""
Data models for the proof graph structure.

The proof graph is the complete, verifiable proof of a poll's integrity.
It includes all participants, certifications, votes, and cryptographic bindings.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json


class ParticipantNode(BaseModel):
    """
    Represents a participant in the proof graph.
    """
    user_id: str
    public_key: Dict[str, Any]
    registered_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for hashing."""
        return {
            "user_id": self.user_id,
            "public_key": self.public_key
        }


class PPECertificationEdge(BaseModel):
    """
    Represents a PPE certification between two participants.
    """
    source_user_id: str
    target_user_id: str
    certification_type: str = "ppe"  # Type of certification
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for hashing."""
        return {
            "source": self.source_user_id,
            "target": self.target_user_id,
            "type": self.certification_type
        }


class VoteRecord(BaseModel):
    """
    Represents a vote in the proof graph.
    """
    user_id: str
    public_key: Dict[str, Any]
    option: str
    signature: str
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for hashing."""
        return {
            "user_id": self.user_id,
            "public_key": self.public_key,
            "option": self.option,
            "signature": self.signature
        }


class GraphMetadata(BaseModel):
    """
    Metadata about the proof graph.
    """
    poll_id: str
    question: str
    options: List[str]
    num_participants: int
    num_certifications: int
    num_votes: int
    min_certifications_required: int = 2
    created_at: str
    pollster_signature: Optional[str] = None


class ProofGraph(BaseModel):
    """
    Complete proof graph for a poll.
    
    This is the cryptographically bound structure that proves the poll's integrity.
    Anyone can verify this graph without trusting the pollster.
    """
    metadata: GraphMetadata
    participants: List[ParticipantNode]
    certifications: List[PPECertificationEdge]
    votes: List[VoteRecord]
    graph_hash: Optional[str] = None
    
    def compute_hash(self) -> str:
        """
        Compute a cryptographic hash of the entire proof graph.
        
        This hash binds all components together. Any modification to
        participants, certifications, or votes will change the hash.
        
        Returns:
            SHA-256 hash of the graph structure
        """
        # Create canonical representation
        graph_dict = {
            "metadata": {
                "poll_id": self.metadata.poll_id,
                "question": self.metadata.question,
                "options": sorted(self.metadata.options),
                "num_participants": self.metadata.num_participants,
                "num_certifications": self.metadata.num_certifications,
                "num_votes": self.metadata.num_votes,
                "min_certifications_required": self.metadata.min_certifications_required
            },
            "participants": sorted([p.to_dict() for p in self.participants], 
                                  key=lambda x: x["user_id"]),
            "certifications": sorted([c.to_dict() for c in self.certifications],
                                    key=lambda x: (x["source"], x["target"])),
            "votes": sorted([v.to_dict() for v in self.votes],
                          key=lambda x: x["user_id"])
        }
        
        # Compute hash
        canonical_json = json.dumps(graph_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode()).hexdigest()
    
    def verify_hash(self) -> bool:
        """
        Verify that the stored hash matches the computed hash.
        
        Returns:
            True if hash is valid
        """
        if self.graph_hash is None:
            return False
        computed = self.compute_hash()
        return computed == self.graph_hash
    
    def get_vote_tally(self) -> Dict[str, int]:
        """
        Compute vote tally from the votes in the graph.
        
        Returns:
            Dictionary mapping options to vote counts
        """
        tally = {option: 0 for option in self.metadata.options}
        for vote in self.votes:
            if vote.option in tally:
                tally[vote.option] += 1
        return tally
    
    def to_exportable_dict(self) -> Dict[str, Any]:
        """
        Convert proof graph to a dictionary suitable for export/download.
        
        Returns:
            Complete graph as dictionary
        """
        return {
            "metadata": self.metadata.model_dump(),
            "participants": [p.model_dump() for p in self.participants],
            "certifications": [c.model_dump() for c in self.certifications],
            "votes": [v.model_dump() for v in self.votes],
            "graph_hash": self.graph_hash,
            "vote_tally": self.get_vote_tally()
        }


class ProofGraphSummary(BaseModel):
    """
    Summary view of a proof graph for quick display.
    """
    poll_id: str
    question: str
    total_participants: int
    total_certifications: int
    total_votes: int
    vote_tally: Dict[str, int]
    graph_hash: str
    is_valid: bool
    verification_message: str