"""
Parameter validation and configuration API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.models.poll_parameters import (
    ParameterConstraints,
    ParameterValidationResult,
    PollParameters,
    SecurityLevel
)
from app.services.parameter_validator import get_validator
from app.services.parameter_calculator import get_calculator
from app.config.parameter_presets import get_preset, get_all_presets

router = APIRouter(prefix="/api/parameters", tags=["parameters"])
logger = logging.getLogger(__name__)


@router.post("/validate", response_model=ParameterValidationResult)
async def validate_parameters(params: ParameterConstraints):
    """
    Validate poll parameters against Appendix C constraints.
    
    Returns detailed validation result with errors, warnings, and metrics.
    """
    try:
        validator = get_validator()
        result = validator.validate_all(params)
        
        return result
        
    except Exception as e:
        logger.error(f"Parameter validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate")
async def calculate_parameters(
    m: int,
    security_level: str = "medium",
    custom_constraints: Optional[dict] = None
):
    """
    Calculate optimal parameters for given participant count and security level.
    
    Args:
        m: Expected number of participants
        security_level: 'high', 'medium', or 'low'
        custom_constraints: Optional custom parameter constraints
        
    Returns:
        Calculated parameters and validation result
    """
    try:
        calculator = get_calculator()
        validator = get_validator()
        
        # Calculate parameters
        params = calculator.calculate_for_security_level(
            m=m,
            security_level=security_level,
            custom_constraints=custom_constraints
        )
        
        # Validate calculated parameters
        validation = validator.validate_all(params)
        
        return {
            "parameters": params.dict(),
            "validation": validation.dict()
        }
        
    except Exception as e:
        logger.error(f"Parameter calculation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/presets")
async def get_security_presets():
    """Get all security level presets."""
    presets = get_all_presets()
    return {
        "presets": {name: preset.dict() for name, preset in presets.items()}
    }


@router.get("/presets/{security_level}")
async def get_security_preset(security_level: str):
    """Get specific security level preset."""
    try:
        preset = get_preset(security_level)
        return preset.dict()
    except:
        raise HTTPException(status_code=404, detail=f"Preset {security_level} not found")


@router.post("/optimize-effort")
async def optimize_for_effort(
    m: int,
    max_ppes_per_user: int,
    min_security_level: float = 0.9
):
    """
    Calculate parameters optimized for user effort while maintaining security.
    
    Args:
        m: Expected participants
        max_ppes_per_user: Maximum PPEs user willing to complete
        min_security_level: Minimum security level (0-1)
        
    Returns:
        Optimized parameters
    """
    try:
        calculator = get_calculator()
        validator = get_validator()
        
        params = calculator.optimize_for_user_effort(
            m=m,
            max_ppes_per_user=max_ppes_per_user,
            min_security_level=min_security_level
        )
        
        validation = validator.validate_all(params)
        
        return {
            "parameters": params.dict(),
            "validation": validation.dict()
        }
        
    except Exception as e:
        logger.error(f"Effort optimization error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/estimate-minimum-participants")
async def estimate_minimum_participants(
    d: float,
    kappa: int = 40,
    eta_v: float = 0.025
):
    """
    Estimate minimum participants for given degree.
    
    Useful for: "I want each user to do d PPEs, how many participants do I need?"
    """
    try:
        calculator = get_calculator()
        min_m = calculator.calculate_minimum_participants(d, kappa, eta_v)
        
        return {
            "minimum_participants": min_m,
            "d": d,
            "kappa": kappa,
            "eta_v": eta_v
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/poll/{poll_id}/parameters")
async def get_poll_parameters(
    poll_id: str,
    db: Session = Depends(get_db)
):
    """Get stored parameters for a poll."""
    params = db.query(PollParameters).filter_by(poll_id=poll_id).first()
    
    if not params:
        raise HTTPException(status_code=404, detail="Poll parameters not found")
    
    return params.to_dict()


@router.post("/poll/{poll_id}/parameters")
async def save_poll_parameters(
    poll_id: str,
    params: ParameterConstraints,
    db: Session = Depends(get_db)
):
    """
    Save and validate parameters for a poll.
    """
    try:
        # Validate first
        validator = get_validator()
        validation = validator.validate_all(params)
        
        if not validation.valid:
            return {
                "success": False,
                "errors": validation.errors,
                "warnings": validation.warnings
            }
        
        # Save to database
        poll_params = PollParameters(
            poll_id=poll_id,
            m=params.m,
            d=params.d,
            kappa=params.kappa,
            eta_v=params.eta_v,
            eta_e=params.eta_e,
            p=params.p,
            b=params.b,
            validated=True,
            validation_result=validation.dict()
        )
        
        db.merge(poll_params)  # Use merge to update if exists
        db.commit()
        
        return {
            "success": True,
            "parameters": poll_params.to_dict(),
            "validation": validation.dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to save parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))