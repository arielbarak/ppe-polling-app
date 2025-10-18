"""
Sybil resistance bound computation.
THE KEY SECURITY METRIC from Theorem 4.4.

Computes: max # of Sybil nodes ≤ Ω(a/d)
where a = attack edges, d = average degree
"""

import networkx as nx
import numpy as np
import logging
from typing import Tuple

from app.models.graph_metrics import SybilResistanceBound

logger = logging.getLogger(__name__)


class SybilBoundCalculator:
    """
    Calculates Sybil resistance bounds from Theorem 4.4.
    
    Main result: If adversary can succeed in 'a' PPEs with honest nodes,
    and graph has average degree 'd', then adversary can control at most
    O(a/d) nodes without detection.
    """
    
    def __init__(
        self,
        graph: nx.Graph,
        attack_edges: int,
        eta_e: float = 0.125,
        eta_v: float = 0.025
    ):
        """
        Initialize calculator.
        
        Args:
            graph: Certification graph
            attack_edges: Number of successful PPEs adversary achieved (a)
            eta_e: Max fraction of failed PPEs before deletion (ηE)
            eta_v: Max fraction of deleted nodes (ηV)
        """
        self.graph = graph
        self.attack_edges = attack_edges
        self.eta_e = eta_e
        self.eta_v = eta_v
        
        self.m = graph.number_of_nodes()
        self.n_edges = graph.number_of_edges()
        self.d = (2 * self.n_edges) / self.m if self.m > 0 else 0
        
        # Count honest nodes
        self.n = len([n for n, data in graph.nodes(data=True) 
                     if data.get('honest', True) and not data.get('deleted', False)])
    
    def compute_sybil_bound(self, expansion_ratio: float = 2.0) -> SybilResistanceBound:
        """
        Compute maximum number of Sybil nodes adversary can create.
        
        From Theorem 4.4:
        max_sybil_nodes = max(K, b / ((b-1)(1/2 - ηV) - bηE) * (a/d))
        
        where b = sqrt(d(1/2 - ηV) / (2ln(m) - 2))
        
        Args:
            expansion_ratio: Measured vertex expansion ratio
            
        Returns:
            SybilResistanceBound with all metrics
        """
        logger.info(f"Computing Sybil bound: a={self.attack_edges}, d={self.d:.2f}, "
                   f"expansion={expansion_ratio:.2f}")
        
        if self.m == 0 or self.d == 0:
            return self._create_zero_bound()
        
        # Compute b parameter from paper
        if self.m > 1:
            b = np.sqrt(self.d * (0.5 - self.eta_v) / (2 * np.log(self.m) - 2))
        else:
            b = 2.0  # Fallback
        
        # Check if b is valid
        denominator = (b - 1) * (0.5 - self.eta_v) - b * self.eta_e
        if b <= 1 or denominator <= 0:
            logger.warning(f"Invalid b parameter: b={b:.3f}, denominator={denominator:.3f}")
            # Use simpler bound based on expansion ratio
            max_sybil = int(self.attack_edges / (self.d * expansion_ratio))
        else:
            # From Theorem 4.4
            max_sybil = int((b / denominator) * (self.attack_edges / self.d))
        
        # K is the "free" bound from paper (Appendix C)
        security_param = 40  # κ
        K = int(security_param + (self.eta_v * self.m + 2) * np.log(self.m) + self.eta_v * self.m)
        
        # Final bound is max of the two
        max_sybil_nodes = max(K, max_sybil)
        
        # Compute multiplicative advantage C*
        # This is how many times more influence adversary has vs honest user
        honest_user_votes = 1  # Each honest user gets 1 vote
        adversary_votes = max_sybil_nodes
        C_star = adversary_votes / honest_user_votes if self.attack_edges > 0 else 1.0
        
        # Resistance level interpretation
        sybil_percentage = (max_sybil_nodes / self.m * 100) if self.m > 0 else 0
        
        if sybil_percentage < 5:
            resistance_level = "HIGH"
        elif sybil_percentage < 15:
            resistance_level = "MEDIUM"
        else:
            resistance_level = "LOW"
        
        bound = SybilResistanceBound(
            max_sybil_nodes=max_sybil_nodes,
            a=self.attack_edges,  # Use alias
            d=self.d,  # Use alias
            n=self.n,  # Use alias
            C_star=C_star,  # Use alias
            expansion_factor=expansion_ratio,
            resistance_level=resistance_level,
            sybil_percentage=sybil_percentage
        )
        
        logger.info(f"Sybil bound computed: max={max_sybil_nodes}, "
                   f"percentage={sybil_percentage:.1f}%, level={resistance_level}")
        
        return bound
    
    def compute_multiplicative_advantage(self, max_sybil: int) -> float:
        """
        Compute adversary's multiplicative advantage.
        
        From paper: C(a) = B(a,m) * d/a
        where B(a,m) is the max influence function
        
        Args:
            max_sybil: Maximum Sybil nodes
            
        Returns:
            Multiplicative advantage C*
        """
        if self.attack_edges == 0:
            return 1.0
        
        # Adversary can influence max_sybil votes
        # By spending attack_edges effort
        # vs honest user who influences 1 vote by spending d effort
        
        adversary_votes_per_effort = max_sybil / self.attack_edges
        honest_votes_per_effort = 1 / self.d if self.d > 0 else 0
        
        if honest_votes_per_effort == 0:
            return float('inf')
        
        C_star = adversary_votes_per_effort / honest_votes_per_effort
        return C_star
    
    def estimate_attack_edges_from_graph(self) -> int:
        """
        Estimate number of attack edges from graph structure.
        
        Attack edges are edges between honest nodes and potentially
        malicious nodes (nodes with suspicious patterns).
        
        Returns:
            Estimated attack edges
        """
        # This is a heuristic - in practice, 'a' is a security parameter
        # representing adversary's resources
        
        # Count edges to nodes with very high or very low degree
        degrees = dict(self.graph.degree())
        avg_degree = np.mean(list(degrees.values()))
        std_degree = np.std(list(degrees.values()))
        
        suspicious_nodes = [
            node for node, deg in degrees.items()
            if abs(deg - avg_degree) > 2 * std_degree
        ]
        
        attack_edge_count = 0
        for node in suspicious_nodes:
            attack_edge_count += degrees[node]
        
        return attack_edge_count
    
    def _create_zero_bound(self) -> SybilResistanceBound:
        """Create bound for empty graph."""
        return SybilResistanceBound(
            max_sybil_nodes=0,
            a=0,  # Use alias
            d=0.0,  # Use alias
            n=0,  # Use alias
            C_star=1.0,  # Use alias
            expansion_factor=0.0,
            resistance_level="UNKNOWN",
            sybil_percentage=0.0
        )


def compute_attack_edges_from_params(
    adversary_resources: float,
    ppe_cost: float = 1.0
) -> int:
    """
    Compute attack edges from adversary's available resources.
    
    If adversary has R resources and each PPE costs C to attack,
    then a = R / C.
    
    Args:
        adversary_resources: Total resources available to adversary
        ppe_cost: Cost per successful attack on PPE
        
    Returns:
        Number of attack edges
    """
    return int(adversary_resources / ppe_cost)