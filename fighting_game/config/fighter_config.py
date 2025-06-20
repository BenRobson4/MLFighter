from dataclasses import dataclass
from typing import Dict

@dataclass
class Fighter:
    """Represents the structure of the stats of a character"""
    name: str  # The name of the fighter
    gravity: float # How strong the gravity is on this character
    jump_force: int # How strong the character's jump is
    move_speed: int # How far the character moves in 1 frame
    x_attack_range: int # How many pixels the characters attack hits in front of them
    y_attack_range: int # How many pixels the characters attack hits above/below them
    attack_damage: int  # How much damage the character does on a landed hit
    attack_cooldown: int # How long the character has to wait between attacks
    health: int # How much health the character has
    weapon: str # What weapon the character is using, e.g., 'Default', 'Sword', 'Dagger', etc.
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'gravity': self.gravity,
            'jump_force': self.jump_force,
            'move_speed': self.move_speed,
            'x_attack_range': self.x_attack_range,
            'y_attack_range': self.y_attack_range,
            'attack_damage': self. attack_damage,
            'attack_cooldown': self.attack_cooldown,
            'health': self.health,
            'weapon': self.weapon
        }
