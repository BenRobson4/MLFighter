from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import numpy as np

from ..data_classes import Fighter, Weapon, Armour, PlayerState, LearningParameters, PlayerInventory
from .ml_agent import MLAgent
from ..globals import Action

logger = logging.getLogger(__name__)

class Player(MLAgent):
    """Player class managing fighter stats, items, and ML agent"""
    
    def __init__(self, 
                 player_id: str,
                 fighter: Fighter,
                 starting_gold: int = 1000,
                 starting_level: int = 1,
                 learning_parameters: Optional[LearningParameters] = None,
                 items: Optional[PlayerInventory] = None,
                 num_actions: int = 6,
                 num_features: int = 20):  # Based on your GameState.get_state_vector
        
        # Player identification
        self.player_id = player_id
        
        # Fighter and stats
        self.base_fighter = fighter  # Original fighter stats
        self.fighter = self._create_modified_fighter(fighter, items)  # Modified by items
        
        # Resources
        self.gold = starting_gold
        self.level = starting_level
        self.experience = 0
        
        # Items and inventory
        self.inventory = items or PlayerInventory()
        
        # Learning parameters
        self.learning_parameters = learning_parameters or LearningParameters()
        self._apply_learning_modifiers()
        
        # Initialize ML Agent
        super().__init__(
            num_features=num_features,
            num_actions=num_actions,
            epsilon=self.learning_parameters.epsilon,
            epsilon_decay=self.learning_parameters.epsilon_decay,
            epsilon_min=self.learning_parameters.epsilon_min,
            learning_rate=self.learning_parameters.learning_rate
        )
        
        # Player state (managed by GameEngine)
        self.state = PlayerState()
        
        # Training metrics
        self.total_reward = 0
        self.wins = 0
        self.losses = 0
        self.matches_played = 0
        self.actions_taken = 0
        
        logger.info(f"Player {player_id} initialized with fighter {fighter.name}")
        
    def _create_modified_fighter(self, base_fighter: Fighter, items: Optional[PlayerInventory]) -> Fighter:
        """Create a fighter with stats modified by equipped items"""
        if not items:
            return base_fighter
            
        # Start with base stats
        modified_fighter = Fighter(
            name=base_fighter.name,
            gravity=base_fighter.gravity,
            jump_force=base_fighter.jump_force,
            move_speed=base_fighter.move_speed,
            x_attack_range=base_fighter.x_attack_range,
            y_attack_range=base_fighter.y_attack_range,
            attack_damage=base_fighter.attack_damage,
            attack_cooldown=base_fighter.attack_cooldown,
            health=base_fighter.health,
            weapon=base_fighter.weapon,
            frame_data=base_fighter.frame_data
        )
        
        # Apply weapon modifiers
        weapon = items.get_equipped_weapon()
        if weapon:
            modified_fighter.gravity *= weapon.gravity_modifier
            modified_fighter.jump_force += weapon.jump_force_modifier
            modified_fighter.move_speed += weapon.move_speed_modifier
            modified_fighter.x_attack_range += weapon.x_attack_range_modifier
            modified_fighter.y_attack_range += weapon.y_attack_range_modifier
            modified_fighter.attack_damage += weapon.attack_damage_modifier
            modified_fighter.attack_cooldown += weapon.attack_cooldown_modifier
            modified_fighter.weapon = weapon.name
            
        # Apply armour modifiers
        armour = items.get_equipped_armour()
        if armour:
            modified_fighter.gravity *= armour.gravity_modifier
            modified_fighter.jump_force += armour.jump_force_modifier
            modified_fighter.move_speed += armour.move_speed_modifier
            modified_fighter.health += armour.health_modifier
            
        return modified_fighter
        
    def _apply_learning_modifiers(self):
        """Apply all learning modifiers to parameters"""
        # Reset to base values before applying modifiers
        base_params = LearningParameters()
        
        # Apply all modifiers
        for category, modifiers in self.inventory.learning_modifiers.items():
            for modifier in modifiers:
                delta = modifier.get("delta", 0)
                self.learning_parameters.apply_modifier(category, delta)
                
        # Update ML agent parameters
        self.update_parameters(
            epsilon=self.learning_parameters.epsilon,
            epsilon_decay=self.learning_parameters.epsilon_decay,
            learning_rate=self.learning_parameters.learning_rate
        )
        
    def add_item(self, item_id: str, item_data: Dict):
        """Add an item to the player's inventory from shop purchase"""
        category = item_data.get("category")
        
        if category == "weapons":
            weapon = Weapon(
                name=item_data.get("name"),
                gravity_modifier=item_data.get("gravity_modifier", 1.0),
                jump_force_modifier=item_data.get("jump_force_modifier", 0),
                move_speed_modifier=item_data.get("move_speed_modifier", 0),
                x_attack_range_modifier=item_data.get("x_attack_range_modifier", 0),
                y_attack_range_modifier=item_data.get("y_attack_range_modifier", 0),
                attack_damage_modifier=item_data.get("attack_damage_modifier", 0),
                attack_cooldown_modifier=item_data.get("attack_cooldown_modifier", 0),
                rarity=item_data.get("rarity", "common")
            )
            self.inventory.add_weapon(weapon)
            self._update_fighter_stats()
            
        elif category == "armour":
            armour = Armour(
                name=item_data.get("name"),
                description=item_data.get("description", ""),
                gravity_modifier=item_data.get("gravity_modifier", 1.0),
                jump_force_modifier=item_data.get("jump_force_modifier", 0),
                move_speed_modifier=item_data.get("move_speed_modifier", 0),
                health_modifier=item_data.get("health_modifier", 0),
                damage_received_modifier=item_data.get("damage_received_modifier", 0),
                rarity=item_data.get("rarity", "common")
            )
            self.inventory.add_armour(armour)
            self._update_fighter_stats()
            
        elif category == "reward_modifiers":
            subcategory = item_data.get("subcategory")
            self.inventory.add_reward_modifier(subcategory, item_data)
            
        elif category == "learning_modifiers":
            subcategory = item_data.get("subcategory")
            self.inventory.add_learning_modifier(subcategory, item_data)
            self._apply_learning_modifiers()
            
        elif category == "features":
            # Extract feature name from item data
            feature_name = item_data.get("properties", {}).get("category", "unknown")
            self.inventory.add_feature(feature_name)
            
        logger.info(f"Player {self.player_id} added item: {item_id}")
        
    def _update_fighter_stats(self):
        """Recalculate fighter stats based on current items"""
        self.fighter = self._create_modified_fighter(self.base_fighter, self.inventory)
        
    def get_action(self, state_vector: np.ndarray, available_actions: Optional[List[int]] = None) -> int:
        """
        Get next action from ML agent and decay epsilon
        
        Args:
            state_vector: State vector from GameState.get_state_vector()
            available_actions: List of valid action indices
            
        Returns:
            Selected action index
        """
        # Get action from ML agent
        action = super().get_action(
            state_vector, 
            available_actions, 
            epsilon=self.learning_parameters.epsilon
        )
        
        # Decay epsilon after each action
        self.learning_parameters.epsilon = max(
            self.learning_parameters.epsilon_min,
            self.learning_parameters.epsilon * self.learning_parameters.epsilon_decay
        )
        
        # Update ML agent's epsilon
        self.update_parameters(epsilon=self.learning_parameters.epsilon)
        
        # Track actions taken
        self.actions_taken += 1
        
        return action
    
    def update(self, 
               state: np.ndarray, 
               action: int, 
               reward: float,
               next_state: np.ndarray, 
               done: bool) -> None:
        """Update the ML agent with current player"""
        super().update(state, action, reward, next_state, done)

    def get_reward_weights(self) -> Dict[str, float]:
        """
        Get reward weights for each reward event type
        
        Returns:
            Dictionary mapping reward event names to their weights
        """
        # Default weights (1.0 = no modification)
        weights = {}
        
        # Apply modifiers from items
        for category, modifiers in self.inventory.reward_modifiers.items():
            if category in weights:
                for modifier in modifiers:
                    delta = modifier.get("delta", 0)
                    # Add modifier delta to existing weight
                    weights[category] = delta
                    
        return weights
        
    def spend_gold(self, amount: int) -> bool:
        """Spend gold if available"""
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False
        
    def add_gold(self, amount: int):
        """Add gold to player"""
        self.gold += amount
        
    def add_experience(self, amount: int):
        """Add experience to player"""
        self.experience += amount
        
    def end_match(self, won: bool, total_reward: float):
        """Record match results"""
        self.matches_played += 1
        self.total_reward += total_reward
        
        if won:
            self.wins += 1
        else:
            self.losses += 1
            
    def get_stats(self) -> Dict:
        """Get player statistics"""
        return {
            "player_id": self.player_id,
            "level": self.level,
            "gold": self.gold,
            "experience": self.experience,
            "matches_played": self.matches_played,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": self.wins / max(1, self.matches_played),
            "average_reward": self.total_reward / max(1, self.matches_played),
            "fighter_name": self.fighter.name,
            "items_owned": len(self.inventory.weapons) + len(self.inventory.armour),
            "learning_params": self.learning_parameters.to_dict(),
            "actions_taken": self.actions_taken,
            "current_epsilon": self.learning_parameters.epsilon
        }
        
    def save(self, filepath: str):
        """Save player data to file"""
        save_data = {
            "player_id": self.player_id,
            "gold": self.gold,
            "level": self.level,
            "experience": self.experience,
            "stats": {
                "matches_played": self.matches_played,
                "wins": self.wins,
                "losses": self.losses,
                "total_reward": self.total_reward,
                "actions_taken": self.actions_taken
            },
            "base_fighter": self.base_fighter.to_dict(),
            "inventory": self.inventory.to_dict(),
            "learning_parameters": self.learning_parameters.to_dict()
        }
        
        # Save player data
        player_file = Path(filepath)
        player_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(player_file, 'w') as f:
            json.dump(save_data, f, indent=2)
            
        # Save ML agent weights
        weights_file = player_file.with_suffix('.pth')
        self.save_weights(str(weights_file))
        
        logger.info(f"Player {self.player_id} saved to {filepath}")
        
    @classmethod
    def load(cls, filepath: str, fighter_class) -> 'Player':
        """Load player data from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Recreate fighter
        fighter = fighter_class(
            name=data["base_fighter"]["name"],
            gravity=data["base_fighter"]["gravity"],
            jump_force=data["base_fighter"]["jump_force"],
            move_speed=data["base_fighter"]["move_speed"],
            x_attack_range=data["base_fighter"]["x_attack_range"],
            y_attack_range=data["base_fighter"]["y_attack_range"],
            attack_damage=data["base_fighter"]["attack_damage"],
            attack_cooldown=data["base_fighter"]["attack_cooldown"],
            health=data["base_fighter"]["health"],
            weapon=data["base_fighter"]["weapon"]
        )
        
        # Recreate learning parameters
        learning_params = LearningParameters(**data["learning_parameters"])
        
        # Create player
        player = cls(
            player_id=data["player_id"],
            fighter=fighter,
            starting_gold=data["gold"],
            starting_level=data["level"],
            learning_parameters=learning_params
        )
        
        # Restore stats
        player.experience = data["experience"]
        player.matches_played = data["stats"]["matches_played"]
        player.wins = data["stats"]["wins"]
        player.losses = data["stats"]["losses"]
        player.total_reward = data["stats"]["total_reward"]
        player.actions_taken = data["stats"].get("actions_taken", 0)
        
        # TODO: Properly restore inventory items
        # This requires recreating Weapon/Armour objects from saved data
        
        # Load ML agent weights
        weights_file = Path(filepath).with_suffix('.pth')
        if weights_file.exists():
            player.load_weights(str(weights_file))
            
        logger.info(f"Player {data['player_id']} loaded from {filepath}")
        return player