from .base_stats_config import BaseStats

class FighterManager:
    """Class to hold fighter information"""
    def fighter_list(self):
        return ['Default', 'Ben', 'Speedy', 'Tanky']
    
    def retrieve_fighter_stats(self, fighter: str) -> BaseStats:

        match fighter:
            case 'Default':
                return BaseStats(gravity=0.8, jump_force=-15, move_speed=5, attack_range=80, attack_damage=10, attack_cooldown=30, health=100)
            
            case 'Ben':
                return BaseStats(gravity=1.2, jump_force=-25, move_speed=10, attack_range=120, attack_damage=20, attack_cooldown=10, health=200)

            case 'Speedy':
                return BaseStats(gravity=1.4, jump_force=-35, move_speed=15, attack_range=50, attack_damage=15, attack_cooldown=15, health=60)
            
            case 'Tanky':
                return BaseStats(gravity=1.2, jump_force=-10, move_speed=6, attack_range=80, attack_damage=20, attack_cooldown=40, health=180)
            
            case _:
                return BaseStats(gravity=0.8, jump_force=-15, move_speed=5, attack_range=80, attack_damage=10, attack_cooldown=30, health=100)

if __name__ == "__main__":
    fighter_manager = FighterManager()
    print(fighter_manager.retrieve_fighter_stats('Ben'))