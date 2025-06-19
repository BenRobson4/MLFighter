from dataclasses import dataclass
from typing import Dict

@dataclass
class BaseStats:
    """Represents the structure of the stats of a character"""
    {
            'gravity': 0.8,
            'jump_force': -15,
            'move_speed': 5,
            'attack_range': 80,
            'attack_damage': 10,
            'attack_cooldown': 30,
            'health': 100
        }
    
    gravity: float # How strong the gravity is on this character
    jump_force: int # How strong the character's jump is
    move_speed: int # How far the character moves in 1 frame
    attack_range: int # How many pixels the characters attack hits in front of them
    attack_damage: int  # How much damage the character does on a landed hit
    attack_cooldown: int # How long the character has to wait between attacks
    health: int # How much health the character has
    
    def to_dict(self) -> Dict:
        return {
            'gravity': self.gravity,
            'jump_force': self.jump_force,
            'move_speed': self.move_speed,
            'attack_range': self.attack_range,
            'attack_damage': self. attack_damage,
            'attack_cooldown': self.attack_cooldown,
            'health': self.health
        }
