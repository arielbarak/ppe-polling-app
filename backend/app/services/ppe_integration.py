"""
PPE service integration utilities.
Helper functions to integrate the new PPE types into existing poll services.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.ppe_types import PPEType, PPEConfig, PPEDifficulty


def create_default_ppe_config(
    poll_id: str,
    db: Session,
    allowed_types: Optional[List[PPEType]] = None,
    default_type: PPEType = PPEType.SYMMETRIC_CAPTCHA,
    difficulty: PPEDifficulty = PPEDifficulty.MEDIUM
) -> PPEConfig:
    """
    Create a default PPE configuration for a new poll.
    
    Args:
        poll_id: Poll identifier
        db: Database session
        allowed_types: List of allowed PPE types (defaults to all basic types)
        default_type: Default PPE type to use
        difficulty: Default difficulty level
        
    Returns:
        Created PPEConfig instance
    """
    if allowed_types is None:
        # Default to basic, well-tested PPE types
        allowed_types = [
            PPEType.SYMMETRIC_CAPTCHA,
            PPEType.PROOF_OF_STORAGE,
            PPEType.COMPUTATIONAL
        ]
    
    # Check if config already exists
    existing_config = db.query(PPEConfig).filter_by(poll_id=poll_id).first()
    if existing_config:
        return existing_config
    
    # Create new configuration
    config = PPEConfig(
        poll_id=poll_id,
        
        # Registration (one-sided)
        registration_ppe_type=PPEType.REGISTRATION_CAPTCHA,
        registration_difficulty=difficulty,
        
        # Certification (two-sided)
        allowed_certification_types=allowed_types,
        default_certification_type=default_type,
        certification_difficulty=difficulty,
        
        # Security and performance parameters
        ppe_timeout=300,  # 5 minutes
        max_concurrent_ppes=3,
        completeness_sigma=0.95,
        soundness_epsilon=0.05,
        
        enable_audit_logging=True
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return config


def update_poll_ppe_config(
    poll_id: str,
    db: Session,
    **updates
) -> PPEConfig:
    """
    Update PPE configuration for an existing poll.
    
    Args:
        poll_id: Poll identifier
        db: Database session
        **updates: Configuration updates
        
    Returns:
        Updated PPEConfig instance
    """
    config = db.query(PPEConfig).filter_by(poll_id=poll_id).first()
    if not config:
        raise ValueError(f"No PPE config found for poll {poll_id}")
    
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    
    return config


def migrate_existing_polls_to_ppe_config(db: Session) -> int:
    """
    Create PPE configurations for existing polls that don't have them.
    
    Args:
        db: Database session
        
    Returns:
        Number of configs created
    """
    from app.models.user import Poll
    
    # Get all polls
    polls = db.query(Poll).all()
    
    created_count = 0
    for poll in polls:
        existing_config = db.query(PPEConfig).filter_by(poll_id=poll.id).first()
        if not existing_config:
            create_default_ppe_config(poll.id, db)
            created_count += 1
    
    return created_count


def get_recommended_ppe_types(
    poll_size: int,
    security_level: str = "medium"
) -> List[PPEType]:
    """
    Get recommended PPE types based on poll characteristics.
    
    Args:
        poll_size: Expected number of participants
        security_level: Required security level ("low", "medium", "high")
        
    Returns:
        List of recommended PPE types
    """
    recommendations = []
    
    # Always include symmetric CAPTCHA as baseline
    recommendations.append(PPEType.SYMMETRIC_CAPTCHA)
    
    if security_level in ["medium", "high"]:
        # Add proof-of-storage for medium+ security
        recommendations.append(PPEType.PROOF_OF_STORAGE)
    
    if security_level == "high" or poll_size < 100:
        # Add computational PPE for high security or small polls
        recommendations.append(PPEType.COMPUTATIONAL)
    
    if poll_size > 100:
        # Add social distance for large polls to reduce friction
        recommendations.append(PPEType.SOCIAL_DISTANCE)
    
    return recommendations


def validate_ppe_config(config: PPEConfig) -> List[str]:
    """
    Validate PPE configuration and return list of warnings/errors.
    
    Args:
        config: PPE configuration to validate
        
    Returns:
        List of validation messages (empty if valid)
    """
    issues = []
    
    # Check security parameters
    if config.completeness_sigma < 0.8:
        issues.append(f"Completeness σ={config.completeness_sigma} is quite low (recommend ≥0.8)")
    
    if config.soundness_epsilon > 0.1:
        issues.append(f"Soundness ε={config.soundness_epsilon} is quite high (recommend ≤0.1)")
    
    # Check timeout
    if config.ppe_timeout < 120:
        issues.append("PPE timeout < 2 minutes may be too short for some users")
    
    if config.ppe_timeout > 600:
        issues.append("PPE timeout > 10 minutes may be too long")
    
    # Check concurrent limits
    if config.max_concurrent_ppes > 5:
        issues.append("High concurrent PPE limit may impact performance")
    
    # Check PPE type consistency
    if not config.allowed_certification_types:
        issues.append("No certification PPE types allowed")
    
    if config.default_certification_type not in config.allowed_certification_types:
        issues.append("Default certification type not in allowed types")
    
    return issues


# Integration functions for existing poll creation
def integrate_ppe_with_poll_creation():
    """
    Example integration code for existing poll creation.
    Add this to your poll creation logic.
    """
    example_code = """
    # In your poll creation function:
    
    from app.services.ppe_integration import create_default_ppe_config, get_recommended_ppe_types
    
    def create_poll(poll_data, db: Session):
        # Create poll as usual
        poll = Poll(**poll_data)
        db.add(poll)
        db.flush()  # Get poll.id
        
        # Create PPE configuration
        recommended_types = get_recommended_ppe_types(
            poll_size=poll_data.get('expected_participants', 50),
            security_level=poll_data.get('security_level', 'medium')
        )
        
        ppe_config = create_default_ppe_config(
            poll_id=poll.id,
            db=db,
            allowed_types=recommended_types
        )
        
        db.commit()
        
        return poll, ppe_config
    """
    
    print("Example integration code:")
    print(example_code)


if __name__ == "__main__":
    # Print integration example
    integrate_ppe_with_poll_creation()