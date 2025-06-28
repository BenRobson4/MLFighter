from dataclasses import dataclass
from typing import Dict, Optional
from ..core.frame_data import FighterFrameData

@dataclass
class Fighter:
    """Represents the structure of the stats of a character"""
    name: str  
    gravity: float 
    jump_force: int 
    move_speed: int 
    x_attack_range: int 
    y_attack_range: int 
    attack_damage: int  
    attack_cooldown: int  # Keep for backward compatibility
    health: int 
    weapon: str 
    frame_data: Optional[FighterFrameData] = None  # New field
    
    def __post_init__(self):
        """Initialize frame data if not provided"""
        if self.frame_data is None:
            self.frame_data = FighterFrameData.get_default()
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'gravity': self.gravity,
            'jump_force': self.jump_force,
            'move_speed': self.move_speed,
            'x_attack_range': self.x_attack_range,
            'y_attack_range': self.y_attack_range,
            'attack_damage': self.attack_damage,
            'attack_cooldown': self.attack_cooldown,
            'health': self.health,
            'weapon': self.weapon
        }