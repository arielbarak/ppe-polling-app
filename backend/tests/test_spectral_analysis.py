"""
Tests for spectral analysis of certification graphs.
"""

import pytest
import networkx as nx
import numpy as np

from app.services.spectral_analysis import SpectralAnalyzer


class TestSpectralAnalyzer:
    
    @pytest.fixture
    def path_graph(self):
        """Create a path graph (poor expansion)."""
        G = nx.path_graph(10)
        return G
    
    @pytest.fixture
    def complete_graph(self):
        """Create a complete graph (excellent expansion)."""
        G = nx.complete_graph(10)
        return G
    
    @pytest.fixture
    def cycle_graph(self):
        """Create a cycle graph (known eigenvalues)."""
        G = nx.cycle_graph(8)
        return G
    
    def test_analyzer_initialization(self, complete_graph):
        """Test analyzer initializes correctly."""
        analyzer = SpectralAnalyzer(complete_graph)
        assert analyzer.m == 10
        assert analyzer.graph == complete_graph
    
    def test_spectral_gap_complete_graph(self, complete_graph):
        """Test spectral gap on complete graph."""
        analyzer = SpectralAnalyzer(complete_graph)
        
        result = analyzer.compute_spectral_gap(threshold=5.0)
        
        # Complete graph K_n has λ₂ = n (excellent connectivity)
        assert result.lambda_2 >= 9.5  # Should be close to 10
        assert result.algebraic_connectivity == result.lambda_2
        assert result.satisfies_threshold
        assert result.computation_time_ms > 0
    
    def test_spectral_gap_path_graph(self, path_graph):
        """Test spectral gap on path graph."""
        analyzer = SpectralAnalyzer(path_graph)
        
        result = analyzer.compute_spectral_gap(threshold=1.0)
        
        # Path graph has small λ₂ (poor connectivity)
        assert 0 < result.lambda_2 < 1.0
        assert not result.satisfies_threshold  # Below threshold
        assert result.computation_time_ms > 0
    
    def test_spectral_gap_cycle_graph(self, cycle_graph):
        """Test spectral gap on cycle graph with known eigenvalues."""
        analyzer = SpectralAnalyzer(cycle_graph)
        
        result = analyzer.compute_spectral_gap()
        
        # Cycle graph C_8 has known eigenvalues
        # λ₂ = 2 - 2*cos(2π/8) = 2 - 2*cos(π/4) ≈ 0.586
        expected_lambda_2 = 2 - 2 * np.cos(2 * np.pi / 8)
        
        assert abs(result.lambda_2 - expected_lambda_2) < 0.1
        assert result.computation_time_ms > 0
    
    def test_sparse_vs_dense_methods(self, complete_graph):
        """Test sparse vs dense spectral gap computation."""
        analyzer = SpectralAnalyzer(complete_graph)
        
        # Test sparse method
        result_sparse = analyzer.compute_spectral_gap(method='sparse')
        
        # Test dense method  
        result_dense = analyzer.compute_spectral_gap(method='dense')
        
        # Results should be very close
        assert abs(result_sparse.lambda_2 - result_dense.lambda_2) < 0.01
        assert result_sparse.satisfies_threshold == result_dense.satisfies_threshold
    
    def test_empty_graph(self):
        """Test analyzer handles empty graph."""
        G = nx.Graph()
        analyzer = SpectralAnalyzer(G)
        
        result = analyzer.compute_spectral_gap()
        
        assert result.lambda_2 == 0.0
        assert result.algebraic_connectivity == 0.0
        assert not result.satisfies_threshold
        assert result.computation_time_ms >= 0
    
    def test_single_node_graph(self):
        """Test analyzer handles single node."""
        G = nx.Graph()
        G.add_node(0)
        analyzer = SpectralAnalyzer(G)
        
        result = analyzer.compute_spectral_gap()
        
        assert result.lambda_2 == 0.0
        assert not result.satisfies_threshold
    
    def test_disconnected_graph(self):
        """Test analyzer handles disconnected graph."""
        # Two separate triangles
        G1 = nx.complete_graph(3)
        G2 = nx.complete_graph(3)
        G = nx.disjoint_union(G1, G2)
        
        analyzer = SpectralAnalyzer(G)
        result = analyzer.compute_spectral_gap()
        
        # Disconnected graph has λ₂ = 0
        assert result.lambda_2 < 0.001  # Should be very close to 0
        assert not result.satisfies_threshold
    
    def test_compute_all_eigenvalues(self, cycle_graph):
        """Test computing multiple eigenvalues."""
        analyzer = SpectralAnalyzer(cycle_graph)
        
        eigenvalues = analyzer.compute_all_eigenvalues(k=5)
        
        assert len(eigenvalues) == 5
        assert eigenvalues[0] < 0.001  # First eigenvalue should be ~0
        assert eigenvalues[1] > eigenvalues[0]  # Eigenvalues should be sorted
        assert all(eigenvalues[i] >= eigenvalues[i-1] for i in range(1, len(eigenvalues)))
    
    def test_large_graph_performance(self):
        """Test performance on larger graph."""
        # Create larger random graph
        G = nx.erdos_renyi_graph(n=200, p=0.1, seed=42)
        analyzer = SpectralAnalyzer(G)
        
        result = analyzer.compute_spectral_gap(method='sparse')
        
        # Should complete reasonably quickly
        assert result.computation_time_ms < 5000  # Less than 5 seconds
        assert result.lambda_2 >= 0
    
    def test_error_handling(self):
        """Test error handling in spectral computation."""
        # Create a graph that might cause numerical issues
        G = nx.Graph()
        G.add_nodes_from(range(5))
        # Add only one edge (nearly disconnected)
        G.add_edge(0, 1)
        
        analyzer = SpectralAnalyzer(G)
        
        # Should not crash, even with difficult graph
        result = analyzer.compute_spectral_gap()
        
        assert isinstance(result.lambda_2, float)
        assert result.computation_time_ms >= 0


