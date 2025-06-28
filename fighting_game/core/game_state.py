import numpy as np
from typing import Dict, Optional
from ..config.fighter_config import Fighter
from ..config.global_constants import ARENA_WIDTH, ARENA_HEIGHT
from .actions import Action

class GameState:
    """Represents the current state of the fighting game"""
    
    def __init__(self, arena_width: int = ARENA_WIDTH, arena_height: int = ARENA_HEIGHT, 
                 player1_stats: Optional[Fighter] = None, 
                 player2_stats: Optional[Fighter] = None):
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.ground_level = arena_height - 100
        
        # Store player stats for reference
        self.player1_stats = player1_stats
        self.player2_stats = player2_stats
        
        # Player states
        self.players = {
            'player1': self._create_player_state(self.arena_width/5, player1_stats),
            'player2': self._create_player_state(4*self.arena_width/5, player2_stats)
        }
        
        self.game_over = False
        self.winner: Optional[str] = None
        self.frame_count = 0
        
    def _create_player_state(self, x_pos: int, player_stats: Optional[Fighter] = None) -> Dict:
        """Create initial player state"""
        health = player_stats.health if player_stats else 100
        
        return {
            'x': x_pos,
            'y': self.ground_level,
            'velocity_x': 0,
            'velocity_y': 0,
            'health': health,
            'is_jumping': False,
            'is_blocking': False,
            'is_attacking': False,
            'attack_cooldown': 0,  # Keep for backward compatibility
            'facing_right': True,
            
            # Frame data tracking
            'current_action': Action.IDLE,
            'action_frame': 0,  # Current frame of the action
            'action_locked': False,  # Whether input is locked
            'input_buffer': None,  # Buffered input during locked state
            
            # Attack hit tracking
            'has_hit_opponent': False,  # Whether current attack has already hit
            'attack_id': 0,  # Unique ID for each attack to track hits
        }
        
    def get_state_vector(self, player_id: str) -> np.ndarray:
        """Convert game state to feature vector for ML model"""
        p1 = self.players['player1']
        p2 = self.players['player2']
        
        # Get max health for normalization (use actual fighter health, or default to 100)
        p1_max_health = self.player1_stats.health if self.player1_stats else 100
        p2_max_health = self.player2_stats.health if self.player2_stats else 100
        
        # Get max speeds for normalization
        p1_max_speed = self.player1_stats.move_speed if self.player1_stats else 10
        p2_max_speed = self.player2_stats.move_speed if self.player2_stats else 10
        p1_max_jump = abs(self.player1_stats.jump_force) if self.player1_stats else 15
        p2_max_jump = abs(self.player2_stats.jump_force) if self.player2_stats else 15
        p1_max_cooldown = self.player1_stats.attack_cooldown if self.player1_stats else 30
        p2_max_cooldown = self.player2_stats.attack_cooldown if self.player2_stats else 30
        
        # Normalize positions and create relative features
        features = [
            p1['x'] / self.arena_width,
            p1['y'] / self.arena_height,
            p1['health'] / p1_max_health,
            p1['velocity_x'] / p1_max_speed,
            p1['velocity_y'] / p1_max_jump,
            int(p1['is_jumping']),
            int(p1['is_blocking']),
            int(p1['is_attacking']),
            p1['attack_cooldown'] / p1_max_cooldown,
            
            p2['x'] / self.arena_width,
            p2['y'] / self.arena_height,
            p2['health'] / p2_max_health,
            p2['velocity_x'] / p2_max_speed,
            p2['velocity_y'] / p2_max_jump,
            int(p2['is_jumping']),
            int(p2['is_blocking']),
            int(p2['is_attacking']),
            p2['attack_cooldown'] / p2_max_cooldown,
            
            # Distance between players
            abs(p1['x'] - p2['x']) / self.arena_width,
            abs(p1['y'] - p2['y']) / self.arena_height,
        ]
        
        return np.array(features, dtype=np.float32)