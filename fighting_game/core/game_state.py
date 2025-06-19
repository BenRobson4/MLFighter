import numpy as np
from typing import Dict, Optional

class GameState:
    """Represents the current state of the fighting game"""
    
    def __init__(self, arena_width: int = 400, arena_height: int = 600):
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.ground_level = arena_height - 100
        
        # Player states
        self.players = {
            'player1': self._create_player_state(200),
            'player2': self._create_player_state(300)
        }
        
        self.game_over = False
        self.winner: Optional[str] = None
        self.frame_count = 0
        
    def _create_player_state(self, x_pos: int) -> Dict:
        """Create initial player state"""
        return {
            'x': x_pos,
            'y': self.ground_level,
            'velocity_x': 0,
            'velocity_y': 0,
            'health': 100,
            'is_jumping': False,
            'is_blocking': False,
            'is_attacking': False,
            'attack_cooldown': 0,
            'facing_right': True
        }
    
    def get_state_vector(self, player_id: str) -> np.ndarray:
        """Convert game state to feature vector for ML model"""
        p1 = self.players['player1']
        p2 = self.players['player2']
        
        # Normalize positions and create relative features
        features = [
            p1['x'] / self.arena_width,
            p1['y'] / self.arena_height,
            p1['health'] / 100,
            p1['velocity_x'] / 10,  # Assuming max velocity ~10
            p1['velocity_y'] / 15,  # Assuming max jump velocity ~15
            int(p1['is_jumping']),
            int(p1['is_blocking']),
            int(p1['is_attacking']),
            p1['attack_cooldown'] / 30,  # Assuming max cooldown ~30 frames
            
            p2['x'] / self.arena_width,
            p2['y'] / self.arena_height,
            p2['health'] / 100,
            p2['velocity_x'] / 10,
            p2['velocity_y'] / 15,
            int(p2['is_jumping']),
            int(p2['is_blocking']),
            int(p2['is_attacking']),
            p2['attack_cooldown'] / 30,
            
            # Distance between players
            abs(p1['x'] - p2['x']) / self.arena_width,
            abs(p1['y'] - p2['y']) / self.arena_height,
        ]
        
        return np.array(features, dtype=np.float32)