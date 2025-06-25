from dataclasses import dataclass
from typing import Dict

@dataclass
class Weapon:
    """Represents the structure of the stats of a character"""
    
    name: str # The name of the weapon, e.g., 'Default', 'Sword', 'Dagger', etc.
    gravity_modifier: float # How the weapon affects the character's gravity
    jump_force_modifier: int # How the weapon affects the character's jump force
    move_speed_modifier: int # How the weapon affects the character's move speed
    x_attack_range_modifier: int # How many pixels the weapon hits in front of them
    y_attack_range_modifier: int # How many pixels the weapon hits above them
    attack_damage_modifier: int  # How much damage the weapon does on a landed hit
    attack_cooldown_modifier: int # How long the character has to wait between attacks with this weapon
    hit_stun_frames_modifier: int = 0 # How many more/fewer frames the opponent is stunned for when hit by this weapon
    block_stun_frames_modifier: int = 0 # How many more/fewer frames the opponent is stunned for when blocking with this weapon
    rarity: str = 'common' # The rarity of the weapon, e.g., common, rare, epic, legendary
    
    def to_dict(self) -> Dict:
        return {
            'gravity_modifier': self.gravity_modifier,
            'jump_force_modifier': self.jump_force_modifier,
            'move_speed_modifier': self.move_speed_modifier,
            'x_attack_range_modifier': self.x_attack_range_modifier,
            'y_attack_range_modifier': self.y_attack_range_modifier,
            'attack_damage_modifier': self.attack_damage_modifier,
            'attack_cooldown_modifier': self.attack_cooldown_modifier,
            'rarity': self.rarity
        }
