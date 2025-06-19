from abc import ABC, abstractmethod
import numpy as np
from ..core import Action

class MLAgent(ABC):
    """Abstract base class for ML agents"""
    
    @abstractmethod
    def get_action(self, state: np.ndarray) -> Action:
        """Given game state, return the action to take"""
        pass
    
    @abstractmethod
    def update(self, state: np.ndarray, action: Action, reward: float, 
               next_state: np.ndarray, done: bool):
        """Update the model with experience"""
        pass