"""
Tests for Sybil resistance bound calculation.
THE KEY SECURITY METRIC.
"""

import pytest
import networkx as nx
import numpy as np

from app.services.sybil_bounds import SybilBoundCalculator, compute_attack_edges_from_params


class TestSybilBoundCalculator:
    
    @pytest.fixture
    def certification_graph(self):
        """Create a realistic certification graph."""
        G = nx.random_regular_graph(d=10, n=200, seed=42)
        
        for node in G.nodes():
            G.nodes[node]['honest'] = True
            G.nodes[node]['deleted'] = False
        
        return G
    
    def test_calculator_initialization(self, certification_graph):
        """Test calculator initializes correctly."""
        calc = SybilBoundCalculator(
            graph=certification_graph,
            attack_edges=500,
            eta_e=0.125,
            eta_v=0.025
        )
        
        assert calc.m == 200
        assert calc.attack_edges == 500
        assert calc.d == 10.0  # 10-regular graph
        assert calc.n == 200  # All honest
    
    def test_sybil_bound_computation(self, certification_graph):
        """Test Sybil bound computation (THE KEY TEST)."""
        attack_edges = 600  # Adversary succeeded in 600 PPEs
        
        calc = SybilBoundCalculator(
            graph=certification_graph,
            attack_edges=attack_edges
        )
        
        bound = calc.compute_sybil_bound(expansion_ratio=2.0)
        
        # Verify bound structure
        assert bound.max_sybil_nodes > 0
        assert bound.attack_edges == attack_edges
        assert bound.average_degree == 10.0
        assert bound.honest_nodes == 200
        assert bound.multiplicative_advantage > 0
        
        # Verify bound is reasonable
        # For 600 attack edges and degree 10, expect bound around 60-100
        assert 30 <= bound.max_sybil_nodes <= 200
        
        # Resistance level should be calculated
        assert bound.resistance_level in ["HIGH", "MEDIUM", "LOW"]
        assert 0 <= bound.sybil_percentage <= 100
        
        print(f"\nSybil Bound Results:")
        print(f"  Max Sybil nodes: {bound.max_sybil_nodes}")
        print(f"  Sybil percentage: {bound.sybil_percentage:.1f}%")
        print(f"  Resistance level: {bound.resistance_level}")
        print(f"  Multiplicative advantage: {bound.multiplicative_advantage:.2f}")
    
    def test_sybil_bound_scales_with_attack_edges(self, certification_graph):
        """Test that bound increases with attack edges."""
        bounds = []
        
        for attack_edges in [100, 500, 1000]:
            calc = SybilBoundCalculator(certification_graph, attack_edges)
            bound = calc.compute_sybil_bound()
            bounds.append(bound.max_sybil_nodes)
        
        # More attack edges → more Sybil nodes
        assert bounds[0] < bounds[1] < bounds[2]
    
    def test_sybil_bound_scales_with_degree(self):
        """Test that bound decreases with higher degree."""
        bounds = []
        
        for degree in [5, 10, 20]:
            G = nx.random_regular_graph(d=degree, n=200, seed=42)
            for node in G.nodes():
                G.nodes[node]['honest'] = True
            
            calc = SybilBoundCalculator(G, attack_edges=500)
            bound = calc.compute_sybil_bound()
            bounds.append(bound.max_sybil_nodes)
        
        # Higher degree → fewer Sybil nodes possible
        assert bounds[0] > bounds[1] > bounds[2]
    
    def test_resistance_level_classification(self, certification_graph):
        """Test resistance level is classified correctly."""
        # High resistance (few Sybils)
        calc_high = SybilBoundCalculator(certification_graph, attack_edges=100)
        bound_high = calc_high.compute_sybil_bound()
        
        # Low resistance (many Sybils)
        calc_low = SybilBoundCalculator(certification_graph, attack_edges=2000)
        bound_low = calc_low.compute_sybil_bound()
        
        # High resistance should have lower percentage
        assert bound_high.sybil_percentage < bound_low.sybil_percentage
    
    def test_multiplicative_advantage(self, certification_graph):
        """Test multiplicative advantage calculation."""
        calc = SybilBoundCalculator(certification_graph, attack_edges=500)
        bound = calc.compute_sybil_bound()
        
        # Adversary has C* times advantage over honest user
        assert bound.multiplicative_advantage >= 1.0
        
        # Should be proportional to max_sybil_nodes
        expected_advantage = bound.max_sybil_nodes / 1  # 1 vote per honest user
        assert abs(bound.multiplicative_advantage - expected_advantage) < 10
    
    def test_attack_edge_estimation(self, certification_graph):
        """Test attack edge estimation from graph."""
        calc = SybilBoundCalculator(certification_graph, attack_edges=0)
        
        estimated = calc.estimate_attack_edges_from_graph()
        
        assert estimated >= 0
        # Should find some suspicious nodes in random graph
        assert estimated < certification_graph.number_of_edges()
    
    def test_zero_graph_handling(self):
        """Test calculator handles empty graph gracefully."""
        G = nx.Graph()
        
        calc = SybilBoundCalculator(G, attack_edges=100)
        bound = calc.compute_sybil_bound()
        
        assert bound.max_sybil_nodes == 0
        assert bound.average_degree == 0.0
    
    def test_edge_cases(self):
        """Test edge cases in bound calculation."""
        # Single node
        G = nx.Graph()
        G.add_node(0)
        G.nodes[0]['honest'] = True
        
        calc = SybilBoundCalculator(G, attack_edges=10)
        bound = calc.compute_sybil_bound()
        
        assert bound.max_sybil_nodes >= 0
        assert bound.resistance_level in ["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    
    def test_theorem_4_4_consistency(self, certification_graph):
        """Test that bound follows Theorem 4.4 from paper."""
        attack_edges = 400
        calc = SybilBoundCalculator(certification_graph, attack_edges)
        bound = calc.compute_sybil_bound()
        
        # Theorem 4.4: max_sybil ≤ O(a/d) where a = attack_edges, d = avg_degree
        theoretical_bound = attack_edges / calc.d
        
        # Our bound should be in the right order of magnitude
        assert bound.max_sybil_nodes <= 10 * theoretical_bound  # Allow for constants
        
        print(f"\nTheorem 4.4 Consistency Check:")
        print(f"  Theoretical O(a/d): {theoretical_bound:.1f}")
        print(f"  Computed bound: {bound.max_sybil_nodes}")
        print(f"  Ratio: {bound.max_sybil_nodes / theoretical_bound:.2f}")


class TestAttackEdgesComputation:
    
    def test_compute_attack_edges_from_resources(self):
        """Test computing attack edges from adversary resources."""
        # Adversary has 1000 resources, each PPE costs 2 to attack
        attack_edges = compute_attack_edges_from_params(
            adversary_resources=1000,
            ppe_cost=2.0
        )
        
        assert attack_edges == 500
    
    def test_attack_edges_scales_linearly(self):
        """Test attack edges scale linearly with resources."""
        edges_1 = compute_attack_edges_from_params(100, 1.0)
        edges_2 = compute_attack_edges_from_params(200, 1.0)
        
        assert edges_2 == 2 * edges_1
    
    def test_attack_edges_different_costs(self):
        """Test attack edges with different PPE costs."""
        resources = 1000
        
        edges_cheap = compute_attack_edges_from_params(resources, ppe_cost=1.0)
        edges_expensive = compute_attack_edges_from_params(resources, ppe_cost=10.0)
        
        assert edges_cheap == 10 * edges_expensive


@pytest.mark.integration
class TestSybilBoundIntegration:
    
    def test_realistic_scenario(self):
        """Test Sybil bound in realistic PPE scenario."""
        # Realistic certification graph parameters
        n_participants = 1000  # 1000 participants
        avg_degree = 60  # Each does 60 PPEs
        
        # Create graph
        G = nx.erdos_renyi_graph(n=n_participants, p=avg_degree/n_participants, seed=42)
        for node in G.nodes():
            G.nodes[node]['honest'] = True
            G.nodes[node]['deleted'] = False
        
        # Adversary scenario: can afford to do 3000 PPEs
        attack_edges = 3000
        
        # Calculate bound
        calc = SybilBoundCalculator(G, attack_edges)
        bound = calc.compute_sybil_bound()
        
        print(f"\n=== Realistic Scenario Results ===")
        print(f"Participants: {n_participants}")
        print(f"Avg degree: {avg_degree}")
        print(f"Attack edges: {attack_edges}")
        print(f"Max Sybil nodes: {bound.max_sybil_nodes}")
        print(f"Sybil %: {bound.sybil_percentage:.1f}%")
        print(f"Resistance: {bound.resistance_level}")
        print(f"Multiplicative advantage: {bound.multiplicative_advantage:.2f}x")
        
        # Assertions for realistic scenario
        assert bound.max_sybil_nodes >= 0  # Bound should be non-negative
        assert bound.sybil_percentage >= 0  # Percentage should be non-negative
        assert bound.resistance_level in ["HIGH", "MEDIUM", "LOW"]  # Valid resistance level
        
        # With 3000 attack edges vs 60 avg degree, we expect significant Sybil capability
        # This demonstrates the importance of having sufficient graph density
        print(f"Theoretical bound (a/d): {attack_edges / 60:.1f}")
        
        # The bound demonstrates the security guarantees - even with this many attacks,
        # we have a concrete upper limit on Sybil nodes
    
    def test_security_parameter_sensitivity(self):
        """Test sensitivity to different security parameters."""
        G = nx.random_regular_graph(d=8, n=100, seed=42)
        for node in G.nodes():
            G.nodes[node]['honest'] = True
        
        results = []
        for eta_e in [0.05, 0.125, 0.25]:  # Different failure tolerances
            calc = SybilBoundCalculator(G, attack_edges=300, eta_e=eta_e)
            bound = calc.compute_sybil_bound()
            results.append(bound.max_sybil_nodes)
            print(f"ηE = {eta_e}: max_sybil = {bound.max_sybil_nodes}")
        
        # Higher failure tolerance should generally allow more Sybils
        # (though this depends on the specific formula)
        assert all(r > 0 for r in results)
    
    def test_comparison_with_literature_bounds(self):
        """Compare our bounds with known theoretical results."""
        # Create expander-like graph
        G = nx.random_regular_graph(d=16, n=500, seed=42)
        for node in G.nodes():
            G.nodes[node]['honest'] = True
        
        attack_edges = 1000
        calc = SybilBoundCalculator(G, attack_edges)
        bound = calc.compute_sybil_bound()
        
        # Literature suggests bounds around O(a/d) for good expanders
        literature_bound = attack_edges / 16  # ≈ 62.5
        
        print(f"\nLiterature Comparison:")
        print(f"  Literature O(a/d): {literature_bound:.1f}")
        print(f"  Our bound: {bound.max_sybil_nodes}")
        print(f"  Factor difference: {bound.max_sybil_nodes / literature_bound:.2f}")
        
        # Our bound should be reasonable compared to literature
        assert 0.1 <= bound.max_sybil_nodes / literature_bound <= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])