from typing import Dict, Any, Tuple, Optional
import numpy as np
from ..data_classes import PlayerState
from ..globals.constants import MAX_X_VELOCITY, MAX_Y_VELOCITY

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
        self.current_frame = 0
        self.max_frames = 1800  # 60 seconds @ 60 FPS
        self.game_over = False
        self.winner = None
        
        # Combat events
        self.hits_this_frame = []
        self.blocks_this_frame = []
        
        # Initialize player positions
        self._initialize_positions()
    
    def _initialize_positions(self):
        """Initialize player positions at the start of the game"""
        p1 = self.players[1]
        p2 = self.players[2]
        
        p1.x = self.arena_width * 0.25
        p1.y = self.floor_y
        p1.facing_right = True
        
        p2.x = self.arena_width * 0.75
        p2.y = self.floor_y
        p2.facing_right = False
    
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
        
        # Create feature vector
        features = [
            player.x / self.arena_width,                                            # player_x
            player.y / self.arena_height,                                           # player_y
            player.health / player.max_health,                                      # player_health
            player.velocity_x / MAX_X_VELOCITY,                                     # player_velocity_x
            player.velocity_y / MAX_Y_VELOCITY,                                     # player_velocity_y
            float(player.is_jumping),                                               # player_is_jumping
            float(player.is_blocking),                                              # player_is_blocking
            float(player.is_attacking),                                             # player_is_attacking
            player.remaining_attack_cooldown / player.attack_cooldown,              # player_attack_cooldown
            
            opponent.x / self.arena_width,                                          # opponent_x
            opponent.y / self.arena_height,                                         # opponent_y
            opponent.health / opponent.max_health,                                  # opponent_health
            opponent.velocity_x / MAX_X_VELOCITY,                                   # opponent_velocity_x
            opponent.velocity_y / MAX_Y_VELOCITY,                                   # opponent_velocity_y
            float(opponent.is_jumping),                                             # opponent_is_jumping
            float(opponent.is_blocking),                                            # opponent_is_blocking
            float(opponent.is_attacking),                                           # opponent_is_attacking
            opponent.remaining_attack_cooldown / opponent.attack_cooldown,          # opponent_attack_cooldown
            
            abs(opponent.x - player.x) / self.arena_width,                          # distance_x
            abs(opponent.y - player.y) / self.arena_height                          # distance_y
        ]
        
        return np.array(features, dtype=np.float32)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to dictionary for reward calculation"""
        p1 = self.players[1]
        p2 = self.players[2]
        
        return {
            'current_frame': self.current_frame,
            'arena_width': self.arena_width,
            'arena_height': self.arena_height,
            'game_over': self.game_over,
            'winner': self.winner,
            'max_health': p1.max_health,  # Assuming same for both
            
            'player1': {
                'x': p1.x,
                'y': p1.y,
                'health': p1.health,
                'velocity_x': p1.velocity_x,
                'velocity_y': p1.velocity_y,
                'is_jumping': p1.is_jumping,
                'is_blocking': p1.is_blocking,
                'is_attacking': p1.is_attacking,
                'is_stunned': p1.is_stunned,
                'attack_cooldown': p1.attack_cooldown,
                'current_action': p1.current_action.name,
                'action_frame': p1.action_frame_counter,
                'action_total_frames': p1.action_total_frames,
            },
            
            'player2': {
                'x': p2.x,
                'y': p2.y,
                'health': p2.health,
                'velocity_x': p2.velocity_x,
                'velocity_y': p2.velocity_y,
                'is_jumping': p2.is_jumping,
                'is_blocking': p2.is_blocking,
                'is_attacking': p2.is_attacking,
                'is_stunned': p2.is_stunned,
                'attack_cooldown': p2.attack_cooldown,
                'current_action': p2.current_action.name,
                'action_frame': p2.action_frame_counter,
                'action_total_frames': p2.action_total_frames,
            },
            
            'hits_this_frame': self.hits_this_frame,
            'blocks_this_frame': self.blocks_this_frame,
            'distance_x': abs(p2.x - p1.x),
            'distance_y': abs(p2.y - p1.y),
        }
    
    def is_game_over(self) -> bool:
        """Check if game is over"""
        # Game ends if time is up or a player has 0 health
        if self.current_frame >= self.max_frames:
            self.game_over = True
            # Determine winner based on health
            p1_health = self.players[1].health
            p2_health = self.players[2].health
            if p1_health > p2_health:
                self.winner = 1
            elif p2_health > p1_health:
                self.winner = 2
            else:
               # Tiebreak condition is whichever player is closer to the centre
                p1_distance_from_center = abs(self.players[1].x - self.arena_width / 2)
                p2_distance_from_center = abs(self.players[2].x - self.arena_width / 2)
                if p1_distance_from_center < p2_distance_from_center:
                    self.winner = 1
                else:
                    self.winner = 2

        
        # Check for KO
        for player_id, player in self.players.items():
            if player.health <= 0:
                self.game_over = True
                self.winner = 2 if player_id == 1 else 1
        
        return self.game_over
    
    def clone(self) -> 'GameState':
        """Create a deep copy of the game state"""
        import copy
        return copy.deepcopy(self)