@pytest.mark.integration
class TestSpectralAnalysisIntegration:
    
    def test_real_world_graph_properties(self):
        """Test spectral properties on realistic PPE certification graphs."""
        # Simulate a realistic PPE certification graph
        n_participants = 100
        avg_degree = 12
        
        # Use random regular graph as baseline
        G = nx.random_regular_graph(d=avg_degree, n=n_participants, seed=42)
        
        analyzer = SpectralAnalyzer(G)
        result = analyzer.compute_spectral_gap()
        
        print(f"\nRealistic Graph Spectral Analysis:")
        print(f"  Nodes: {n_participants}")
        print(f"  Average degree: {avg_degree}")
        print(f"  λ₂: {result.lambda_2:.4f}")
        print(f"  Computation time: {result.computation_time_ms:.2f}ms")
        
        # Regular graphs typically have good spectral gaps
        assert result.lambda_2 > 0.1
        assert result.satisfies_threshold
        
    def test_expansion_correlation(self):
        """Test correlation between spectral gap and expansion."""
        graphs = {
            "poor_expansion": nx.path_graph(20),
            "medium_expansion": nx.cycle_graph(20),
            "good_expansion": nx.random_regular_graph(d=6, n=20, seed=42)
        }
        
        lambda_2_values = {}
        
        for name, graph in graphs.items():
            analyzer = SpectralAnalyzer(graph)
            result = analyzer.compute_spectral_gap()
            lambda_2_values[name] = result.lambda_2
            print(f"{name}: λ₂ = {result.lambda_2:.4f}")
        
        # Better expansion should correlate with larger λ₂
        assert lambda_2_values["poor_expansion"] < lambda_2_values["medium_expansion"]
        assert lambda_2_values["medium_expansion"] < lambda_2_values["good_expansion"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])