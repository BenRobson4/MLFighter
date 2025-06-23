from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np
from ..game_loop.game_state import GameState


class RewardEvent(ABC):
    """Base class for all reward events"""
    
    # Metadata (to be overridden by subclasses)
    name: str = None
    description: str = None
    category: str = "general"  # e.g., "distance", "health", "combat", "position"
    range: tuple = (0, 1)  # Expected output range
    higher_is_better: bool = True  # Whether higher values are desirable
    is_continuous: bool = True  # Whether the reward is continuous or discrete
    
    def __init__(self):
        if self.name is None:
            # Auto-generate name from class name if not provided
            self.name = self.__class__.__name__.replace('Reward', '').lower()
    
    @abstractmethod
    def measure(self, game_state: GameState, player_id: int) -> float:
        """
        Calculate the reward value for this event
        
        Args:
            game_state: Current state of the game
            player_id: ID of the player for whom the reward is being calculated
            
        Returns:
            Normalized reward value (typically 0-1)
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get metadata about this reward event"""
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'range': self.range,
            'higher_is_better': self.higher_is_better,
            'is_continuous': self.is_continuous,
            'class': self.__class__.__name__
        }
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"