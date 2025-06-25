from dataclasses import dataclass
from typing import Dict, Optional
from .weapon import Weapon
from .armour import Armour
from .fighter_frame_data import FighterFrameData
from .action_frame_data import ActionFrameData
from ..globals import Action


@dataclass
class Fighter:
    """Represents the structure of a character with stats and frame data"""
    name: str
    width: int
    height: int
    gravity: float
    friction: float
    jump_force: int
    jump_cooldown: int
    move_speed: int
    x_attack_range: int
    y_attack_range: int
    attack_damage: int
    attack_cooldown: int
    on_hit_stun: int
    block_efficiency: float
    block_cooldown: int
    on_block_stun: int
    health: int 
    damage_reduction: float = 0.0
    weapon: Optional[Weapon] = None
    armour: Optional[Armour] = None
    frame_data: Optional[FighterFrameData] = None
    
    def get_action_data(self, action: Action) -> ActionFrameData:
        """Get frame data for a specific action"""
        return self.frame_data.get_action_data(action)
    
    def get_total_frames(self, action: Action) -> int:
        """Get total frames for an action"""
        return self.get_action_data(action).total_frames