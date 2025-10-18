"""
API endpoints for graph expansion metrics.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import networkx as nx
import logging

from app.models.graph_metrics import GraphExpansionMetrics
from app.services.graph_expansion_service import expansion_service
# Note: Update this import path based on your actual database setup
# from app.database import get_db
from app.models import get_certification_graph, get_poll_participants

# Temporary placeholder for database dependency
# Replace with your actual database session dependency
def get_db():
    """Placeholder for database session dependency"""
    pass

router = APIRouter(prefix="/api/expansion", tags=["expansion"])
logger = logging.getLogger(__name__)


def get_poll_graph(db: Session, poll_id: str) -> nx.Graph:
    """
    Get certification graph as NetworkX graph for expansion analysis.
    
    Args:
        db: Database session
        poll_id: Poll identifier
        
    Returns:
        NetworkX graph with certification edges
    """
    # Get participants and certifications
    participants = get_poll_participants(db, poll_id)
    edges = get_certification_graph(db, poll_id)
    
    if not participants:
        raise HTTPException(status_code=404, detail=f"Poll {poll_id} not found or has no participants")
    
    # Build NetworkX graph
    G = nx.Graph()
    
    # Add nodes with attributes
    for participant in participants:
        G.add_node(
            participant.user_id,
            honest=True,  # Assume all registered participants are honest initially
            deleted=False  # Track if node was deleted due to failed certifications
        )
    
    # Add edges (successful PPE certifications)
    for user_id, peer_id in edges:
        if G.has_node(user_id) and G.has_node(peer_id):
            G.add_edge(user_id, peer_id)
    
    logger.info(f"Built graph for poll {poll_id}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


@router.get("/{poll_id}/metrics", response_model=GraphExpansionMetrics)
async def get_expansion_metrics(
    poll_id: str,
    attack_edges: Optional[int] = None,
    recalculate: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get graph expansion metrics for a poll.
    
    Returns all expansion properties including THE KEY METRIC:
    maximum number of Sybil identities adversary can create.
    
    Args:
        poll_id: Poll identifier
        attack_edges: Adversary's attack edges (optional, will be estimated)
        recalculate: Force recalculation even if cached
        db: Database session
        
    Returns:
        Complete expansion metrics including Sybil bound
    """
    try:
        # Get certification graph for poll
        graph = get_poll_graph(db, poll_id)
        
        if graph.number_of_nodes() == 0:
            raise HTTPException(status_code=404, detail=f"Poll {poll_id} has no participants")
        
        # Compute metrics
        metrics = expansion_service.compute_all_metrics(
            graph=graph,
            poll_id=poll_id,
            attack_edges=attack_edges
        )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing expansion metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{poll_id}/sybil-bound")
async def get_sybil_bound(
    poll_id: str, 
    attack_edges: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get ONLY the Sybil resistance bound (quick endpoint).
    
    Returns:
        Sybil bound information
    """
    try:
        graph = get_poll_graph(db, poll_id)
        
        if graph.number_of_nodes() == 0:
            raise HTTPException(status_code=404, detail="Poll has no participants")
        
        metrics = expansion_service.compute_all_metrics(
            graph=graph,
            poll_id=poll_id,
            attack_edges=attack_edges
        )
        
        return {
            "poll_id": poll_id,
            "sybil_bound": metrics.sybil_bound,
            "verification_passed": metrics.verification_passed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing Sybil bound: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{poll_id}/expansion/vertex")
async def get_vertex_expansion(poll_id: str, db: Session = Depends(get_db)):
    """Get vertex expansion only."""
    try:
        graph = get_poll_graph(db, poll_id)
        metrics = expansion_service.compute_all_metrics(graph, poll_id)
        return metrics.vertex_expansion
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing vertex expansion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{poll_id}/expansion/edge")
async def get_edge_expansion(poll_id: str, db: Session = Depends(get_db)):
    """Get edge expansion (conductance) only."""
    try:
        graph = get_poll_graph(db, poll_id)
        metrics = expansion_service.compute_all_metrics(graph, poll_id)
        return metrics.edge_expansion
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing edge expansion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{poll_id}/expansion/spectral")
async def get_spectral_gap(poll_id: str, db: Session = Depends(get_db)):
    """Get spectral gap only."""
    try:
        graph = get_poll_graph(db, poll_id)
        metrics = expansion_service.compute_all_metrics(graph, poll_id)
        return metrics.spectral_gap
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing spectral gap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{poll_id}/lse-property")
async def get_lse_property(poll_id: str, db: Session = Depends(get_db)):
    """Get LSE property verification only."""
    try:
        graph = get_poll_graph(db, poll_id)
        metrics = expansion_service.compute_all_metrics(graph, poll_id)
        return {
            "poll_id": poll_id,
            "is_lse": metrics.is_lse,
            "lse_parameters": metrics.lse_parameters,
            "verification_passed": metrics.verification_passed
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing LSE property: {e}")
        raise HTTPException(status_code=500, detail=str(e))