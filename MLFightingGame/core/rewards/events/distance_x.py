from ..base_reward import RewardEvent
from ..reward_registry import RewardRegistry
from typing import Dict, Any
from ...globals.constants import ARENA_WIDTH


@RewardRegistry.register
class DistanceX(RewardEvent):
    """Reward for landing an attack"""
    
    def __init__(self):
        super().__init__(
            name="distance_x",
            description="horizontal distance between the two players",
            category='Distance',
            higher_is_better=False,
            is_continuous=True
        )
    
    def measure(self, game_state: Dict[str, Any]) -> float:
        # Returns the normalised distance between the two players
        p1_x = game_state['player1']['x']
        p2_x = game_state['player2']['x']

        return abs(p1_x - p2_x)/ARENA_WIDTH