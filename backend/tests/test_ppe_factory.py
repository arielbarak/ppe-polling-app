"""
Tests for PPE factory system.
"""

import pytest
from app.ppe.factory import PPEFactory
from app.ppe.base import BasePPE, PPEType, PPEDifficulty
from app.ppe.symmetric_captcha import SymmetricCaptchaPPE


def test_factory_builtin_registration():
    """Test that built-in PPE types are registered."""
    factory = PPEFactory()
    
    assert factory.is_registered(PPEType.SYMMETRIC_CAPTCHA)
    
    available = factory.get_available_types()
    assert PPEType.SYMMETRIC_CAPTCHA.value in available


def test_factory_create_instance():
    """Test creating PPE instances."""
    factory = PPEFactory()
    
    ppe = factory.create(PPEType.SYMMETRIC_CAPTCHA, PPEDifficulty.MEDIUM)
    
    assert isinstance(ppe, BasePPE)
    assert isinstance(ppe, SymmetricCaptchaPPE)
    assert ppe.difficulty == PPEDifficulty.MEDIUM


def test_factory_invalid_type():
    """Test creating invalid PPE type raises error."""
    factory = PPEFactory()
    
    with pytest.raises(ValueError):
        factory.create(PPEType.PROOF_OF_WORK)  # Not registered


def test_symmetric_captcha_interface():
    """Test Symmetric CAPTCHA implements interface correctly."""
    ppe = SymmetricCaptchaPPE(PPEDifficulty.MEDIUM)
    
    # Test challenge generation
    challenge, solution = ppe.generate_challenge_with_secret("secret", "session")
    assert challenge is not None
    assert solution is not None
    
    # Test verification
    assert ppe.verify_challenge_generation("secret", "session", challenge, solution)
    
    # Test solution verification
    assert ppe.verify_solution(challenge, solution)
    
    # Test effort estimation
    assert ppe.estimate_effort() > 0


def test_symmetric_captcha_deterministic():
    """Test that challenge generation is deterministic."""
    ppe = SymmetricCaptchaPPE(PPEDifficulty.MEDIUM)
    
    # Generate same challenge twice
    challenge1, solution1 = ppe.generate_challenge_with_secret("secret", "session")
    challenge2, solution2 = ppe.generate_challenge_with_secret("secret", "session")
    
    # Should be identical
    assert challenge1 == challenge2
    assert solution1 == solution2


def test_symmetric_captcha_different_secrets():
    """Test that different secrets produce different challenges."""
    ppe = SymmetricCaptchaPPE(PPEDifficulty.MEDIUM)
    
    challenge1, solution1 = ppe.generate_challenge_with_secret("secret1", "session")
    challenge2, solution2 = ppe.generate_challenge_with_secret("secret2", "session")
    
    # Should be different
    assert challenge1 != challenge2
    assert solution1 != solution2


def test_symmetric_captcha_difficulty_levels():
    """Test different difficulty levels."""
    # Easy
    ppe_easy = SymmetricCaptchaPPE(PPEDifficulty.EASY)
    challenge_easy, solution_easy = ppe_easy.generate_challenge_with_secret("secret", "session")
    
    # Medium
    ppe_medium = SymmetricCaptchaPPE(PPEDifficulty.MEDIUM)
    challenge_medium, solution_medium = ppe_medium.generate_challenge_with_secret("secret", "session")
    
    # Hard
    ppe_hard = SymmetricCaptchaPPE(PPEDifficulty.HARD)
    challenge_hard, solution_hard = ppe_hard.generate_challenge_with_secret("secret", "session")
    
    # Different difficulties should produce different lengths
    assert len(solution_easy.replace(' ', '')) != len(solution_medium.replace(' ', ''))
    assert len(solution_medium.replace(' ', '')) != len(solution_hard.replace(' ', ''))


def test_ppe_metadata():
    """Test PPE metadata functionality."""
    factory = PPEFactory()
    
    metadata = factory.get_metadata(PPEType.SYMMETRIC_CAPTCHA)
    assert metadata is not None
    assert metadata.name == "Symmetric CAPTCHA"
    assert metadata.requires_human == True


def test_ppe_client_config():
    """Test PPE client configuration."""
    ppe = SymmetricCaptchaPPE(PPEDifficulty.MEDIUM)
    
    config = ppe.get_client_config()
    assert config["type"] == "symmetric_captcha"
    assert config["difficulty"] == "medium"
    assert "estimated_effort" in config


def test_ppe_serialization():
    """Test PPE challenge serialization."""
    ppe = SymmetricCaptchaPPE(PPEDifficulty.MEDIUM)
    
    challenge, solution = ppe.generate_challenge_with_secret("secret", "session")
    
    # Test serialization
    serialized = ppe.serialize_challenge(challenge)
    assert serialized["type"] == "symmetric_captcha"
    assert serialized["data"] == challenge
    
    # Test deserialization
    deserialized = ppe.deserialize_challenge(serialized)
    assert deserialized == challenge