from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from ..globals.actions import Action


@dataclass
class PlayerState:
    """Represents the state of a player/fighter"""
    
    # Identity
    player_id: int  # 1 or 2
    fighter_type: str  # 'aggressive', 'defensive', etc.
    
    # Physics properties
    x: float = 0.0
    y: float = 0.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    facing_right: bool = True
    gravity: float = 9.8  # Customizable per fighter
    friction: float = 0.1  # Customizable per fighter
    width: int = 50
    height: int = 100
    
    # Combat properties
    health: float = 100.0
    max_health: float = 100.0
    damage_reduction: float = 0.0  # Percentage reduction from incoming damage
    attack_damage: float = 10.0
    x_attack_range: float = 80.0
    y_attack_range: float = 40.0
    on_hit_stun: int = 1 # Frames the enemy is stunned for when a hit lands
    on_block_stun: int = 2 # Frames the enemy is stunned for when their attack is successfully blocked
    block_efficiency: float = 0.75  # Damage reduction when blocking
    
    # Action state
    current_action: Action = Action.IDLE
    action_frame_counter: int = 0 # Frames since action started
    action_total_frames: int = 0 # Total frames for current action
    is_actionable: bool = True
    
    # Status flags
    is_jumping: bool = False
    jump_cooldown: int = 30 # Minimum frames between jumps
    jump_cooldown_remaining: int = 0 # Frames before player can jump again after landing

    is_attacking: bool = False
    attack_cooldown: int = 20 # Minimum frames between attacks
    attack_cooldown_remaining: int = 0 # Frames before player can attack again

    is_blocking: bool = False
    block_cooldown: int = 15 # Minimum frames between blocks
    block_cooldown_remaining: int = 0 # Frames before player can block again

    is_stunned: bool = False
    stun_frames_remaining: int = 0 # Frames remaining in stun state
    
    # Action durations (frames)
    action_durations: Dict[Action, int] = None
    
    # Last action decision info
    last_action_state: Optional[np.ndarray] = None
    last_action_choice: Optional[Action] = None
    requested_action: Optional[Action] = None
    accumulated_reward: float = 0.0
    reward_components: Dict[str, float] = None
    
    def __post_init__(self):
        if self.action_durations is None:
            self.action_durations = {
                Action.LEFT: 1,
                Action.RIGHT: 1,
                Action.JUMP: 20,
                Action.BLOCK: 15,
                Action.ATTACK: 12,
                Action.IDLE: 1
            }
        
        if self.reward_components is None:
            self.reward_components = {}
    
    def get_hitbox(self) -> Tuple[float, float, float, float]:
        """Get current hitbox as (x1, y1, x2, y2)"""
        return (
            self.x - self.width / 2,
            self.y - self.height / 2,
            self.x + self.width / 2,
            self.y + self.height / 2
        )
    
    def get_attack_hitbox(self) -> Optional[Tuple[float, float, float, float]]:
        """Get attack hitbox if currently attacking"""
        if not self.is_attacking:
            return None
        
        # Determine attack direction based on facing
        direction = 1 if self.facing_right else -1
        attack_x_offset = self.width / 2 * direction
        
        return (
            self.x + attack_x_offset,
            self.y - self.y_attack_range/ 2,
            self.x + attack_x_offset + self.x_attack_range * direction,
            self.y + self.y_attack_range/ 2
        )
    
    def can_take_action(self) -> bool:
        """Check if player can take a new action"""
        if self.is_stunned:
            return False
        return self.action_frame_counter >= self.action_total_frames

    def is_action_allowed(self, action: Action) -> bool:
        """Check if a specific action is allowed given current game state"""
        if action == Action.ATTACK and self.attack_cooldown_remaining > 0:
            return False
        
        if action == Action.BLOCK and self.block_cooldown_remaining > 0:
            return False
        
        if action == Action.JUMP and self.y < 0:
            return False
        
        if action == Action.JUMP and self.jump_cooldown_remaining > 0:
            return False
        
        return True

    def commit_to_action(self, action: Action):
        """Commit to a new action and update frame counters"""
        self.current_action = action
        self.action_frame_counter = 0
        self.action_total_frames = self.action_durations[action]
