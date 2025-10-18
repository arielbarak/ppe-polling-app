"""
Service for constructing and managing proof graphs.
"""

from typing import Optional
from datetime import datetime
from ..models.proof_graph import (
    ProofGraph,
    GraphMetadata,
    ParticipantNode,
    PPECertificationEdge,
    VoteRecord,
    ProofGraphSummary
)
from ..models.poll import Poll


class ProofGraphService:
    """
    Service for building and managing proof graphs.
    """
    
    def __init__(self):
        # Cache of constructed proof graphs: {poll_id: ProofGraph}
        self._proof_graphs = {}
    
    def construct_proof_graph(self, poll: Poll) -> ProofGraph:
        """
        Construct a complete proof graph from a poll.
        
        This is the main function that builds Protocol 5's proof graph.
        
        Args:
            poll: The poll object with all data
            
        Returns:
            Complete ProofGraph object
        """
        # Build metadata
        metadata = GraphMetadata(
            poll_id=poll.id,
            question=poll.question,
            options=poll.options,
            num_participants=len(poll.registrants),
            num_certifications=sum(len(certs) for certs in poll.ppe_certifications.values()) // 2,
            num_votes=len(poll.votes),
            min_certifications_required=2,
            created_at=datetime.now().isoformat()
        )
        
        # Build participant nodes
        participants = []
        for user_id, public_key in poll.registrants.items():
            participants.append(ParticipantNode(
                user_id=user_id,
                public_key=public_key
            ))
        
        # Build certification edges (undirected, so only add each edge once)
        certifications = []
        processed_edges = set()
        
        for user_id, certified_peers in poll.ppe_certifications.items():
            for peer_id in certified_peers:
                # Create edge identifier (sorted to avoid duplicates)
                edge_id = tuple(sorted([user_id, peer_id]))
                
                if edge_id not in processed_edges:
                    certifications.append(PPECertificationEdge(
                        source_user_id=edge_id[0],
                        target_user_id=edge_id[1],
                        certification_type="ppe"
                    ))
                    processed_edges.add(edge_id)
        
        # Build vote records
        votes = []
        for user_id, vote_data in poll.votes.items():
            # Handle both dict and Vote object formats
            if isinstance(vote_data, dict):
                public_key = vote_data.get("publicKey", poll.registrants.get(user_id, {}))
                option = vote_data.get("option", "")
                signature = vote_data.get("signature", "")
            else:
                public_key = vote_data.publicKey
                option = vote_data.option
                signature = vote_data.signature
            
            votes.append(VoteRecord(
                user_id=user_id,
                public_key=public_key,
                option=option,
                signature=signature
            ))
        
        # Construct proof graph
        proof_graph = ProofGraph(
            metadata=metadata,
            participants=participants,
            certifications=certifications,
            votes=votes
        )
        
        # Compute and set hash
        proof_graph.graph_hash = proof_graph.compute_hash()
        
        # Cache the proof graph
        self._proof_graphs[poll.id] = proof_graph
        
        return proof_graph
    
    def get_proof_graph(self, poll_id: str) -> Optional[ProofGraph]:
        """
        Get a cached proof graph.
        
        Args:
            poll_id: Poll identifier
            
        Returns:
            ProofGraph if cached, None otherwise
        """
        return self._proof_graphs.get(poll_id)
    
    def get_or_construct_proof_graph(self, poll: Poll) -> ProofGraph:
        """
        Get cached proof graph or construct new one.
        
        Args:
            poll: Poll object
            
        Returns:
            ProofGraph
        """
        cached = self.get_proof_graph(poll.id)
        if cached:
            # Verify it's still valid (same number of votes)
            if cached.metadata.num_votes == len(poll.votes):
                return cached
        
        # Construct new proof graph
        return self.construct_proof_graph(poll)
    
    def invalidate_proof_graph(self, poll_id: str):
        """
        Invalidate cached proof graph.
        
        Should be called when poll data changes.
        
        Args:
            poll_id: Poll identifier
        """
        if poll_id in self._proof_graphs:
            del self._proof_graphs[poll_id]
    
    def create_summary(self, proof_graph: ProofGraph, 
                      verification_result: dict) -> ProofGraphSummary:
        """
        Create a summary view of a proof graph.
        
        Args:
            proof_graph: The complete proof graph
            verification_result: Result from verification
            
        Returns:
            ProofGraphSummary
        """
        return ProofGraphSummary(
            poll_id=proof_graph.metadata.poll_id,
            question=proof_graph.metadata.question,
            total_participants=proof_graph.metadata.num_participants,
            total_certifications=proof_graph.metadata.num_certifications,
            total_votes=proof_graph.metadata.num_votes,
            vote_tally=proof_graph.get_vote_tally(),
            graph_hash=proof_graph.graph_hash,
            is_valid=verification_result.get("is_valid", False),
            verification_message=verification_result.get("verification_message", "")
        )


# Singleton instance
proof_graph_service = ProofGraphService()