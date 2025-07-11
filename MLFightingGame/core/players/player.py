from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import numpy as np

from ..data_classes import Fighter, Weapon, Armour, LearningParameters, PlayerInventory
from .ml_agent import MLAgent
from .fighter_loader import FighterLoader
from .player_state_builder import PlayerStateBuilder
from .player_state_machine import StateMachine
from ..globals import Action, State
from ..globals.constants import ARENA_WIDTH, SPAWN_MARGIN, GROUND_LEVEL

logger = logging.getLogger(__name__)

class Player(MLAgent):
    """Player class managing fighter stats, items, and ML agent"""
    def __init__(self, 
                 player_id: int, # 1 or 2
                 fighter_name: str = None,
                 starting_gold: int = 1000,
                 starting_level: int = 1,
                 learning_parameters: Optional[LearningParameters] = None,
                 initial_feature_mask: Optional[np.ndarray] = None,
                 items: Optional[PlayerInventory] = None,
                 num_actions: int = 6,
                 num_features: int = 20):
        # Player identification
        self.player_id = player_id
        
        # Load fighter from configuration
        FighterLoader.set_config_path('/Users/benrobson/Documents/Coding/Random Programs/MLFightingGame/MLFightingGame/core/players/fighters.json')
        if fighter_name is None:
            fighter_name = "aggressive"  # Default fighter if none specified

        fighter = FighterLoader.load_fighter(fighter_name)
        
        # Fighter and stats
        self.base_fighter = fighter
        self.fighter = self._create_modified_fighter(fighter, items)
        
        # Resources
        self.gold = starting_gold
        self.level = starting_level
        self.experience = 0
        
        # Items and inventory
        self.inventory = items or PlayerInventory()
        
        # Learning parameters
        self.learning_parameters = learning_parameters or LearningParameters()
        self.base_learning_parameters = self.learning_parameters.copy()  # Store base parameters
        
        self.initial_feature_mask = initial_feature_mask

        # Initialize ML Agent with feature mask
        super().__init__(
            num_features=num_features,
            num_actions=num_actions,
            epsilon=self.learning_parameters.epsilon,
            epsilon_decay=self.learning_parameters.epsilon_decay,
            epsilon_min=self.learning_parameters.epsilon_min,
            learning_rate=self.learning_parameters.learning_rate,
            initial_feature_mask=self.initial_feature_mask  # Pass to parent
        )
        
        self._apply_learning_modifiers()

        # Player state (managed by GameEngine)
        self.state = PlayerStateBuilder.build(
            player=self,
            player_id=self.player_id,
            spawn_x=None,
            spawn_y=None
        )

        self.state_machine = StateMachine(self.state)
        
        # Training metrics
        self.total_reward = 0
        self.wins = 0
        self.losses = 0
        self.total_fights = 0
        self.batch_history = []
        self.actions_taken = 0
        
        logger.info(f"Player {player_id} initialized with fighter {fighter.name}")
    
    def set_player_id(self, player_id: int):
        """Update player ID and reset position based on new ID"""
        self.player_id = player_id
        self.state.player_id = player_id
        
        # Update spawn position based on new ID
        self.state.start_y = GROUND_LEVEL
        if player_id == 1:
            self.state.start_x = SPAWN_MARGIN  # Player 1 spawn
            self.state.x = self.state.start_x
        else:
            self.state.start_x = ARENA_WIDTH - SPAWN_MARGIN  # Player 2 spawn
            self.state.x = self.state.start_x
        
    def _create_modified_fighter(self, base_fighter: Fighter, items: Optional[PlayerInventory]) -> Fighter:
        """Create a fighter with stats modified by equipped items"""
        if not items:
            return base_fighter
            
        # Start with base stats
        modified_fighter = Fighter(
            name=base_fighter.name,

            width=base_fighter.width,
            height=base_fighter.height,

            gravity=base_fighter.gravity,
            friction=base_fighter.friction,
            jump_force=base_fighter.jump_force,
            jump_cooldown=base_fighter.jump_cooldown,
            move_speed=base_fighter.move_speed,

            x_attack_range=base_fighter.x_attack_range,
            y_attack_range=base_fighter.y_attack_range,
            attack_damage=base_fighter.attack_damage,
            attack_cooldown=base_fighter.attack_cooldown,
            on_hit_stun=base_fighter.on_hit_stun,

            block_efficiency=base_fighter.block_efficiency,
            block_cooldown=base_fighter.block_cooldown,
            on_block_stun=base_fighter.on_block_stun,

            health=base_fighter.health,
            damage_reduction=base_fighter.damage_reduction,

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
            modified_fighter.on_hit_stun += weapon.hit_stun_frames_modifier
            modified_fighter.on_block_stun += weapon.block_stun_frames_modifier
            modified_fighter.weapon = weapon.name
            
        # Apply armour modifiers
        armour = items.get_equipped_armour()
        if armour:
            modified_fighter.gravity *= armour.gravity_modifier
            modified_fighter.jump_force += armour.jump_force_modifier
            modified_fighter.move_speed += armour.move_speed_modifier
            modified_fighter.health += armour.health_modifier
            modified_fighter.damage_reduction += armour.damage_reduction_modifier
            
        return modified_fighter
        
    def _apply_learning_modifiers(self):
        """Apply all learning modifiers to parameters"""
        # Reset to base values before applying modifiers
        self.learning_parameters = self.base_learning_parameters.copy()
        
        # Apply all modifiers
        for category, modifiers in self.inventory.learning_modifiers.items():
            for modifier in modifiers:
                delta = modifier.get("delta", 0)
                self.learning_parameters.apply_modifier(category, delta)
                
        # Update ML agent parameters
        super().update_parameters(
            epsilon=self.learning_parameters.epsilon,
            epsilon_decay=self.learning_parameters.epsilon_decay,
            learning_rate=self.learning_parameters.learning_rate
        )

    def _update_feature_mask(self):
        """Update feature map in the ML agent"""
        if self.initial_feature_mask is not None:
            self.feature_mask = self.initial_feature_mask.copy()
        else:
            # Default to all features enabled
            self.feature_mask = np.ones(self.num_features, dtype=bool)
        
        # Apply any feature modifiers from inventory
        for feature in self.inventory.features:
            if feature in self.feature_mask:
                self.feature_mask[feature] = True
        
        super().update_parameters(feature_mask=self.feature_mask)

    def get_hitbox(self) -> Tuple[float, float, float, float]:
        """Get current hitbox as (x1, y1, x2, y2)"""
        return (
            self.state.x - self.state.width / 2,
            self.state.y - self.state.height / 2,
            self.state.x + self.state.width / 2,
            self.state.y + self.state.height / 2
        )
    
    def get_attack_hitbox(self) -> Optional[Tuple[float, float, float, float]]:
        """Get attack hitbox if currently attacking"""
        if not self.state.current_state == State.ATTACK_ACTIVE:
            return None
        
        # Determine attack direction based on facing
        direction = 1 if self.state.facing_right else -1
        attack_x_offset = self.state.width / 2 * direction
        
        # Calculate start and end points
        attack_start_x = self.state.x + attack_x_offset
        attack_end_x = attack_start_x + (self.state.x_attack_range * direction)
        
        # Ensure x1 < x2 by using min/max
        x1 = min(attack_start_x, attack_end_x)
        x2 = max(attack_start_x, attack_end_x)
        
        return (
            x1,
            self.state.y - self.state.y_attack_range / 2,
            x2,
            self.state.y + self.state.y_attack_range / 2
        )

    def can_take_action(self) -> bool:
        """Check if player can take a new action"""
        actionable_states = self.state_machine.actionable_states
        return self.state.current_state in actionable_states

    def is_action_off_cooldown(self, action: Action) -> bool:
        """Check if a specific action is off cooldown"""
        if action == Action.ATTACK and self.state.attack_cooldown_remaining > 0:
            return False
        
        if action == Action.BLOCK and self.state.block_cooldown_remaining > 0:
            return False
        
        if action == Action.JUMP and self.state.y < 0:
            return False
        
        if action == Action.JUMP and self.state.jump_cooldown_remaining > 0:
            return False
        
        return True
        
    def add_item(self, item_id: str, item_data: Dict):
        """Add an item to the player's inventory from shop purchase"""
        category = item_data.get("category")
        
        logger.info(f"Player {self.player_id} adding item {item_id} of category {category}")
        
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
                hit_stun_frames_modifier=item_data.get("hit_stun_frames_modifier", 0),
                block_stun_frames_modifier=item_data.get("block_stun_frames_modifier", 0),
                rarity=item_data.get("rarity", "common")
            )
            self.inventory.add_weapon(weapon)
            self._update_fighter_stats()
            logger.info(f"Added weapon {weapon.name}, now have {len(self.inventory.weapons)} weapons")
            
        elif category == "armour":
            armour = Armour(
                name=item_data.get("name"),
                description=item_data.get("description", ""),
                gravity_modifier=item_data.get("gravity_modifier", 1.0),
                jump_force_modifier=item_data.get("jump_force_modifier", 0),
                move_speed_modifier=item_data.get("move_speed_modifier", 0),
                health_modifier=item_data.get("health_modifier", 0),
                damage_reduction_modifier=item_data.get("damage_reduction_modifier", 0),
                rarity=item_data.get("rarity", "common")
            )
            self.inventory.add_armour(armour)
            self._update_fighter_stats()
            logger.info(f"Added armour {armour.name}, now have {len(self.inventory.armour)} armour pieces")
            
        elif category == "reward_modifiers":
            subcategory = item_data.get("subcategory")
            self.inventory.add_reward_modifier(subcategory, item_data)
            logger.info(f"Added reward modifier for {subcategory}")
            
        elif category == "learning_modifiers":
            subcategory = item_data.get("subcategory")
            self.inventory.add_learning_modifier(subcategory, item_data)
            self._apply_learning_modifiers()
            logger.info(f"Added learning modifier for {subcategory}")
            
        elif category == "features":
            # Extract feature index from item data
            feature_properties = item_data.get("properties", {})
            feature_index = feature_properties.get("feature_index")
            feature_name = item_data.get("name", f"feature_{feature_index}")
            
            if feature_index is not None and feature_index < self.num_features:
                # Update feature mask to enable this feature
                current_mask = self.feature_mask.cpu().numpy()
                current_mask[feature_index] = 1
                
                # Update ML agent's feature mask
                super().update_parameters(feature_mask=current_mask)
                
                # Add to inventory for tracking
                self.inventory.add_feature(feature_name)
                
                logger.info(f"Player {self.player_id} unlocked feature {feature_index}: {feature_name}")
            else:
                logger.warning(f"Invalid feature index {feature_index} in item {item_id}")
        else:
            logger.warning(f"Unknown item category: {category}")
        
        logger.info(f"Player {self.player_id} inventory updated with item: {item_id}")

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

        ## return Action.JUMP  # Test that the game works without the ML logic

        # Get action from ML agent
        action = super().get_action(
            state_vector, 
            available_actions, 
            epsilon=self.learning_parameters.epsilon
        )

        action = Action(action)  # Ensure action is an Action enum
        
        # Decay epsilon after each action
        self.learning_parameters.epsilon = max(
            self.learning_parameters.epsilon_min,
            self.learning_parameters.epsilon * self.learning_parameters.epsilon_decay
        )
        
        # Update ML agent's epsilon
        super().update_parameters(epsilon=self.learning_parameters.epsilon)
        
        # Track actions taken
        self.actions_taken += 1
        
        return action

    def request_action(self, action: Action):
        if self.state_machine.can_transition(self.state.current_state, action):
            new_state = self.state_machine.get_next_state(self.state, self.state.current_state, action)
            self._enter_state(new_state)
    
    def update_state(self):
        # Check for automatic transitions
        should_transition, event = self.state_machine.should_auto_transition(self.state)
        if should_transition:
            new_state = self.state_machine.get_next_state(self.state, self.state.current_state, event)
            self._enter_state(new_state)
    
    def _enter_state(self, new_state: State):
        """Apply state effects when entering a new state"""
        previous_state = self.state.current_state
        
        # Update state
        self.state.current_state = new_state
        self.state.state_frame_counter = 0
        
        # Apply state effects
        effects = self.state_machine.get_state_effects(new_state)
        for effect, value in effects.items():
            if value == 'negative_move_speed':
                self.state.velocity_x = -self.state.move_speed
            elif value == 'positive_move_speed':
                self.state.velocity_x = self.state.move_speed
            elif value == 'negative_jump_force':
                self.state.velocity_y = -self.state.jump_force
            else:
                setattr(self.state, effect, value)

        # Handle cooldowns when actions complete
        if previous_state in [State.ATTACK_RECOVERY, State.BLOCK_RECOVERY, State.JUMP_RECOVERY]:
            if new_state == State.IDLE:
                if previous_state == State.ATTACK_RECOVERY:
                    self.state.attack_cooldown_remaining = self.state.attack_cooldown
                elif previous_state == State.BLOCK_RECOVERY:
                    self.state.block_cooldown_remaining = self.state.block_cooldown
                elif previous_state == State.JUMP_RECOVERY:
                    self.state.jump_cooldown_remaining = self.state.jump_cooldown
            
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
        
    def end_batch(self, wins: int, losses: int):
        """
        Update player statistics after a batch of fights completes.
        
        Args:
            wins: Number of wins in this batch
            losses: Number of losses in this batch
        """
        # Update win/loss record
        self.wins += wins
        self.losses += losses
        
        # Update total fights
        self.total_fights = self.wins + self.losses
        
        # Log the batch results
        logger.info(f"Player {self.fighter.name} batch complete: "
                    f"{wins} wins, {losses} losses "
                    f"(Total: {self.wins}W-{self.losses}L)")
        
        # Optional: You could add batch-level learning updates here
        # For example, adjusting exploration rate based on performance
        # or saving model checkpoints after batches
        
        # Optional: Track performance metrics
        if hasattr(self, 'batch_history'):
            self.batch_history.append({
                'wins': wins,
                'losses': losses,
                'win_rate': wins / (wins + losses) if (wins + losses) > 0 else 0
            })

            
    def get_stats(self) -> Dict:
        """Get player statistics"""
        return {
            "player_id": self.player_id,
            "level": self.level,
            "gold": self.gold,
            "experience": self.experience,
            "total_fights": self.total_fights,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": self.wins / max(1, self.total_fights),
            "average_reward": self.total_reward / max(1, self.total_fights),
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
                "total_fights": self.total_fights,
                "wins": self.wins,
                "losses": self.losses,
                "total_reward": self.total_reward,
                "actions_taken": self.actions_taken,
                "batch_history": self.batch_history
            },
            "base_fighter": self.state.fighter_name,
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
        player.total_fights = data["stats"]["total_fights"]
        player.batch_history = data["stats"]["batch_history"]
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