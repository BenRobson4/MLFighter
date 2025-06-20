from .fighter_config import Fighter
from .weapon_manager import WeaponManager
from .weapon_config import Weapon

class FighterManager:
    """Class to hold fighter information"""
    def fighter_list(self):
        return ['Default', 'Ben', 'Speedy', 'Tanky']
    
    def retrieve_fighter_base_stats(self, fighter: str) -> Fighter:

        match fighter:
            case 'Default':
                return Fighter(name='Default',
                               gravity=0.8, 
                               jump_force=-15, 
                               move_speed=5, 
                               x_attack_range=80, 
                               y_attack_range=60,
                               attack_damage=10, 
                               attack_cooldown=30, 
                               health=100, 
                               weapon='Default'
                               )
            
            case 'Ben':
                return Fighter(name='Ben',
                               gravity=1.2, 
                               jump_force=-20, 
                               move_speed=10, 
                               x_attack_range=120,
                               y_attack_range=80,
                               attack_damage=20, 
                               attack_cooldown=15, 
                               health=200, 
                               weapon='Default'
                               )

            case 'Speedy':
                return Fighter(name='Speedy',
                               gravity=1.4, 
                               jump_force=-25, 
                               move_speed=15, 
                               x_attack_range=50,
                               y_attack_range=40,
                               attack_damage=15, 
                               attack_cooldown=10, 
                               health=60, 
                               weapon='Default'
                               )
            
            case 'Tanky':
                return Fighter(name='Tanky',
                               gravity=1.2, 
                               jump_force=-10, 
                               move_speed=4, 
                               x_attack_range=80,
                               y_attack_range=60,
                               attack_damage=10, 
                               attack_cooldown=50, 
                               health=180, 
                               weapon='Bow'
                               )
            
            case _:
                return Fighter(name='Default',
                               gravity=0.8, 
                               jump_force=-15,
                               move_speed=5, 
                               x_attack_range=80, 
                               y_attack_range=60,
                               attack_damage=10, 
                               attack_cooldown=30, 
                               health=100, 
                               weapon='Default'
                               )

    def current_stats(self, fighter: str) -> Fighter:
        """Retrieve the current stats of a fighter"""

        weapon_manager = WeaponManager()
        base_stats = self.retrieve_fighter_base_stats(fighter)
        
        # Logic to modify stats based on weapon (other factors to be added later)
        if base_stats.weapon != 'Default':
            weapon_stats = weapon_manager.retrieve_weapon_stats(base_stats.weapon).to_dict()
            return Fighter(
                name=base_stats.name,
                gravity=base_stats.gravity * weapon_stats['gravity_modifier'],
                jump_force=int(base_stats.jump_force * weapon_stats['jump_force_modifier']),
                move_speed=int(base_stats.move_speed * weapon_stats['move_speed_modifier']),
                x_attack_range=int(base_stats.x_attack_range + weapon_stats['x_attack_range_modifier']),
                y_attack_range=int(base_stats.y_attack_range + weapon_stats['y_attack_range_modifier']),
                attack_damage=int(base_stats.attack_damage + weapon_stats['attack_damage_modifier']),
                attack_cooldown=int(base_stats.attack_cooldown + weapon_stats['attack_cooldown_modifier']),
                health=base_stats.health,
                weapon=base_stats.weapon
            )
        else:
            return base_stats