from typing import Dict, Any, Tuple, Optional
import numpy as np
from ..data_classes import PlayerState
from ..globals.constants import MAX_X_VELOCITY, MAX_Y_VELOCITY, MAX_FRAMES
from ..globals import State

class GameState:
    """Represents the complete state of the game"""
    
    def __init__(self, arena_width: int = 800, arena_height: int = 400, 
                 player1_state: Optional[PlayerState] = None, 
                 player2_state: Optional[PlayerState] = None):
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.ground_level = arena_height - 50  # Floor height
        
        # Players
        self.players: Dict[int, PlayerState] = {
            1: player1_state,
            2: player2_state
        }
        
        # Game state
        self.max_frames = MAX_FRAMES 
        self.game_over = False
        self.winner = None
        
        # Combat events
        self.hits_this_frame = []
        self.blocks_this_frame = []
    
    def get_player(self, player_id: int) -> PlayerState:
        """Get player by ID"""
        return self.players[player_id]
    
    def get_opponent(self, player_id: int) -> PlayerState:
        """Get opponent of given player"""
        return self.players[2 if player_id == 1 else 1]
    
    def get_distance_between_players(self) -> Tuple[float, float]:
        """Get distance between players (x, y)"""
        p1 = self.players[1]
        p2 = self.players[2]
        
        return abs(p2.x - p1.x), abs(p2.y - p1.y)
    
    def get_state_vector(self, player_id: int) -> np.ndarray:
        """
        Get normalized state vector for ML agent
        
        This includes all relevant game state information for decision making,
        normalized to appropriate ranges.
        """
        player = self.get_player(player_id)
        opponent = self.get_opponent(player_id)

        player_is_jumping = player.current_state in [State.JUMP_ACTIVE, State.JUMP_RISING, State.JUMP_FALLING]
        opponent_is_jumping = opponent.current_state in [State.JUMP_ACTIVE, State.JUMP_RISING, State.JUMP_FALLING]
        
        # Create feature vector
        features = [
            player.x / self.arena_width,                                            # player_x
            player.y / self.arena_height,                                           # player_y
            player.health / player.max_health,                                      # player_health
            player.velocity_x / MAX_X_VELOCITY,                                     # player_velocity_x
            player.velocity_y / MAX_Y_VELOCITY,                                     # player_velocity_y
            float(player_is_jumping),                                               # player_is_jumping
            float(player.current_state == State.BLOCK_ACTIVE),                      # player_is_blocking
            float(player.current_state == State.ATTACK_ACTIVE),                     # player_is_attacking
            player.attack_cooldown_remaining / player.attack_cooldown,              # player_attack_cooldown
            
            opponent.x / self.arena_width,                                          # opponent_x
            opponent.y / self.arena_height,                                         # opponent_y
            opponent.health / opponent.max_health,                                  # opponent_health
            opponent.velocity_x / MAX_X_VELOCITY,                                   # opponent_velocity_x
            opponent.velocity_y / MAX_Y_VELOCITY,                                   # opponent_velocity_y
            float(opponent_is_jumping),                                             # opponent_is_jumping
            float(opponent.current_state == State.BLOCK_ACTIVE),                    # opponent_is_blocking
            float(opponent.current_state == State.ATTACK_ACTIVE),                   # opponent_is_attacking
            opponent.attack_cooldown_remaining / opponent.attack_cooldown,          # opponent_attack_cooldown
            
            abs(opponent.x - player.x) / self.arena_width,                          # distance_x
            abs(opponent.y - player.y) / self.arena_height                          # distance_y
        ]
        
        return np.array(features, dtype=np.float32)
    
    def clone(self) -> 'GameState':
        """Create a deep copy of the game state"""
        import copy
        return copy.deepcopy(self)