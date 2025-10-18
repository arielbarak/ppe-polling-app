"""
Tests for proof graph construction and verification.
"""

import pytest
from app.models.proof_graph import (
    ProofGraph,
    GraphMetadata,
    ParticipantNode,
    PPECertificationEdge,
    VoteRecord
)
from app.services.proof_graph_service import ProofGraphService
from app.models.poll import Poll, PollCreate


@pytest.fixture
def sample_poll():
    """Create a sample poll with data."""
    poll = Poll(
        id="test-poll-1",
        question="Test Question",
        options=["Option A", "Option B"]
    )
    
    # Add registrants
    poll.registrants = {
        "user1": {"kty": "EC", "x": "x1", "y": "y1"},
        "user2": {"kty": "EC", "x": "x2", "y": "y2"},
        "user3": {"kty": "EC", "x": "x3", "y": "y3"}
    }
    
    # Add PPE certifications
    poll.ppe_certifications = {
        "user1": {"user2", "user3"},
        "user2": {"user1", "user3"},
        "user3": {"user1", "user2"}
    }
    
    # Add votes
    from app.models.poll import Vote
    poll.votes = {
        "user1": Vote(
            publicKey={"kty": "EC", "x": "x1", "y": "y1"},
            option="Option A",
            signature="sig1"
        ),
        "user2": Vote(
            publicKey={"kty": "EC", "x": "x2", "y": "y2"},
            option="Option B",
            signature="sig2"
        )
    }
    
    return poll


def test_proof_graph_construction(sample_poll):
    """Test basic proof graph construction."""
    service = ProofGraphService()
    proof_graph = service.construct_proof_graph(sample_poll)
    
    assert proof_graph.metadata.poll_id == "test-poll-1"
    assert proof_graph.metadata.num_participants == 3
    assert proof_graph.metadata.num_certifications == 3  # 3 edges in complete graph
    assert proof_graph.metadata.num_votes == 2
    assert len(proof_graph.participants) == 3
    assert len(proof_graph.certifications) == 3
    assert len(proof_graph.votes) == 2


def test_proof_graph_hash(sample_poll):
    """Test proof graph hash computation."""
    service = ProofGraphService()
    proof_graph = service.construct_proof_graph(sample_poll)
    
    # Hash should be computed
    assert proof_graph.graph_hash is not None
    assert len(proof_graph.graph_hash) == 64  # SHA-256 hex
    
    # Hash should verify
    assert proof_graph.verify_hash()


def test_proof_graph_hash_deterministic(sample_poll):
    """Test that hash is deterministic."""
    service = ProofGraphService()
    
    proof_graph1 = service.construct_proof_graph(sample_poll)
    proof_graph2 = service.construct_proof_graph(sample_poll)
    
    assert proof_graph1.graph_hash == proof_graph2.graph_hash


def test_proof_graph_hash_changes_with_data():
    """Test that hash changes when data changes."""
    service = ProofGraphService()
    
    # Create two polls with different data
    poll1 = Poll(
        id="test-poll-1",
        question="Question 1",
        options=["A", "B"]
    )
    poll1.registrants = {"user1": {"kty": "EC", "x": "x1", "y": "y1"}}
    
    poll2 = Poll(
        id="test-poll-2",
        question="Question 2",
        options=["A", "B"]
    )
    poll2.registrants = {"user2": {"kty": "EC", "x": "x2", "y": "y2"}}
    
    graph1 = service.construct_proof_graph(poll1)
    graph2 = service.construct_proof_graph(poll2)
    
    assert graph1.graph_hash != graph2.graph_hash


def test_vote_tally(sample_poll):
    """Test vote tally computation."""
    service = ProofGraphService()
    proof_graph = service.construct_proof_graph(sample_poll)
    
    tally = proof_graph.get_vote_tally()
    
    assert tally["Option A"] == 1
    assert tally["Option B"] == 1


def test_exportable_dict(sample_poll):
    """Test exportable dictionary format."""
    service = ProofGraphService()
    proof_graph = service.construct_proof_graph(sample_poll)
    
    export_dict = proof_graph.to_exportable_dict()
    
    assert "metadata" in export_dict
    assert "participants" in export_dict
    assert "certifications" in export_dict
    assert "votes" in export_dict
    assert "graph_hash" in export_dict
    assert "vote_tally" in export_dict


def test_proof_graph_caching(sample_poll):
    """Test proof graph caching."""
    service = ProofGraphService()
    
    # First construction
    graph1 = service.get_or_construct_proof_graph(sample_poll)
    
    # Second call should return cached
    graph2 = service.get_or_construct_proof_graph(sample_poll)
    
    assert graph1 is graph2  # Same object


def test_proof_graph_invalidation(sample_poll):
    """Test cache invalidation."""
    service = ProofGraphService()
    
    # Construct and cache
    service.construct_proof_graph(sample_poll)
    
    # Invalidate
    service.invalidate_proof_graph(sample_poll.id)
    
    # Should not be cached
    cached = service.get_proof_graph(sample_poll.id)
    assert cached is None


