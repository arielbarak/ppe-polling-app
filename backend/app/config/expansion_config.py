"""
Configuration for graph expansion verification.
"""

from pydantic_settings import BaseSettings


class ExpansionConfig(BaseSettings):
    # Security parameters
    SECURITY_PARAMETER: int = 40  # κ
    
    # Graph parameters (from Appendix C)
    ETA_E: float = 0.125  # Max fraction failed PPEs (ηE)
    ETA_V: float = 0.025  # Max fraction deleted nodes (ηV)
    
    # Expansion thresholds
    VERTEX_EXPANSION_THRESHOLD: float = 2.0
    EDGE_EXPANSION_THRESHOLD: float = 0.3
    SPECTRAL_GAP_THRESHOLD: float = 0.1
    MINIMUM_DEGREE: int = 2
    
    # Computation parameters
    EXPANSION_SAMPLE_SIZE: int = 100  # Samples for expansion calculation
    USE_SPARSE_SPECTRAL: bool = True  # Use sparse methods for large graphs
    
    class Config:
        env_prefix = "EXPANSION_"


expansion_config = ExpansionConfig()