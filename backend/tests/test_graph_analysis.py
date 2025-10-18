"""
Tests for graph analysis utilities.
"""

import pytest
import networkx as nx
from app.utils.graph_analysis import (
    build_networkx_graph,
    calculate_conductance,
    calculate_edge_expansion,
    detect_low_conductance_clusters,
    analyze_degree_distribution,
    detect_isolated_components,
    calculate_clustering_coefficient
)


def test_build_networkx_graph():
    """Test graph construction."""
    adj_list = {
        "A": {"B", "C"},
        "B": {"A", "C"},
        "C": {"A", "B"}
    }
    
    G = build_networkx_graph(adj_list)
    
    assert len(G.nodes()) == 3
    assert len(G.edges()) == 3


def test_calculate_conductance():
    """Test conductance calculation."""
    # Complete graph
    G = nx.complete_graph(4)
    
    # Conductance of half should be 1.0 (perfect cut)
    subset = {0, 1}
    conductance = calculate_conductance(G, subset)
    
    assert conductance > 0


def test_calculate_edge_expansion():
    """Test edge expansion calculation."""
    G = nx.complete_graph(4)
    
    subset = {0, 1}
    expansion = calculate_edge_expansion(G, subset)
    
    assert expansion > 0


def test_analyze_degree_distribution():
    """Test degree distribution analysis."""
    G = nx.complete_graph(5)
    
    stats = analyze_degree_distribution(G)
    
    assert stats["min"] == 4  # Complete graph, all nodes degree 4
    assert stats["max"] == 4
    assert stats["mean"] == 4


def test_detect_isolated_components():
    """Test isolated component detection."""
    # Create graph with isolated component
    G = nx.Graph()
    G.add_edges_from([(1, 2), (2, 3), (3, 1)])  # Triangle
    G.add_edges_from([(4, 5)])  # Isolated pair
    
    isolated = detect_isolated_components(G, max_size=2)
    
    assert len(isolated) == 1
    assert len(list(isolated)[0]) == 2


def test_clustering_coefficient():
    """Test clustering coefficient calculation."""
    # Triangle has clustering 1.0
    G = nx.Graph()
    G.add_edges_from([(1, 2), (2, 3), (3, 1)])
    
    clustering = calculate_clustering_coefficient(G)
    
    assert clustering == 1.0