def test_certification_edge_deduplication(sample_poll):
    """Test that certification edges are deduplicated properly."""
    service = ProofGraphService()
    proof_graph = service.construct_proof_graph(sample_poll)
    
    # Should have exactly 3 certifications (each edge only once)
    assert len(proof_graph.certifications) == 3
    
    # Check that edges are properly formatted
    edges = [(c.source_user_id, c.target_user_id) for c in proof_graph.certifications]
    
    # All edges should be alphabetically ordered (source < target)
    for source, target in edges:
        assert source < target
    
    # Should contain all expected edges
    expected_edges = {("user1", "user2"), ("user1", "user3"), ("user2", "user3")}
    actual_edges = set(edges)
    assert actual_edges == expected_edges


def test_participant_nodes(sample_poll):
    """Test participant node creation."""
    service = ProofGraphService()
    proof_graph = service.construct_proof_graph(sample_poll)
    
    # Should have all participants
    user_ids = {p.user_id for p in proof_graph.participants}
    expected_ids = {"user1", "user2", "user3"}
    assert user_ids == expected_ids
    
    # Each participant should have public key
    for participant in proof_graph.participants:
        assert "kty" in participant.public_key
        assert participant.public_key["kty"] == "EC"


def test_vote_records(sample_poll):
    """Test vote record creation."""
    service = ProofGraphService()
    proof_graph = service.construct_proof_graph(sample_poll)
    
    # Should have all votes
    voter_ids = {v.user_id for v in proof_graph.votes}
    expected_ids = {"user1", "user2"}
    assert voter_ids == expected_ids
    
    # Each vote should have proper structure
    for vote in proof_graph.votes:
        assert vote.option in ["Option A", "Option B"]
        assert vote.signature.startswith("sig")
        assert "kty" in vote.public_key


def test_metadata_accuracy(sample_poll):
    """Test that metadata accurately reflects the poll data."""
    service = ProofGraphService()
    proof_graph = service.construct_proof_graph(sample_poll)
    
    metadata = proof_graph.metadata
    
    assert metadata.poll_id == sample_poll.id
    assert metadata.question == sample_poll.question
    assert set(metadata.options) == set(sample_poll.options)
    assert metadata.num_participants == len(sample_poll.registrants)
    assert metadata.num_votes == len(sample_poll.votes)
    assert metadata.min_certifications_required == 2


def test_hash_with_no_data():
    """Test hash computation with minimal data."""
    poll = Poll(id="empty-poll", question="Empty?", options=["Yes", "No"])
    
    service = ProofGraphService()
    proof_graph = service.construct_proof_graph(poll)
    
    # Should still compute hash
    assert proof_graph.graph_hash is not None
    assert proof_graph.verify_hash()
    
    # Should have empty collections
    assert len(proof_graph.participants) == 0
    assert len(proof_graph.certifications) == 0
    assert len(proof_graph.votes) == 0


def test_proof_graph_with_dict_votes():
    """Test proof graph construction with dict-format votes."""
    poll = Poll(
        id="dict-vote-poll",
        question="Test Question",
        options=["A", "B"]
    )
    
    poll.registrants = {
        "user1": {"kty": "EC", "x": "x1", "y": "y1"}
    }
    
    # Add vote as dictionary (not Vote object)
    poll.votes = {
        "user1": {
            "publicKey": {"kty": "EC", "x": "x1", "y": "y1"},
            "option": "A",
            "signature": "dict-sig"
        }
    }
    
    service = ProofGraphService()
    proof_graph = service.construct_proof_graph(poll)
    
    # Should handle dict format
    assert len(proof_graph.votes) == 1
    vote = proof_graph.votes[0]
    assert vote.user_id == "user1"
    assert vote.option == "A"
    assert vote.signature == "dict-sig"


def test_canonical_hash_ordering():
    """Test that hash is canonical regardless of insertion order."""
    service = ProofGraphService()
    
    # Create poll with data in one order
    poll1 = Poll(id="order-test", question="Test", options=["B", "A"])  # Reversed options
    poll1.registrants = {
        "user2": {"kty": "EC", "x": "x2", "y": "y2"},
        "user1": {"kty": "EC", "x": "x1", "y": "y1"}  # Reversed order
    }
    poll1.ppe_certifications = {
        "user2": {"user1"},
        "user1": {"user2"}
    }
    
    # Create equivalent poll with different order
    poll2 = Poll(id="order-test", question="Test", options=["A", "B"])  # Normal order
    poll2.registrants = {
        "user1": {"kty": "EC", "x": "x1", "y": "y1"},
        "user2": {"kty": "EC", "x": "x2", "y": "y2"}  # Normal order
    }
    poll2.ppe_certifications = {
        "user1": {"user2"},
        "user2": {"user1"}
    }
    
    graph1 = service.construct_proof_graph(poll1)
    graph2 = service.construct_proof_graph(poll2)
    
    # Should have same hash due to canonical ordering
    assert graph1.graph_hash == graph2.graph_hash