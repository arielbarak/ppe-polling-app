"""
API routes for PPE configuration and type selection.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel

from ..ppe.factory import ppe_factory
from ..ppe.base import PPEType, PPEDifficulty


router = APIRouter(prefix="/ppe", tags=["PPE Configuration"])


class PPEConfigRequest(BaseModel):
    """Request to configure PPE for a poll."""
    ppe_type: str
    difficulty: str = "medium"


@router.get("/types")
async def get_available_ppe_types():
    """
    Get all available PPE mechanism types.
    
    Returns:
        Dictionary of available PPE types with metadata
    """
    return {
        "available_types": ppe_factory.get_available_types(),
        "default_type": PPEType.SYMMETRIC_CAPTCHA.value
    }


@router.get("/types/{ppe_type}")
async def get_ppe_type_info(ppe_type: str):
    """
    Get detailed information about a specific PPE type.
    
    Args:
        ppe_type: PPE type identifier
        
    Returns:
        Metadata about the PPE type
    """
    try:
        ppe_type_enum = PPEType(ppe_type)
    except ValueError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"PPE type '{ppe_type}' not found"
        )
    
    metadata = ppe_factory.get_metadata(ppe_type_enum)
    if not metadata:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"No metadata found for PPE type '{ppe_type}'"
        )
    
    return metadata.to_dict()


@router.post("/test-challenge")
async def test_challenge_generation(config: PPEConfigRequest):
    """
    Test challenge generation for a PPE type.
    
    Useful for testing and debugging new PPE implementations.
    
    Args:
        config: PPE configuration
        
    Returns:
        Sample challenge and metadata
    """
    try:
        ppe_type = PPEType(config.ppe_type)
        difficulty = PPEDifficulty(config.difficulty)
    except ValueError as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Invalid configuration: {str(e)}"
        )
    
    # Create PPE instance
    ppe = ppe_factory.create(ppe_type, difficulty)
    
    # Generate test challenge
    test_secret = "test_secret_123"
    test_session = "test_session_456"
    
    challenge_data, solution = ppe.generate_challenge_with_secret(
        test_secret, test_session
    )
    
    return {
        "ppe_type": ppe_type.value,
        "difficulty": difficulty.value,
        "sample_challenge": challenge_data,
        "estimated_effort_seconds": ppe.estimate_effort(),
        "client_config": ppe.get_client_config(),
        "note": "This is a test challenge. The solution is hidden."
    }


@router.get("/config/default")
async def get_default_config():
    """
    Get the default PPE configuration.
    
    Returns:
        Default PPE settings
    """
    return {
        "ppe_type": PPEType.SYMMETRIC_CAPTCHA.value,
        "difficulty": PPEDifficulty.MEDIUM.value,
        "description": "Default configuration uses Symmetric CAPTCHA at medium difficulty"
    }