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
    width: int = 50
    height: int = 100
    
    # Combat properties
    health: float = 100.0
    max_health: float = 100.0
    attack_power: float = 10.0
    attack_range: float = 60.0
    block_efficiency: float = 0.75  # Damage reduction when blocking
    attack_cooldown: int = 20 # Minimum frames between attacks
    
    # Action state
    current_action: Action = Action.IDLE
    action_frame_counter: int = 0
    action_total_frames: int = 0
    is_actionable: bool = True
    
    # Status flags
    is_jumping: bool = False
    is_blocking: bool = False
    is_attacking: bool = False
    is_stunned: bool = False
    remaining_attack_cooldown: int = 0 # Frames before player can attack again
    
    # Action durations (frames)
    action_durations: Dict[Action, int] = None
    
    # Last action decision info
    last_action_state: Optional[np.ndarray] = None
    last_action_choice: Optional[Action] = None
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
            self.y - self.height / 4,
            self.x + attack_x_offset + self.attack_range * direction,
            self.y + self.height / 4
        )
    
    def can_take_action(self) -> bool:
        """Check if player can take a new action"""
        return (
            self.is_actionable and
            not self.is_stunned and
            self.action_frame_counter >= self.action_total_frames and
            self.attack_cooldown <= 0
        )
    
    def commit_to_action(self, action: Action):
        """Commit to a new action"""
        self.current_action = action
        self.action_frame_counter = 0
        self.action_total_frames = self.action_durations[action]
        self.is_actionable = False
        
        # Set appropriate flags
        self.is_jumping = (action == Action.JUMP)
        self.is_blocking = (action == Action.BLOCK)
        self.is_attacking = (action == Action.ATTACK)

        if action == Action.LEFT:
            self.facing_right = False
        
        if action == Action.RIGHT:
            self.facing_right = True
        
        if action == Action.ATTACK:
            self.attack_cooldown = 30  # Example cooldown
    
    def reset_accumulated_reward(self):
        """Reset accumulated reward and components"""
        self.accumulated_reward = 0.0
        self.reward_components.clear()
    
    def add_reward(self, reward: float, component: str = 'general'):
        """Add reward to accumulated total with component tracking"""
        self.accumulated_reward += reward
        if component in self.reward_components:
            self.reward_components[component] += reward
        else:
            self.reward_components[component] = reward
    