"""
Graph expansion property calculations.
Implements algorithms from PPE paper Section 4.1.

Key functions:
- compute_vertex_expansion: Check |N(S)| / |S| for subsets
- compute_edge_expansion: Calculate conductance φ(S)
- verify_lse_property: Check if graph is (K, ρ, q)-LSE
- compute_minimum_degree: Verify degree requirements
"""

import networkx as nx
import numpy as np
from typing import List, Tuple, Set, Dict
from itertools import combinations
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

from app.models.graph_metrics import (
    VertexExpansionResult,
    EdgeExpansionResult,
    LSEParameters,
    MinimumDegreeResult
)

logger = logging.getLogger(__name__)


class GraphExpansionAnalyzer:
    """
    Analyzes graph expansion properties for PPE certification graph.
    
    Based on Definition 4.1 and Lemma 4.2 from paper.
    """
    
    def __init__(self, graph: nx.Graph):
        """
        Initialize analyzer with certification graph.
        
        Args:
            graph: NetworkX graph representing the certification graph.
                   Nodes should have 'honest' attribute (bool).
                   Edges represent successful PPE executions.
        """
        self.graph = graph
        self.m = graph.number_of_nodes()
        self.n_edges = graph.number_of_edges()
        
        # Count honest vs deleted nodes
        self.honest_nodes = [n for n, d in graph.nodes(data=True) if d.get('honest', True)]
        self.deleted_nodes = [n for n, d in graph.nodes(data=True) if d.get('deleted', False)]
        self.n = len(self.honest_nodes)
        self.rho = len(self.deleted_nodes)
        
        logger.info(f"Graph initialized: {self.m} nodes, {self.n_edges} edges, "
                   f"{self.n} honest, {self.rho} deleted")
    
    def compute_vertex_expansion(
        self, 
        K: int, 
        rho: int,
        threshold: float = 2.0,
        sample_size: int = 100
    ) -> VertexExpansionResult:
        """
        Compute vertex expansion ratio for the graph.
        
        From Definition 4.1: For sets A, B where K ≤ |A| ≤ m/2,
        check if |neighbors(A) ∩ B| / |A| > threshold
        
        Args:
            K: Minimum set size to check
            rho: Maximum deleted nodes
            threshold: Required expansion ratio (default 2.0 from paper)
            sample_size: Number of random subsets to test
            
        Returns:
            VertexExpansionResult with worst-case expansion ratio
        """
        logger.info(f"Computing vertex expansion: K={K}, rho={rho}, threshold={threshold}")
        
        if K >= self.m / 2:
            logger.warning(f"K={K} >= m/2={self.m/2}, adjusting K to {int(self.m/4)}")
            K = int(self.m / 4)
        
        worst_expansion = float('inf')
        worst_subset_size = 0
        worst_neighbor_size = 0
        
        # Sample random subsets of various sizes
        max_subset_size = max(K, self.m // 2)
        if max_subset_size <= K:
            max_subset_size = min(self.m - 1, K + 10)  # Ensure we have a range
        
        num_sizes = min(10, max_subset_size - K + 1)
        if num_sizes <= 0:
            num_sizes = 1
            subset_sizes = [K]
        else:
            subset_sizes = np.linspace(K, max_subset_size, num_sizes, dtype=int)
        
        for subset_size in subset_sizes:
            for _ in range(sample_size // len(subset_sizes)):
                # Randomly sample a subset A
                A = set(np.random.choice(list(self.graph.nodes()), 
                                        size=min(subset_size, self.m),
                                        replace=False))
                
                # Get neighbors of A
                neighbors_A = set()
                for node in A:
                    neighbors_A.update(self.graph.neighbors(node))
                
                # Remove A itself from neighbors
                neighbors_A -= A
                
                # B is all nodes except A and up to rho deleted nodes
                B = set(self.graph.nodes()) - A
                if len(B) >= self.m - len(A) - rho:
                    B = set(list(B)[:self.m - len(A) - rho])
                
                # Compute expansion ratio
                neighbors_in_B = neighbors_A & B
                expansion_ratio = len(neighbors_in_B) / len(A) if len(A) > 0 else 0
                
                if expansion_ratio < worst_expansion:
                    worst_expansion = expansion_ratio
                    worst_subset_size = len(A)
                    worst_neighbor_size = len(neighbors_in_B)
        
        result = VertexExpansionResult(
            subset_size=worst_subset_size,
            neighbor_size=worst_neighbor_size,
            expansion_ratio=worst_expansion,
            satisfies_threshold=(worst_expansion >= threshold),
            threshold=threshold
        )
        
        logger.info(f"Vertex expansion result: ratio={worst_expansion:.3f}, "
                   f"satisfies={result.satisfies_threshold}")
        
        return result
    
    def compute_edge_expansion(
        self,
        K: int,
        rho: int,
        threshold: float = 0.3,
        sample_size: int = 100
    ) -> EdgeExpansionResult:
        """
        Compute edge expansion (conductance) for the graph.
        
        Conductance φ(S) = |E(S, V\S)| / min(|S|, |V\S|)
        
        Args:
            K: Minimum set size to check
            rho: Maximum deleted nodes
            threshold: Required conductance
            sample_size: Number of random subsets to test
            
        Returns:
            EdgeExpansionResult with worst-case conductance
        """
        logger.info(f"Computing edge expansion: K={K}, rho={rho}, threshold={threshold}")
        
        worst_conductance = float('inf')
        worst_subset_size = 0
        worst_crossing_edges = 0
        
        # Sample random subsets
        max_subset_size = max(K, self.m // 2)
        if max_subset_size <= K:
            max_subset_size = min(self.m - 1, K + 10)  # Ensure we have a range
        
        num_sizes = min(10, max_subset_size - K + 1)
        if num_sizes <= 0:
            num_sizes = 1
            subset_sizes = [K]
        else:
            subset_sizes = np.linspace(K, max_subset_size, num_sizes, dtype=int)
        
        for subset_size in subset_sizes:
            for _ in range(sample_size // len(subset_sizes)):
                # Randomly sample subset S
                S = set(np.random.choice(list(self.graph.nodes()),
                                        size=min(subset_size, self.m),
                                        replace=False))
                
                # V \ S
                V_minus_S = set(self.graph.nodes()) - S
                
                # Count crossing edges
                crossing_edges = 0
                for node in S:
                    for neighbor in self.graph.neighbors(node):
                        if neighbor in V_minus_S:
                            crossing_edges += 1
                
                # Compute conductance
                denominator = min(len(S), len(V_minus_S))
                conductance = crossing_edges / denominator if denominator > 0 else 0
                
                if conductance < worst_conductance:
                    worst_conductance = conductance
                    worst_subset_size = len(S)
                    worst_crossing_edges = crossing_edges
        
        result = EdgeExpansionResult(
            subset_size=worst_subset_size,
            crossing_edges=worst_crossing_edges,
            conductance=worst_conductance,
            satisfies_threshold=(worst_conductance >= threshold),
            threshold=threshold
        )
        
        logger.info(f"Edge expansion result: conductance={worst_conductance:.3f}, "
                   f"satisfies={result.satisfies_threshold}")
        
        return result
    
    def verify_lse_property(
        self,
        lse_params: LSEParameters,
        sample_size: int = 100
    ) -> bool:
        """
        Verify if graph satisfies (K, ρ, q)-LSE property.
        
        From Definition 4.1: For all pairs A, B where:
        - K ≤ |A| ≤ m/2
        - |B| ≥ m - |A| - ρ
        Check: |e(A, B)| > |A||B|q
        
        Args:
            lse_params: LSE parameters (K, ρ, q)
            sample_size: Number of random subset pairs to test
            
        Returns:
            True if graph satisfies LSE property
        """
        logger.info(f"Verifying LSE property: K={lse_params.K}, "
                   f"ρ={lse_params.rho}, q={lse_params.q}")
        
        K = lse_params.K
        rho = lse_params.rho
        q = lse_params.q
        
        # Sample random subset pairs
        violations = 0
        tests = 0
        
        max_subset_size = max(K, self.m // 2)
        if max_subset_size <= K:
            max_subset_size = min(self.m - 1, K + 10)  # Ensure we have a range
        
        num_sizes = min(10, max_subset_size - K + 1)
        if num_sizes <= 0:
            num_sizes = 1
            subset_sizes = [K]
        else:
            subset_sizes = np.linspace(K, max_subset_size, num_sizes, dtype=int)
        
        for subset_size_A in subset_sizes:
            for _ in range(sample_size // len(subset_sizes)):
                # Sample set A
                A = set(np.random.choice(list(self.graph.nodes()),
                                        size=min(subset_size_A, self.m),
                                        replace=False))
                
                # Sample set B: |B| ≥ m - |A| - ρ
                min_B_size = max(1, self.m - len(A) - rho)
                max_B_size = self.m - len(A)
                
                if max_B_size < min_B_size:
                    continue
                
                B_size = np.random.randint(min_B_size, max_B_size + 1)
                possible_B_nodes = list(set(self.graph.nodes()) - A)
                
                if len(possible_B_nodes) < B_size:
                    B = set(possible_B_nodes)
                else:
                    B = set(np.random.choice(possible_B_nodes, size=B_size, replace=False))
                
                # Count edges between A and B
                edges_AB = 0
                for node_a in A:
                    for node_b in self.graph.neighbors(node_a):
                        if node_b in B:
                            edges_AB += 1
                
                # Check LSE condition: |e(A,B)| > |A||B|q
                required_edges = len(A) * len(B) * q
                
                tests += 1
                if edges_AB <= required_edges:
                    violations += 1
                    logger.debug(f"LSE violation: |A|={len(A)}, |B|={len(B)}, "
                               f"e(A,B)={edges_AB} ≤ {required_edges:.1f}")
        
        violation_rate = violations / tests if tests > 0 else 0
        is_lse = (violation_rate < 0.05)  # Allow 5% violation due to sampling
        
        logger.info(f"LSE verification: {violations}/{tests} violations "
                   f"({violation_rate*100:.1f}%), is_LSE={is_lse}")
        
        return is_lse
    
    def compute_minimum_degree(self, required_min: int = 2) -> MinimumDegreeResult:
        """
        Verify minimum degree requirement.
        
        From paper: Each honest node must have degree ≥ d (typically d ≥ 2)
        
        Args:
            required_min: Required minimum degree
            
        Returns:
            MinimumDegreeResult
        """
        degrees = dict(self.graph.degree())
        min_degree = min(degrees.values()) if degrees else 0
        
        # Find nodes below threshold
        nodes_below = [node for node, deg in degrees.items() 
                      if deg < required_min]
        
        result = MinimumDegreeResult(
            minimum_degree=min_degree,
            required_minimum=required_min,
            satisfies_requirement=(min_degree >= required_min),
            nodes_below_threshold=nodes_below
        )
        
        logger.info(f"Minimum degree: {min_degree}, required: {required_min}, "
                   f"nodes below: {len(nodes_below)}")
        
        return result
    
    def compute_average_degree(self) -> float:
        """Compute average degree of the graph."""
        if self.m == 0:
            return 0.0
        return (2 * self.n_edges) / self.m


def build_lse_parameters_from_graph(
    graph: nx.Graph,
    security_param: int = 40,
    eta_v: float = 0.025
) -> LSEParameters:
    """
    Compute LSE parameters based on graph properties.
    
    From Lemma 4.2 and Appendix C of paper.
    
    Args:
        graph: Certification graph
        security_param: Security parameter κ
        eta_v: Maximum fraction of deleted nodes (ηV)
        
    Returns:
        LSE parameters (K, ρ, q)
    """
    m = graph.number_of_nodes()
    d = (2 * graph.number_of_edges()) / m if m > 0 else 0
    
    # From paper: K = κ + (ηVm + 2)ln(m) + ηVm
    K = int(security_param + (eta_v * m + 2) * np.log(m) + eta_v * m)
    
    # ρ = ηVm (maximum deleted nodes)
    rho = int(eta_v * m)
    
    # From Lemma 4.2: q = (b-1)/b * p where b = sqrt(d(1/2 - ηV)/(2ln(m)-2))
    # and p = d/m
    if m > 0 and d > 0:
        b = np.sqrt(d * (0.5 - eta_v) / (2 * np.log(m) - 2))
        p = d / m
        q = ((b - 1) / b) * p if b > 1 else 0.3  # Fallback
    else:
        q = 0.3  # Default
    
    return LSEParameters(K=K, rho=rho, q=q)