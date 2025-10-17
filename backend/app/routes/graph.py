"""
API routes for ideal certification graph operations.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, List, Set
import json

from ..services.graph_service import graph_service
from ..services.poll_service import poll_service

router = APIRouter(prefix="/polls/{poll_id}/graph", tags=["Graph"])


@router.get("/generate")
async def generate_graph(poll_id: str, k: int = 3):
    """
    Generate or retrieve the ideal certification graph for a poll.
    
    This determines which participants should perform PPE with each other.
    The graph is deterministic based on the poll_id and registered participants.
    
    Args:
        poll_id: Poll identifier
        k: Desired degree (number of neighbors per participant), default 3
        
    Returns:
        Graph properties and validation results
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    participant_ids = list(poll.registrants.keys())
    
    if len(participant_ids) < 2:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Need at least 2 registered participants to generate graph"
        )
    
    # Generate the graph
    graph = graph_service.get_or_generate_graph(poll_id, participant_ids, k)
    
    # Get properties
    properties = graph_service.get_graph_properties(poll_id)
    metrics = graph_service.get_graph_metrics(poll_id)
    
    return {
        "poll_id": poll_id,
        "num_participants": len(participant_ids),
        "properties": properties,
        "metrics": metrics,
        "message": "Graph generated successfully"
    }


@router.get("/neighbors")
async def get_neighbors(poll_id: str, user_id: str):
    """
    Get the assigned PPE neighbors for a specific user.
    
    Args:
        poll_id: Poll identifier
        user_id: User identifier
        
    Returns:
        List of neighbor user IDs that this user should perform PPE with
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    if user_id not in poll.registrants:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "User not registered for this poll"
        )
    
    # Ensure graph is generated
    participant_ids = list(poll.registrants.keys())
    if len(participant_ids) < 2:
        return {
            "user_id": user_id,
            "neighbors": [],
            "message": "Not enough participants for PPE"
        }
    
    graph = graph_service.get_or_generate_graph(poll_id, participant_ids)
    neighbors = graph_service.get_user_neighbors(poll_id, user_id)
    
    return {
        "user_id": user_id,
        "neighbors": list(neighbors),
        "neighbor_count": len(neighbors)
    }


@router.get("/")
async def get_full_graph(poll_id: str):
    """
    Get the complete ideal certification graph for a poll.
    
    Returns the full adjacency list representation.
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        Complete graph structure
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    graph = graph_service.get_full_graph(poll_id)
    
    if graph is None:
        # Graph not generated yet, generate it
        participant_ids = list(poll.registrants.keys())
        if len(participant_ids) < 2:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Not enough participants to generate graph"
            )
        graph = graph_service.get_or_generate_graph(poll_id, participant_ids)
    
    # Convert sets to lists for JSON serialization
    graph_serializable = {
        user_id: list(neighbors) 
        for user_id, neighbors in graph.items()
    }
    
    properties = graph_service.get_graph_properties(poll_id)
    
    return {
        "poll_id": poll_id,
        "graph": graph_serializable,
        "properties": properties
    }


@router.post("/invalidate")
async def invalidate_graph(poll_id: str):
    """
    Invalidate the cached graph for a poll.
    
    Should be called when participant list changes significantly.
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        Success message
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    graph_service.invalidate_graph(poll_id)
    
    return {
        "message": "Graph invalidated successfully",
        "poll_id": poll_id
    }