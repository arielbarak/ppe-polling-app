"""
Factory for creating PPE mechanism instances.

Handles registration and instantiation of different PPE types.
"""

from typing import Dict, Type, Optional
from .base import BasePPE, PPEType, PPEDifficulty, PPEMetadata
from .symmetric_captcha import SymmetricCaptchaPPE


class PPEFactory:
    """
    Factory for creating PPE mechanism instances.
    
    Supports plugin registration for custom PPE types.
    """
    
    def __init__(self):
        # Registry of available PPE implementations
        self._registry: Dict[PPEType, Type[BasePPE]] = {}
        self._metadata: Dict[PPEType, PPEMetadata] = {}
        
        # Register built-in implementations
        self._register_builtin()
    
    def _register_builtin(self):
        """Register built-in PPE implementations."""
        self.register(
            SymmetricCaptchaPPE,
            PPEMetadata(
                ppe_type=PPEType.SYMMETRIC_CAPTCHA,
                name="Symmetric CAPTCHA",
                description="Text-based CAPTCHA solved by both parties",
                requires_human=True,
                supports_batch=False,
                client_library_required=False
            )
        )
    
    def register(self, ppe_class: Type[BasePPE], metadata: PPEMetadata):
        """
        Register a new PPE implementation.
        
        Args:
            ppe_class: The PPE implementation class
            metadata: Metadata about the implementation
        """
        # Verify it's a valid PPE class
        if not issubclass(ppe_class, BasePPE):
            raise ValueError(f"{ppe_class.__name__} must inherit from BasePPE")
        
        self._registry[metadata.ppe_type] = ppe_class
        self._metadata[metadata.ppe_type] = metadata
        
        print(f"Registered PPE type: {metadata.name} ({metadata.ppe_type.value})")
    
    def create(self, ppe_type: PPEType, 
               difficulty: PPEDifficulty = PPEDifficulty.MEDIUM) -> BasePPE:
        """
        Create a PPE instance.
        
        Args:
            ppe_type: Type of PPE to create
            difficulty: Challenge difficulty
            
        Returns:
            PPE instance
            
        Raises:
            ValueError: If PPE type not registered
        """
        if ppe_type not in self._registry:
            raise ValueError(f"PPE type {ppe_type.value} not registered")
        
        ppe_class = self._registry[ppe_type]
        return ppe_class(difficulty=difficulty)
    
    def get_available_types(self) -> Dict[str, Dict]:
        """
        Get all available PPE types with metadata.
        
        Returns:
            Dictionary mapping type names to metadata
        """
        return {
            ppe_type.value: metadata.to_dict()
            for ppe_type, metadata in self._metadata.items()
        }
    
    def get_metadata(self, ppe_type: PPEType) -> Optional[PPEMetadata]:
        """
        Get metadata for a specific PPE type.
        
        Args:
            ppe_type: PPE type
            
        Returns:
            Metadata or None if not found
        """
        return self._metadata.get(ppe_type)
    
    def is_registered(self, ppe_type: PPEType) -> bool:
        """
        Check if a PPE type is registered.
        
        Args:
            ppe_type: PPE type to check
            
        Returns:
            True if registered
        """
        return ppe_type in self._registry


# Singleton instance
ppe_factory = PPEFactory()