"""
Poll parameter models with validation.
Based on Appendix C of PPE paper.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
import math

from app.database import Base


class ParameterConstraints(BaseModel):
    """
    Constraints from Appendix C of paper.
    All parameters must satisfy these for security guarantees.
    """
    
    # Basic parameters
    m: int = Field(..., gt=0, description="Total number of participants")
    d: float = Field(..., gt=0, description="Expected degree (PPEs per user)")
    kappa: int = Field(40, ge=20, le=128, description="Security parameter (κ)")
    eta_v: float = Field(0.025, gt=0, lt=0.1, description="Max fraction deleted nodes (ηV)")
    eta_e: float = Field(0.125, gt=0, lt=0.5, description="Max fraction failed PPEs (ηE)")
    
    # Derived parameters
    p: Optional[float] = Field(None, description="Edge probability (d/m)")
    b: Optional[float] = Field(None, description="Expansion parameter")
    
    class Config:
        json_schema_extra = {
            "example": {
                "m": 1000,
                "d": 60,
                "kappa": 40,
                "eta_v": 0.025,
                "eta_e": 0.125
            }
        }
    
    @validator('p', always=True)
    def calculate_p(cls, v, values):
        """Calculate edge probability if not provided."""
        if v is None and 'm' in values and 'd' in values:
            return values['d'] / values['m']
        return v
    
    @validator('b', always=True)
    def calculate_b(cls, v, values):
        """Calculate expansion parameter if not provided."""
        if v is None and 'd' in values and 'm' in values and 'eta_v' in values:
            d = values['d']
            m = values['m']
            eta_v = values['eta_v']
            
            if m > 1:
                numerator = d * (0.5 - eta_v)
                denominator = 2 * math.log(m) - 2
                if denominator > 0:
                    return math.sqrt(numerator / denominator)
        return v


class ParameterValidationResult(BaseModel):
    """Result of parameter validation."""
    
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Constraint satisfaction details
    constraint_1_satisfied: bool = False  # Minimum nodes
    constraint_2_satisfied: bool = False  # Edge probability bounds
    constraint_3_satisfied: bool = False  # Expansion parameter
    constraint_4_satisfied: bool = False  # Failed PPE threshold
    constraint_5_satisfied: bool = False  # Minimum degree
    constraint_6_satisfied: bool = False  # Sybil bound validity
    
    # Calculated values
    calculated_values: Dict[str, float] = Field(default_factory=dict)
    
    # Security metrics
    estimated_sybil_resistance: Optional[float] = None
    estimated_completion_rate: Optional[float] = None


class PollParameters(Base):
    """
    Store validated parameters for a poll.
    """
    __tablename__ = "poll_parameters"
    
    poll_id = Column(String, primary_key=True)
    
    # Core parameters
    m = Column(Integer, nullable=False)  # Expected participants
    d = Column(Float, nullable=False)     # Expected degree
    kappa = Column(Integer, default=40)   # Security parameter
    eta_v = Column(Float, default=0.025)  # Max deleted nodes fraction
    eta_e = Column(Float, default=0.125)  # Max failed PPEs fraction
    
    # Derived parameters
    p = Column(Float, nullable=False)     # Edge probability
    b = Column(Float, nullable=True)      # Expansion parameter
    
    # Validation status
    validated = Column(Boolean, default=False)
    validation_result = Column(JSON, nullable=True)
    
    # Security level
    security_level = Column(String, default="medium")  # high/medium/low
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "poll_id": self.poll_id,
            "m": self.m,
            "d": self.d,
            "kappa": self.kappa,
            "eta_v": self.eta_v,
            "eta_e": self.eta_e,
            "p": self.p,
            "b": self.b,
            "validated": self.validated,
            "security_level": self.security_level
        }


class SecurityLevel(BaseModel):
    """Security level configuration."""
    
    name: str = Field(..., description="Security level name")
    description: str = Field(..., description="What this level provides")
    
    # Recommended parameters
    recommended_d: int = Field(..., description="Recommended degree")
    recommended_kappa: int = Field(..., description="Recommended security param")
    recommended_eta_v: float = Field(..., description="Recommended ηV")
    recommended_eta_e: float = Field(..., description="Recommended ηE")
    
    # Expected outcomes
    sybil_resistance_percentage: float = Field(..., description="% resistance to Sybil attacks")
    user_effort_description: str = Field(..., description="User effort level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "high",
                "description": "Maximum security, suitable for high-stakes decisions",
                "recommended_d": 80,
                "recommended_kappa": 80,
                "recommended_eta_v": 0.01,
                "recommended_eta_e": 0.1,
                "sybil_resistance_percentage": 98.0,
                "user_effort_description": "High - 80 verifications required"
            }
        }