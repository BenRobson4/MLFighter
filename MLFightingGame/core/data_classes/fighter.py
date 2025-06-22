from dataclasses import dataclass
from typing import Dict, Optional, ClassVar
from .fighter_frame_data import FighterFrameData
from .action_frame_data import ActionFrameData
from ..globals import Action


@dataclass
class Fighter:
    """Represents the structure of a character with stats and frame data"""
    name: str
    gravity: float
    jump_force: int
    move_speed: int
    x_attack_range: int
    y_attack_range: int
    attack_damage: int
    attack_cooldown: int
    health: int 
    weapon: str 
    frame_data: Optional[FighterFrameData] = None
    
    # Class variables for fighter metadata
    description: ClassVar[str] = "Base fighter"
    difficulty: ClassVar[int] = 1  # 1-5 scale
    style: ClassVar[str] = "balanced"
    
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
            'weapon': self.weapon,
            'description': self.description,
            'difficulty': self.difficulty,
            'style': self.style
        }
    
    def get_action_data(self, action: Action) -> ActionFrameData:
        """Get frame data for a specific action"""
        return self.frame_data.get_action_data(action)
    
    def get_total_frames(self, action: Action) -> int:
        """Get total frames for an action"""
        return self.get_action_data(action).total_frames
    
    @classmethod
    def get_metadata(cls) -> Dict:
        """Get fighter metadata for UI/configuration"""
        return {
            'name': cls.__name__,
            'description': cls.description,
            'difficulty': cls.difficulty,
            'style': cls.style
        }