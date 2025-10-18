"""
API routes for proof graph operations.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any

from ..services.proof_graph_service import proof_graph_service
from ..services.poll_service import poll_service


router = APIRouter(prefix="/polls/{poll_id}/proof", tags=["Proof Graph"])


@router.get("/graph")
async def get_proof_graph(poll_id: str):
    """
    Get the complete proof graph for a poll.
    
    This is Protocol 5 - the pollster publishes the proof graph
    which allows anyone to verify the poll's integrity.
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        Complete proof graph with all participants, certifications, and votes
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    # Construct or retrieve proof graph
    proof_graph = proof_graph_service.get_or_construct_proof_graph(poll)
    
    # Verify the hash is valid
    if not proof_graph.verify_hash():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Proof graph hash verification failed"
        )
    
    return proof_graph.model_dump()


@router.get("/summary")
async def get_proof_summary(poll_id: str):
    """
    Get a summary of the proof graph.
    
    Provides high-level view without full graph details.
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        Proof graph summary
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    # Get or construct proof graph
    proof_graph = proof_graph_service.get_or_construct_proof_graph(poll)
    
    # Get verification result
    verification_result = poll_service.verify_poll_integrity(poll)
    
    # Create summary
    summary = proof_graph_service.create_summary(proof_graph, verification_result)
    
    return summary.model_dump()


@router.get("/export")
async def export_proof_graph(poll_id: str):
    """
    Export the complete proof graph as a downloadable JSON file.
    
    This allows external parties to download and verify the poll
    independently.
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        JSON file with complete proof graph
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    # Get proof graph
    proof_graph = proof_graph_service.get_or_construct_proof_graph(poll)
    
    # Create exportable format
    export_data = proof_graph.to_exportable_dict()
    
    # Add verification instructions
    export_data["verification_instructions"] = {
        "description": "This proof graph can be independently verified",
        "steps": [
            "1. Verify the graph hash matches the computed hash",
            "2. Verify all votes have valid signatures",
            "3. Verify all voters have sufficient PPE certifications",
            "4. Verify the certification graph has good expansion properties"
        ]
    }
    
    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f"attachment; filename=proof_graph_{poll_id}.json"
        }
    )


@router.post("/reconstruct")
async def reconstruct_proof_graph(poll_id: str):
    """
    Force reconstruction of the proof graph.
    
    Useful if poll data has changed and cached proof graph is stale.
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        Newly constructed proof graph
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    # Invalidate cache
    proof_graph_service.invalidate_proof_graph(poll_id)
    
    # Reconstruct
    proof_graph = proof_graph_service.construct_proof_graph(poll)
    
    return {
        "message": "Proof graph reconstructed successfully",
        "graph_hash": proof_graph.graph_hash,
        "num_participants": proof_graph.metadata.num_participants,
        "num_certifications": proof_graph.metadata.num_certifications,
        "num_votes": proof_graph.metadata.num_votes
    }


@router.get("/verify-hash")
async def verify_proof_hash(poll_id: str):
    """
    Verify the integrity of a proof graph's hash.
    
    Args:
        poll_id: Poll identifier
        
    Returns:
        Hash verification result
    """
    poll = poll_service.get_poll(poll_id)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    
    proof_graph = proof_graph_service.get_or_construct_proof_graph(poll)
    
    is_valid = proof_graph.verify_hash()
    stored_hash = proof_graph.graph_hash
    computed_hash = proof_graph.compute_hash()
    
    return {
        "is_valid": is_valid,
        "stored_hash": stored_hash,
        "computed_hash": computed_hash,
        "match": stored_hash == computed_hash
    }