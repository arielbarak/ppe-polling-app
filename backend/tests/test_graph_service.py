"""
Tests for graph service.
"""

import pytest
from app.services.graph_service import GraphService


@pytest.fixture
def graph_service():
    """Create a fresh graph service instance."""
    return GraphService()


def test_get_or_generate_graph(graph_service):
    """Test graph generation and caching."""
    poll_id = "test-poll-1"
    participants = ["user1", "user2", "user3", "user4", "user5"]
    
    # Generate graph
    graph1 = graph_service.get_or_generate_graph(poll_id, participants, k=2)
    
    assert len(graph1) == 5
    
    # Get cached graph
    graph2 = graph_service.get_or_generate_graph(poll_id, participants, k=2)
    
    # Should be same object (cached)
    assert graph1 is graph2


def test_get_user_neighbors(graph_service):
    """Test retrieving user neighbors."""
    poll_id = "test-poll-2"
    participants = ["user1", "user2", "user3", "user4"]
    
    graph_service.get_or_generate_graph(poll_id, participants, k=2)
    
    neighbors = graph_service.get_user_neighbors(poll_id, "user1")
    
    assert isinstance(neighbors, set)
    assert len(neighbors) >= 1  # Should have at least one neighbor


def test_get_graph_properties(graph_service):
    """Test retrieving graph properties."""
    poll_id = "test-poll-3"
    participants = ["user1", "user2", "user3"]
    
    graph_service.get_or_generate_graph(poll_id, participants, k=2)
    
    props = graph_service.get_graph_properties(poll_id)
    
    assert "is_valid" in props
    assert "is_connected" in props
    assert "num_nodes" in props
    assert props["num_nodes"] == 3


def test_invalidate_graph(graph_service):
    """Test graph cache invalidation."""
    poll_id = "test-poll-4"
    participants = ["user1", "user2", "user3"]
    
    # Generate graph
    graph_service.get_or_generate_graph(poll_id, participants, k=2)
    
    # Invalidate
    graph_service.invalidate_graph(poll_id)
    
    # Graph should not be in cache
    graph = graph_service.get_full_graph(poll_id)
    assert graph is None


def test_get_graph_metrics(graph_service):
    """Test retrieving graph metrics."""
    poll_id = "test-poll-5"
    participants = ["user1", "user2", "user3", "user4", "user5"]
    
    graph_service.get_or_generate_graph(poll_id, participants, k=2)
    
    metrics = graph_service.get_graph_metrics(poll_id)
    
    assert "num_nodes" in metrics
    assert "num_edges" in metrics
    assert "density" in metrics