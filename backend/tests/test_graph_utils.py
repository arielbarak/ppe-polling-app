"""
Tests for graph utility functions.
"""

import pytest
from app.utils.graph_utils import (
    generate_seed_from_poll_id,
    generate_random_regular_graph,
    generate_ideal_graph,
    validate_graph_properties,
    get_user_neighbors,
    calculate_graph_metrics
)


def test_generate_seed_deterministic():
    """Test that seed generation is deterministic."""
    poll_id = "test-poll-123"
    seed1 = generate_seed_from_poll_id(poll_id)
    seed2 = generate_seed_from_poll_id(poll_id)
    assert seed1 == seed2


def test_generate_seed_different_for_different_polls():
    """Test that different polls get different seeds."""
    seed1 = generate_seed_from_poll_id("poll-1")
    seed2 = generate_seed_from_poll_id("poll-2")
    assert seed1 != seed2


def test_generate_random_regular_graph_basic():
    """Test basic random regular graph generation."""
    n = 6
    k = 3
    seed = 12345
    
    graph = generate_random_regular_graph(n, k, seed)
    
    # Check all nodes present
    assert len(graph) == n
    
    # Check degree of each node
    for node, neighbors in graph.items():
        assert len(neighbors) == k, f"Node {node} has degree {len(neighbors)}, expected {k}"
    
    # Check symmetry
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            assert node in graph[neighbor], f"Graph not symmetric: {node} -> {neighbor}"


def test_generate_random_regular_graph_deterministic():
    """Test that graph generation is deterministic given same seed."""
    n = 10
    k = 3
    seed = 54321
    
    graph1 = generate_random_regular_graph(n, k, seed)
    graph2 = generate_random_regular_graph(n, k, seed)
    
    assert graph1 == graph2


def test_generate_random_regular_graph_edge_cases():
    """Test edge cases for graph generation."""
    # Too few nodes
    graph = generate_random_regular_graph(1, 0, 123)
    assert graph == {}  # The function returns {} for n < 2
    
    # k too large should raise error
    with pytest.raises(ValueError):
        generate_random_regular_graph(5, 5, 123)


def test_generate_ideal_graph():
    """Test ideal graph generation with user IDs."""
    participants = ["user1", "user2", "user3", "user4", "user5", "user6"]
    poll_id = "test-poll"
    k = 2
    
    graph = generate_ideal_graph(participants, poll_id, k)
    
    # Check all participants in graph
    assert set(graph.keys()) == set(participants)
    
    # Check degrees
    for user, neighbors in graph.items():
        assert len(neighbors) <= k + 1  # Allow some flexibility


def test_generate_ideal_graph_empty():
    """Test ideal graph with no participants."""
    graph = generate_ideal_graph([], "poll-id", 3)
    assert graph == {}


def test_generate_ideal_graph_single_participant():
    """Test ideal graph with single participant."""
    graph = generate_ideal_graph(["user1"], "poll-id", 3)
    assert graph == {"user1": set()}


def test_generate_ideal_graph_two_participants():
    """Test ideal graph with two participants."""
    graph = generate_ideal_graph(["user1", "user2"], "poll-id", 3)
    assert len(graph) == 2
    assert "user2" in graph["user1"]
    assert "user1" in graph["user2"]


def test_validate_graph_properties():
    """Test graph property validation."""
    # Valid symmetric graph
    graph = {
        "A": {"B", "C"},
        "B": {"A", "C"},
        "C": {"A", "B"}
    }
    
    props = validate_graph_properties(graph)
    
    assert props["is_valid"] is True
    assert props["is_symmetric"] is True
    assert props["is_connected"] is True
    assert props["num_nodes"] == 3
    assert props["num_edges"] == 3
    assert props["min_degree"] == 2
    assert props["max_degree"] == 2


def test_validate_graph_properties_asymmetric():
    """Test detection of asymmetric graph."""
    # Asymmetric graph
    graph = {
        "A": {"B"},
        "B": {"C"},
        "C": set()
    }
    
    props = validate_graph_properties(graph)
    assert props["is_symmetric"] is False


def test_validate_graph_properties_disconnected():
    """Test detection of disconnected graph."""
    graph = {
        "A": {"B"},
        "B": {"A"},
        "C": {"D"},
        "D": {"C"}
    }
    
    props = validate_graph_properties(graph)
    assert props["is_connected"] is False


def test_get_user_neighbors():
    """Test retrieving user neighbors."""
    graph = {
        "user1": {"user2", "user3"},
        "user2": {"user1"},
        "user3": {"user1"}
    }
    
    neighbors = get_user_neighbors(graph, "user1")
    assert neighbors == {"user2", "user3"}
    
    # Non-existent user
    neighbors = get_user_neighbors(graph, "user999")
    assert neighbors == set()


def test_calculate_graph_metrics():
    """Test graph metrics calculation."""
    graph = {
        "A": {"B", "C"},
        "B": {"A", "C", "D"},
        "C": {"A", "B", "D"},
        "D": {"B", "C"}
    }
    
    metrics = calculate_graph_metrics(graph)
    
    assert metrics["num_nodes"] == 4
    assert metrics["num_edges"] == 5
    assert "density" in metrics
    assert "avg_clustering" in metrics