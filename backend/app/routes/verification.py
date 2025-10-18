"""
API routes for advanced verification.
"""

from fastapi import APIRouter, HTTPException, status
from ..services.verification_service import verification_service
from ..services.poll_service import poll_service


router = APIRouter(prefix="/polls/{poll_id}/verification", tags=["Verification"])


@router.get("/comprehensive")
async def verify_poll_comprehensive(poll_id: str):
    """
    Perform comprehensive verification of a poll.
    
    Runs all advanced verification algorithms including:
    - Graph expansion analysis
    - Sybil attack detection
    - Vote signature verification
    - Statistical analysis
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        Complete verification result with errors, warnings, and analysis
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    result = verification_service.verify_poll_comprehensive(poll)
    
    return result.to_dict()


@router.get("/graph-properties")
async def get_graph_properties(poll_id: str):
    """
    Get detailed graph properties analysis.
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        Graph connectivity, expansion, and structural properties
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    result = verification_service.verify_poll_comprehensive(poll)
    
    return {
        "connectivity": result.analysis.get("connectivity", {}),
        "degree_distribution": result.analysis.get("degree_distribution", {}),
        "clustering_coefficient": result.metrics.get("clustering_coefficient", 0),
        "spectral_gap": result.metrics.get("spectral_gap", 0),
        "expansion_ratios": result.analysis.get("expansion_ratios", [])
    }


@router.get("/sybil-detection")
async def detect_sybil_attacks(poll_id: str):
    """
    Run Sybil attack detection algorithms.
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        Potential Sybil clusters and suspicious patterns
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    result = verification_service.verify_poll_comprehensive(poll)
    
    return {
        "suspicious_clusters": result.analysis.get("suspicious_clusters", []),
        "isolated_components": result.analysis.get("isolated_components", []),
        "vote_certification_correlation": result.analysis.get("vote_certification_correlation", {}),
        "has_suspicious_patterns": len(result.warnings) > 0
    }


@router.get("/vote-validation")
async def validate_votes(poll_id: str):
    """
    Validate all votes in the poll.
    
    Checks signatures, eligibility, and authorization.
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        Vote validation results
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    result = verification_service.verify_poll_comprehensive(poll)
    
    return {
        "total_votes": result.metrics.get("total_votes", 0),
        "valid_votes": result.metrics.get("valid_votes", 0),
        "unauthorized_votes": result.analysis.get("unauthorized_votes", []),
        "invalid_signatures": result.analysis.get("invalid_signatures", []),
        "all_valid": result.is_valid
    }


@router.get("/statistical-analysis")
async def get_statistical_analysis(poll_id: str):
    """
    Get statistical analysis of the poll.
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        Statistical metrics and distributions
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    result = verification_service.verify_poll_comprehensive(poll)
    
    return {
        "participation_rate": result.metrics.get("participation_rate", 0),
        "certification_coverage": result.metrics.get("certification_coverage", 0),
        "avg_certifications_per_user": result.metrics.get("avg_certifications_per_user", 0),
        "std_certifications_per_user": result.metrics.get("std_certifications_per_user", 0),
        "degree_distribution": result.analysis.get("degree_distribution", {})
    }