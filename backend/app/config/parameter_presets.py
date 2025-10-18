"""
Parameter presets for common security levels.
"""

from typing import Dict
from app.models.poll_parameters import SecurityLevel


SECURITY_PRESETS: Dict[str, SecurityLevel] = {
    "high": SecurityLevel(
        name="high",
        description="Maximum security - suitable for critical decisions (elections, governance)",
        recommended_d=80,
        recommended_kappa=80,
        recommended_eta_v=0.01,
        recommended_eta_e=0.1,
        sybil_resistance_percentage=98.0,
        user_effort_description="High - approximately 80 verifications required per user"
    ),
    
    "medium": SecurityLevel(
        name="medium",
        description="Balanced security and usability - suitable for most polls",
        recommended_d=60,
        recommended_kappa=40,
        recommended_eta_v=0.025,
        recommended_eta_e=0.125,
        sybil_resistance_percentage=95.0,
        user_effort_description="Medium - approximately 60 verifications required per user"
    ),
    
    "low": SecurityLevel(
        name="low",
        description="Basic security - suitable for low-stakes surveys",
        recommended_d=40,
        recommended_kappa=20,
        recommended_eta_v=0.05,
        recommended_eta_e=0.15,
        sybil_resistance_percentage=90.0,
        user_effort_description="Low - approximately 40 verifications required per user"
    ),
    
    "custom": SecurityLevel(
        name="custom",
        description="Manually configure all parameters",
        recommended_d=60,
        recommended_kappa=40,
        recommended_eta_v=0.025,
        recommended_eta_e=0.125,
        sybil_resistance_percentage=0.0,
        user_effort_description="Configure manually"
    )
}


def get_preset(security_level: str) -> SecurityLevel:
    """Get security level preset."""
    return SECURITY_PRESETS.get(security_level, SECURITY_PRESETS["medium"])


def get_all_presets() -> Dict[str, SecurityLevel]:
    """Get all available presets."""
    return SECURITY_PRESETS