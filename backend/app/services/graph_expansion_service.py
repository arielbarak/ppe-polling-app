"""
High-level service for graph expansion analysis.
Orchestrates all expansion metrics computation.
"""

import networkx as nx
import logging
from typing import Optional

from app.models.graph_metrics import GraphExpansionMetrics
from app.services.graph_expansion import (
    GraphExpansionAnalyzer,
    build_lse_parameters_from_graph
)
from app.services.spectral_analysis import SpectralAnalyzer
from app.services.sybil_bounds import SybilBoundCalculator

logger = logging.getLogger(__name__)


class GraphExpansionService:
    """
    Service for computing all graph expansion metrics.
    Main entry point for expansion verification.
    """
    
    def compute_all_metrics(
        self,
        graph: nx.Graph,
        poll_id: str,
        attack_edges: Optional[int] = None,
        security_param: int = 40,
        eta_e: float = 0.125,
        eta_v: float = 0.025
    ) -> GraphExpansionMetrics:
        """
        Compute all expansion metrics for certification graph.
        
        Args:
            graph: Certification graph
            poll_id: Poll identifier
            attack_edges: Number of attack edges (if None, estimated)
            security_param: Security parameter κ
            eta_e: Max fraction failed PPEs (ηE)
            eta_v: Max fraction deleted nodes (ηV)
            
        Returns:
            Complete GraphExpansionMetrics
        """
        logger.info(f"Computing expansion metrics for poll {poll_id}")
        
        # Initialize analyzers
        expansion_analyzer = GraphExpansionAnalyzer(graph)
        spectral_analyzer = SpectralAnalyzer(graph)
        
        # Build LSE parameters
        lse_params = build_lse_parameters_from_graph(graph, security_param, eta_v)
        
        # Estimate attack edges if not provided
        if attack_edges is None:
            sybil_calc_temp = SybilBoundCalculator(graph, 0, eta_e, eta_v)
            attack_edges = sybil_calc_temp.estimate_attack_edges_from_graph()
            logger.info(f"Estimated attack edges: {attack_edges}")
        
        # Compute expansion properties
        vertex_exp = expansion_analyzer.compute_vertex_expansion(
            K=lse_params.K,
            rho=lse_params.rho,
            threshold=2.0
        )
        
        edge_exp = expansion_analyzer.compute_edge_expansion(
            K=lse_params.K,
            rho=lse_params.rho,
            threshold=0.3
        )
        
        spectral_gap = spectral_analyzer.compute_spectral_gap(
            threshold=0.1
        )
        
        min_degree = expansion_analyzer.compute_minimum_degree(
            required_min=2
        )
        
        # Verify LSE property
        is_lse = expansion_analyzer.verify_lse_property(lse_params)
        
        # Compute Sybil bound (THE KEY METRIC)
        sybil_calculator = SybilBoundCalculator(graph, attack_edges, eta_e, eta_v)
        sybil_bound = sybil_calculator.compute_sybil_bound(
            expansion_ratio=vertex_exp.expansion_ratio
        )
        
        # Overall verification
        verification_passed = all([
            is_lse,
            vertex_exp.satisfies_threshold,
            edge_exp.satisfies_threshold,
            spectral_gap.satisfies_threshold,
            min_degree.satisfies_requirement
        ])
        
        failure_reasons = []
        if not is_lse:
            failure_reasons.append("Graph does not satisfy LSE property")
        if not vertex_exp.satisfies_threshold:
            failure_reasons.append(f"Vertex expansion too low: {vertex_exp.expansion_ratio:.2f}")
        if not edge_exp.satisfies_threshold:
            failure_reasons.append(f"Edge expansion too low: {edge_exp.conductance:.2f}")
        if not spectral_gap.satisfies_threshold:
            failure_reasons.append(f"Spectral gap too low: {spectral_gap.lambda_2:.2f}")
        if not min_degree.satisfies_requirement:
            failure_reasons.append(f"Minimum degree too low: {min_degree.minimum_degree}")
        
        # Build result
        metrics = GraphExpansionMetrics(
            poll_id=poll_id,
            m=graph.number_of_nodes(),  # Use alias
            num_edges=graph.number_of_edges(),
            n=expansion_analyzer.n,  # Use alias
            num_deleted_nodes=expansion_analyzer.rho,
            d=expansion_analyzer.compute_average_degree(),  # Use alias
            lse_parameters=lse_params,
            is_lse=is_lse,
            vertex_expansion=vertex_exp,
            edge_expansion=edge_exp,
            spectral_gap=spectral_gap,
            minimum_degree=min_degree,
            sybil_bound=sybil_bound,
            verification_passed=verification_passed,
            failure_reasons=failure_reasons
        )
        
        logger.info(f"Expansion metrics computed: verification_passed={verification_passed}, "
                   f"max_sybil={sybil_bound.max_sybil_nodes}")
        
        return metrics


# Global service instance
expansion_service = GraphExpansionService()