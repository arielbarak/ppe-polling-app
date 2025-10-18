"""
Unit tests for graph expansion calculations.
"""

import pytest
import networkx as nx
import numpy as np

from app.services.graph_expansion import (
    GraphExpansionAnalyzer,
    build_lse_parameters_from_graph
)
from app.models.graph_metrics import LSEParameters


class TestGraphExpansionAnalyzer:
    
    @pytest.fixture
    def small_expander_graph(self):
        """Create a small expander graph for testing."""
        # Create a random regular graph (good expander)
        G = nx.random_regular_graph(d=4, n=20, seed=42)
        
        # Add honest/deleted attributes
        for node in G.nodes():
            G.nodes[node]['honest'] = True
            G.nodes[node]['deleted'] = False
        
        return G
    
    @pytest.fixture
    def poor_expander_graph(self):
        """Create a graph with poor expansion (two clusters)."""
        # Two separate cliques connected by single edge
        G1 = nx.complete_graph(10)
        G2 = nx.complete_graph(10)
        G = nx.disjoint_union(G1, G2)
        G.add_edge(0, 10)  # Connect the two clusters
        
        for node in G.nodes():
            G.nodes[node]['honest'] = True
            G.nodes[node]['deleted'] = False
        
        return G
    
    def test_analyzer_initialization(self, small_expander_graph):
        """Test analyzer initializes correctly."""
        analyzer = GraphExpansionAnalyzer(small_expander_graph)
        
        assert analyzer.m == 20
        assert analyzer.n == 20  # All honest
        assert analyzer.rho == 0  # None deleted
        assert analyzer.n_edges == 40  # 4-regular on 20 nodes
    
    def test_vertex_expansion_good_graph(self, small_expander_graph):
        """Test vertex expansion on good expander."""
        analyzer = GraphExpansionAnalyzer(small_expander_graph)
        
        result = analyzer.compute_vertex_expansion(
            K=5,
            rho=2,
            threshold=0.8,  # Lower threshold for small graph
            sample_size=50
        )
        
        assert result.expansion_ratio >= 0.5  # More realistic for small graph
        assert result.subset_size >= 5
    
    def test_vertex_expansion_poor_graph(self, poor_expander_graph):
        """Test vertex expansion on poor expander."""
        analyzer = GraphExpansionAnalyzer(poor_expander_graph)
        
        result = analyzer.compute_vertex_expansion(
            K=5,
            rho=2,
            threshold=2.0,  # Higher threshold
            sample_size=100
        )
        
        # Poor expander should have low expansion for some sets
        # (specifically, sets contained in one cluster)
        assert result.expansion_ratio < 2.0 or not result.satisfies_threshold
    
    def test_edge_expansion(self, small_expander_graph):
        """Test edge expansion (conductance)."""
        analyzer = GraphExpansionAnalyzer(small_expander_graph)
        
        result = analyzer.compute_edge_expansion(
            K=5,
            rho=2,
            threshold=0.2,
            sample_size=50
        )
        
        assert result.conductance >= 0.0
        assert result.crossing_edges >= 0
        assert isinstance(result.satisfies_threshold, bool)
    
    def test_lse_property_verification(self, small_expander_graph):
        """Test LSE property verification."""
        analyzer = GraphExpansionAnalyzer(small_expander_graph)
        
        lse_params = LSEParameters(K=5, rho=2, q=0.1)
        
        is_lse = analyzer.verify_lse_property(lse_params, sample_size=50)
        
        assert isinstance(is_lse, bool)
        # Good expander should satisfy LSE with reasonable params
        assert is_lse
    
    def test_minimum_degree(self, small_expander_graph):
        """Test minimum degree calculation."""
        analyzer = GraphExpansionAnalyzer(small_expander_graph)
        
        result = analyzer.compute_minimum_degree(required_min=2)
        
        assert result.minimum_degree == 4  # 4-regular graph
        assert result.satisfies_requirement
        assert len(result.nodes_below_threshold) == 0
    
    def test_average_degree(self, small_expander_graph):
        """Test average degree calculation."""
        analyzer = GraphExpansionAnalyzer(small_expander_graph)
        
        avg_degree = analyzer.compute_average_degree()
        
        assert avg_degree == 4.0  # 4-regular graph


class TestLSEParameterBuilder:
    
    def test_build_lse_parameters(self):
        """Test LSE parameter construction from graph."""
        G = nx.random_regular_graph(d=6, n=100, seed=42)
        
        lse_params = build_lse_parameters_from_graph(
            G,
            security_param=40,
            eta_v=0.025
        )
        
        assert lse_params.K > 0
        assert lse_params.rho == int(0.025 * 100)  # ηVm
        assert 0 < lse_params.q < 1
    
    def test_lse_parameters_scale_with_graph(self):
        """Test LSE parameters scale appropriately."""
        G_small = nx.random_regular_graph(d=4, n=50, seed=42)
        G_large = nx.random_regular_graph(d=4, n=500, seed=42)
        
        params_small = build_lse_parameters_from_graph(G_small)
        params_large = build_lse_parameters_from_graph(G_large)
        
        # K should be larger for larger graph
        assert params_large.K > params_small.K
        assert params_large.rho > params_small.rho


@pytest.mark.integration
class TestGraphExpansionIntegration:
    
    def test_complete_workflow(self):
        """Test complete expansion analysis workflow."""
        # Create realistic certification graph
        n_participants = 100
        d_avg = 8
        
        # Random regular graph approximates PPE certification graph
        G = nx.random_regular_graph(d=d_avg, n=n_participants, seed=42)
        
        # Mark some nodes as deleted
        for node in list(G.nodes())[:5]:
            G.nodes[node]['deleted'] = True
            G.nodes[node]['honest'] = True
        
        for node in list(G.nodes())[5:]:
            G.nodes[node]['deleted'] = False
            G.nodes[node]['honest'] = True
        
        # Analyze
        analyzer = GraphExpansionAnalyzer(G)
        lse_params = build_lse_parameters_from_graph(G)
        
        # Compute all metrics
        vertex_exp = analyzer.compute_vertex_expansion(
            lse_params.K, lse_params.rho
        )
        edge_exp = analyzer.compute_edge_expansion(
            lse_params.K, lse_params.rho
        )
        is_lse = analyzer.verify_lse_property(lse_params)
        min_deg = analyzer.compute_minimum_degree()
        
        # Verify results are reasonable
        assert vertex_exp.expansion_ratio > 0
        assert edge_exp.conductance > 0
        assert isinstance(is_lse, bool)
        assert min_deg.minimum_degree > 0
        
        print(f"\nIntegration Test Results:")
        print(f"  Vertex expansion: {vertex_exp.expansion_ratio:.3f}")
        print(f"  Edge expansion: {edge_exp.conductance:.3f}")
        print(f"  Is LSE: {is_lse}")
        print(f"  Min degree: {min_deg.minimum_degree}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])