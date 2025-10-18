"""
Data models for graph expansion metrics.
Based on PPE paper Section 4.1 and Theorem 4.4.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class LSEParameters(BaseModel):
    """
    Large-Set Expanding property parameters.
    From Definition 4.1 in paper.
    """
    K: int = Field(..., description="Minimum set size for expansion")
    rho: int = Field(..., description="Maximum number of deleted nodes")
    q: float = Field(..., description="Expansion factor")
    
    class Config:
        json_schema_extra = {
            "example": {
                "K": 100,
                "rho": 50,
                "q": 0.45
            }
        }


class VertexExpansionResult(BaseModel):
    """Results of vertex expansion calculation."""
    subset_size: int
    neighbor_size: int
    expansion_ratio: float = Field(..., description="|N(S)| / |S|")
    satisfies_threshold: bool
    threshold: float


class EdgeExpansionResult(BaseModel):
    """
    Results of edge expansion (conductance) calculation.
    φ(S) = |E(S, V\S)| / min(|S|, |V\S|)
    """
    subset_size: int
    crossing_edges: int
    conductance: float
    satisfies_threshold: bool
    threshold: float


class SpectralGapResult(BaseModel):
    """
    Spectral gap analysis results.
    Second eigenvalue of Laplacian matrix.
    """
    second_eigenvalue: float = Field(..., description="Second eigenvalue (lambda_2)")
    algebraic_connectivity: float  # Same as lambda_2
    satisfies_threshold: bool
    threshold: float
    computation_time_ms: float
    
    @property
    def lambda_2(self):
        """Alias for second_eigenvalue for convenience."""
        return self.second_eigenvalue


class SybilResistanceBound(BaseModel):
    """
    THE KEY METRIC: Sybil attack resistance bound.
    From Theorem 4.4: # Sybil nodes ≤ Ω(a/d)
    """
    max_sybil_nodes: int = Field(
        ..., 
        description="Maximum number of Sybil identities adversary can create"
    )
    attack_edges: int = Field(..., alias="a", description="# successful PPEs with honest nodes")
    average_degree: float = Field(..., alias="d", description="Average degree of graph")
    honest_nodes: int = Field(..., alias="n", description="Number of honest participants")
    multiplicative_advantage: float = Field(
        ..., 
        alias="C_star",
        description="Adversary's advantage over honest user"
    )
    expansion_factor: float = Field(..., description="Graph expansion ratio used in bound")
    
    # Human-readable interpretation
    resistance_level: str = Field(
        ..., 
        description="HIGH/MEDIUM/LOW based on max_sybil_nodes/honest_nodes ratio"
    )
    sybil_percentage: float = Field(
        ...,
        description="Percentage of total nodes that could be Sybil"
    )


class MinimumDegreeResult(BaseModel):
    """Minimum degree verification."""
    minimum_degree: int
    required_minimum: int
    satisfies_requirement: bool
    nodes_below_threshold: List[int] = Field(default_factory=list)


class GraphExpansionMetrics(BaseModel):
    """
    Complete graph expansion verification results.
    All metrics from PPE paper Section 4.1.
    """
    poll_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Graph basic properties
    num_nodes: int = Field(..., alias="m")
    num_edges: int
    num_honest_nodes: int = Field(..., alias="n")
    num_deleted_nodes: int
    average_degree: float = Field(..., alias="d")
    
    # LSE property
    lse_parameters: LSEParameters
    is_lse: bool = Field(..., description="Does graph satisfy (K,ρ,q)-LSE?")
    
    # Expansion properties
    vertex_expansion: VertexExpansionResult
    edge_expansion: EdgeExpansionResult
    spectral_gap: SpectralGapResult
    minimum_degree: MinimumDegreeResult
    
    # THE CRITICAL METRIC
    sybil_bound: SybilResistanceBound
    
    # Overall verdict
    verification_passed: bool = Field(
        ...,
        description="Do all expansion properties satisfy requirements?"
    )
    failure_reasons: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "poll_id": "poll_123",
                "num_nodes": 1000,
                "num_edges": 30000,
                "num_honest_nodes": 800,
                "num_deleted_nodes": 25,
                "average_degree": 60,
                "is_lse": True,
                "sybil_bound": {
                    "max_sybil_nodes": 50,
                    "attack_edges": 3000,
                    "average_degree": 60,
                    "honest_nodes": 800,
                    "multiplicative_advantage": 1.5,
                    "expansion_factor": 2.1,
                    "resistance_level": "HIGH",
                    "sybil_percentage": 5.0
                },
                "verification_passed": True
            }
        }