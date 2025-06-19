import numpy as np
from .base_agent import MLAgent
from ..core import Action

class SimpleAgent(MLAgent):
    """A simple agent that runs to the center and attacks left."""

    def __init__(self):
        self.epsilon = 0 # Not used, but 0 to show no exploration
    
    def get_action(self, state: np.ndarray) -> Action:
        # Always move towards the center and attack left
        if state['player1']['x'] < 0.5:
            action = 1 # Move right

        elif state['player1']['x'] > 0.5:
            action = 0 # Move left
        
        else:
            action = 4 # Attack
        
        return Action(action)
    
    def update(self, state: np.ndarray, action: Action, reward: float,
               next_state: np.ndarray, done: bool):
        # Simple agent does not learn from experience
        pass