from .weapon_config import Weapon

class WeaponManager:
    """Class to hold fighter information"""
    def weapon_list(self):
        return ['Default', 'Sword', 'Dagger', 'Lance', 'Bow']
    
    def retrieve_weapon_stats(self, weapon: str) -> Weapon:

        match weapon:
            case 'Default':
                return Weapon(name='Default',
                              gravity_modifier=1, 
                              jump_force_modifier=1, 
                              move_speed_modifier=1, 
                              x_attack_range_modifier=0,
                              y_attack_range_modifier=0,
                              attack_damage_modifier=0, 
                              attack_cooldown_modifier=0, 
                              rarity='common'
                              )
            
            case 'Sword':
                return Weapon(name='Sword',
                              gravity_modifier=1.1, 
                              jump_force_modifier=0.9, 
                              move_speed_modifier=1, 
                              x_attack_range_modifier=40,
                              y_attack_range_modifier=20,
                              attack_damage_modifier=5, 
                              attack_cooldown_modifier=10, 
                              rarity='common'
                              )
            
            case 'Dagger':
                return Weapon(name='Dagger',
                              gravity_modifier=1.2, 
                              jump_force_modifier=1.2, 
                              move_speed_modifier=1.4, 
                              x_attack_range_modifier=-20,
                              y_attack_range_modifier=-400,
                              attack_damage_modifier=10, 
                              attack_cooldown_modifier=-10, 
                              rarity='common'
                              )
            
            case 'Lance':
                return Weapon(name='Lance',
                              gravity_modifier=0.8, 
                              jump_force_modifier=1, 
                              move_speed_modifier=0.9, 
                              x_attack_range_modifier=80,
                              y_attack_range_modifier=-20,
                              attack_damage_modifier=20, 
                              attack_cooldown_modifier=30, 
                              rarity='common'
                            )
            
            case 'Bow':
                return Weapon(name='Bow',
                              gravity_modifier=0.7, 
                              jump_force_modifier=1.1, 
                              move_speed_modifier=1, 
                              x_attack_range_modifier=300,
                              y_attack_range_modifier=-40,
                              attack_damage_modifier=0, 
                              attack_cooldown_modifier=40, 
                              rarity='rare'
                              )
            case _:
                return Weapon(name='Default',
                              gravity_modifier=1, 
                              jump_force_modifier=1, 
                              move_speed_modifier=1, 
                              x_attack_range_modifier=80,
                              y_attack_range_modifier=80,
                              attack_damage_modifier=10, 
                              attack_cooldown_modifier=30, 
                              rarity='common'
                              )