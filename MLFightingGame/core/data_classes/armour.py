from dataclasses import dataclass
from typing import Dict

@dataclass
class Armour:
    """Represents an armour item and its modifications when equipped"""
    
    name: str # The name of the item, e.g., 'Chainmail', 'Leather', 'Cloth', etc.
    description: str # Description of the armour item
    gravity_modifier: float # How the item affects the character's gravity
    jump_force_modifier: int # How the item affects the character's jump force
    move_speed_modifier: int # How the item affects the character's move speed
    health_modifier: int # How the item affects the character's health
    damage_reduction_modifier: int  # How the damage that landed attack deal is modified
    rarity: str = 'common' # The rarity of the weapon, e.g., common, rare, epic, legendary
    
    def to_dict(self) -> Dict:
        return {
            'gravity_modifier': self.gravity_modifier,
            'jump_force_modifier': self.jump_force_modifier,
            'move_speed_modifier': self.move_speed_modifier,
            'health_modifier': self.health_modifier,
            'damage_reduction_modifier': self.damage_reduction_modifier,
            'rarity': self.rarity
        }
