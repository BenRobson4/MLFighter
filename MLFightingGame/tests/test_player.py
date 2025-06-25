import numpy as np

from ..core.players.player import Player
from ..core.globals import Action


class TestPlayer(Player):
    """Test player that returns a predetermined action"""

    def __init__(self, player_id: int, fighter_name: str, fixed_action: Action = Action.IDLE):
        """
        Initialize test player with a fixed action
        
        Args:
            player_id: The player ID (1 or 2)
            fighter_name: Name of the fighter to load from JSON
            fixed_action: The action this player will always return
        """
        super().__init__(player_id=player_id, fighter_name=fighter_name)
        self.fixed_action = fixed_action
        self.actions_taken = 0

    def get_action(self, state_vector: np.ndarray) -> Action:
        """Always return the fixed action"""
        self.actions_taken += 1
        return self.fixed_action

    def set_fixed_action(self, action: Action):
        """Update the fixed action for testing different scenarios"""
        self.fixed_action = action