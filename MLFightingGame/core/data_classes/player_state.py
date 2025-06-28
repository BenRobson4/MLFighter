from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from ..globals.actions import Action
from ..globals.states import State


@dataclass
class PlayerState:
    """Represents the state of a player/fighter"""
    
    # Identity
    player_id: int = 0 # 1 or 2
    fighter_name: str  = None # 'aggressive', 'defensive', etc.
    
    # Physics properties
    x: float = 0.0
    start_x: float = 0.0
    y: float = 0.0
    start_y: float = 0.0
    is_grounded: bool = True  # True if on the ground, False if in the air
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    facing_right: bool = True
    gravity: float = 1  # Customizable per fighter
    friction: float = 0.1  # Customizable per fighter
    width: int = 50
    height: int = 100
    
    # Combat properties
    health: float = 100.0
    max_health: float = 100.0
    damage_reduction: float = 0.0  # Percentage reduction from incoming damage
    move_speed: float = 5.0  # Speed of movement in pixels per frame
    jump_force: float = 10.0  # Force applied when jumping
    attack_damage: float = 10.0
    x_attack_range: float = 80.0
    y_attack_range: float = 40.0
    on_hit_stun: int = 1 # Frames the enemy is stunned for when a hit lands
    on_block_stun: int = 2 # Frames the enemy is stunned for when their attack is successfully blocked
    block_efficiency: float = 0.75  # Damage reduction when blocking
    
    # Action state
    last_action_frame: int = 0 # Frame the last action was performed
    action_complete: bool = True # Whether the last action has completed (used for ML agents' rewards)
    current_state: State = State.IDLE  # Current state of the player
    state_frame_counter: int = 0 # Frames in current state
    
    # Status flags
    jump_cooldown: int = 30 # Minimum frames between jumps
    jump_cooldown_remaining: int = 0 # Frames before player can jump again after landing

    attack_cooldown: int = 20 # Minimum frames between attacks
    attack_cooldown_remaining: int = 0 # Frames before player can attack again
    current_attack_landed: bool = False # Whether the current attack has landed on the opponent

    block_cooldown: int = 15 # Minimum frames between blocks
    block_cooldown_remaining: int = 0 # Frames before player can block again

    got_stunned: bool = False # Flag whether the player got stunned this frame
    stun_frames_remaining: int = 0 # Frames remaining in stun state
    
    # Last action decision info
    last_action_state: Optional[np.ndarray] = None
    last_action_choice: Optional[Action] = None
    requested_action: Optional[Action] = None
    accumulated_reward: float = 0.0 # Reward accumulated for the current action
    total_reward: float = 0.0 # Total reward accumulated for the player

    frame_data: Dict[Action, List] = None
    
    def __post_init__(self):
        if self.frame_data is None:
            self.frame_data = {
                Action.LEFT: [1, 10, 0],
                Action.RIGHT: [1, 10, 0],
                Action.JUMP: [10, 1, 20],
                Action.BLOCK: [5, 25, 15],
                Action.ATTACK: [10, 30, 20],
                Action.IDLE: [0, 0, 0]
            }
    
