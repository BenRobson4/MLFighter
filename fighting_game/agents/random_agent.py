import numpy as np
from .base_agent import MLAgent
from ..core import Action

class RandomAgent(MLAgent):
    """Simple random agent for testing"""
    def __init__(self):
        self.epsilon = 1 # Not used just here for consistency with other agents
    
    def get_action(self, state: np.ndarray) -> Action:
        return Action(np.random.randint(0, len(Action)))
    
    def update(self, state: np.ndarray, action: Action, reward: float,
               next_state: np.ndarray, done: bool):
        pass  # Random agent doesn't learn