from typing import Optional, Dict, Any
from ...data_classes import Fighter
from .fighter_registry import FighterRegistry


class FighterFactory:
    """Factory for creating fighter instances"""
    
    @staticmethod
    def create_fighter(fighter_name: str, **kwargs) -> Optional[Fighter]:
        """
        Create a fighter instance by name
        
        Args:
            fighter_name: Name of the fighter class
            **kwargs: Optional overrides for fighter attributes
        
        Returns:
            Fighter instance or None if not found
        """
        # Auto-discover fighters if not done already
        if not FighterRegistry._fighters:
            FighterRegistry.auto_discover()
        
        fighter_class = FighterRegistry.get_fighter(fighter_name)
        if not fighter_class:
            print(f"Fighter '{fighter_name}' not found")
            return None
        
        # Create fighter instance
        fighter = fighter_class()
        
        # Apply any overrides
        for key, value in kwargs.items():
            if hasattr(fighter, key):
                setattr(fighter, key, value)
        
        return fighter
    
    @staticmethod
    def list_available_fighters() -> Dict[str, Dict[str, Any]]:
        """
        List all available fighters with metadata
        
        Returns:
            Dictionary mapping fighter names to metadata
        """
        # Auto-discover fighters if not done already
        if not FighterRegistry._fighters:
            FighterRegistry.auto_discover()
        
        result = {}
        for name, fighter_class in FighterRegistry._fighters.items():
            result[name] = fighter_class.get_metadata()
        
        return result