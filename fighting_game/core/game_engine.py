from typing import Dict, Tuple, Optional, List
from .game_state import GameState
from .actions import Action
from .action_processor import ActionProcessor
from .reward_system import RewardEvent, RewardCalculator
from ..config.fighter_config import Fighter
from ..config.fighter_manager import FighterManager

class GameEngine:
    """Main game engine that handles physics and game logic"""
    
    def __init__(self, player1_fighter: str = 'Default', player2_fighter: str = 'Default'):
        self.fighter_manager = FighterManager()
        
        # Get fighter stats
        self.player1_stats = self.fighter_manager.current_stats(player1_fighter)
        self.player2_stats = self.fighter_manager.current_stats(player2_fighter)
        
        # Create game state with fighter stats
        self.state = GameState(player1_stats=self.player1_stats, player2_stats=self.player2_stats)
        
        # Store player physics configs for easy access
        self.player_physics = {
            'player1': self.player1_stats.to_dict(),
            'player2': self.player2_stats.to_dict()
        }
        
        # Create action processors
        self.action_processors = {
            'player1': ActionProcessor(self.player1_stats),
            'player2': ActionProcessor(self.player2_stats)
        }

        # Initialize reward calculator
        self.reward_calculator = RewardCalculator()
        
        # Store player reward weights (will be set by training system)
        self.player_reward_weights = {
            'player1': {},
            'player2': {}
        }
        
    def set_reward_weights(self, player_id: str, weights: Dict[str, float]):
        """Set reward weights for a specific player"""
        self.player_reward_weights[player_id] = weights
    
    def step(self, player1_action: Action, player2_action: Action) -> Tuple[GameState, Dict[str, float], List[RewardEvent]]:
        """Execute one game step and return new state + rewards + events"""
        if self.state.game_over:
            return self.state, {'player1': 0, 'player2': 0}, []
        
        # Store actions for reward calculation
        actions = {'player1': player1_action, 'player2': player2_action}
        
        # Process actions with frame data
        self._process_action_with_frames('player1', player1_action)
        self._process_action_with_frames('player2', player2_action)
        
        # Update physics
        self._update_physics()
        
        # Handle combat
        self._handle_combat()
        
        # Update frame counters
        self._update_action_frames()
        
        # Check win conditions
        self._check_game_over()
        
        # Calculate rewards using the new system
        rewards, events = self.reward_calculator.calculate_rewards(
            self.state, actions, self.player_reward_weights
        )
        
        self.state.frame_count += 1
        
        return self.state, rewards, events
    
    def _process_action_with_frames(self, player_id: str, action: Action):
        """Process player action with frame data consideration"""
        player = self.state.players[player_id]
        processor = self.action_processors[player_id]
        
        # Check if player can perform action
        if processor.can_perform_action(player, action):
            processor.start_action(player, action)
            self._apply_action(player_id, action)
        elif player['action_locked'] and action != player['current_action']:
            # Buffer the input
            processor.buffer_input(player, action)
    
    def _update_action_frames(self):
        """Update action frame counters"""
        for player_id, player in self.state.players.items():
            processor = self.action_processors[player_id]
            processor.update_action_frame(player)
            
            # Check for buffered input
            buffered_action = processor.complete_action(player) if not player['action_locked'] else None
            if buffered_action:
                self._process_action_with_frames(player_id, buffered_action)
    
    
    def _apply_action(self, player_id: str, action: Action):
        """Apply player action to game state"""
        player = self.state.players[player_id]
        physics = self.player_physics[player_id]
        
        # Reset action states
        player['is_blocking'] = False
        player['is_attacking'] = False
        
        if action == Action.LEFT:
            player['velocity_x'] = -physics['move_speed']
            player['facing_right'] = False
        elif action == Action.RIGHT:
            player['velocity_x'] = physics['move_speed']
            player['facing_right'] = True
        elif action == Action.JUMP and not player['is_jumping']:
            player['velocity_y'] = physics['jump_force']
            player['is_jumping'] = True
        elif action == Action.BLOCK:
            player['is_blocking'] = True
            player['velocity_x'] = 0
        elif action == Action.ATTACK and player['attack_cooldown'] <= 0:
            player['is_attacking'] = True
            player['attack_cooldown'] = physics['attack_cooldown']
        else:  # IDLE
            player['velocity_x'] = 0
    
    def _update_physics(self):
        """Update physics for all players"""
        for player_id, player in self.state.players.items():
            physics = self.player_physics[player_id]
            
            # Apply gravity
            if player['is_jumping']:
                player['velocity_y'] += physics['gravity']
            
            # Update positions
            player['x'] += player['velocity_x']
            player['y'] += player['velocity_y']
            
            # Boundary checking
            player['x'] = max(50, min(self.state.arena_width - 50, player['x']))
            
            # Ground collision
            if player['y'] >= self.state.ground_level:
                player['y'] = self.state.ground_level
                player['velocity_y'] = 0
                player['is_jumping'] = False
    
    def _handle_combat(self):
        """Handle combat interactions between players"""
        p1, p2 = self.state.players['player1'], self.state.players['player2']
        p1_physics, p2_physics = self.player_physics['player1'], self.player_physics['player2']
        p1_processor, p2_processor = self.action_processors['player1'], self.action_processors['player2']
        
        x_distance = p1['x'] - p2['x']
        y_distance = abs(p1['y'] - p2['y'])
        p2_facing_right = (p2['facing_right'] << 1) - 1  # Convert to -1 or 1  
        p1_facing_right = -p2_facing_right
        p1_x_displacement = x_distance * p1_facing_right
        p2_x_displacement = x_distance * p2_facing_right

        # Check if player 1 is in range to attack player 2
        p1_in_range = (p1_x_displacement <= p1_physics['x_attack_range'] and 
                    p1_x_displacement >= 0 and 
                    y_distance <= p1_physics['y_attack_range'])

        # Check if player 2 is in range to attack player 1
        p2_in_range = (p2_x_displacement <= p2_physics['x_attack_range'] and 
                    p2_x_displacement >= 0 and 
                    y_distance <= p2_physics['y_attack_range'])
        
        # Check if attacks can hit (in active frames AND haven't hit yet)
        p1_can_hit = p1_processor.can_hit_opponent(p1)
        p2_can_hit = p2_processor.can_hit_opponent(p2)
        
        # Player 1 attacking Player 2
        if (p1_can_hit and p1_in_range and not p2['is_blocking']):
            p2['health'] -= p1_physics['attack_damage']
            p1_processor.register_hit(p1)  # Mark that the hit has connected
            # Optional: Add hit stun or knockback here
        
        # Player 2 attacking Player 1
        if (p2_can_hit and p2_in_range and not p1['is_blocking']):
            p1['health'] -= p2_physics['attack_damage']
            p2_processor.register_hit(p2)  # Mark that the hit has connected
            # Optional: Add hit stun or knockback here
            
    def _update_cooldowns(self):
        """Update attack cooldowns"""
        for player in self.state.players.values():
            if player['attack_cooldown'] > 0:
                player['attack_cooldown'] -= 1
    
    def _check_game_over(self):
        """Check if game is over"""
        p1_health = self.state.players['player1']['health']
        p2_health = self.state.players['player2']['health']
        p1_x = self.state.players['player1']['x']
        p2_x = self.state.players['player2']['x']
        
        if p1_health <= 0:
            self.state.game_over = True
            self.state.winner = 'player2'
        elif p2_health <= 0:
            self.state.game_over = True
            self.state.winner = 'player1'
        elif self.state.frame_count >= 3600:  # 60 seconds at 60 FPS
            self.state.game_over = True
            p1_dist_from_center = abs(p1_x - self.state.arena_width / 2)
            p2_dist_from_center = abs(p2_x - self.state.arena_width / 2)
            if p1_dist_from_center < p2_dist_from_center:
                self.state.winner = 'player1'
            else:
                self.state.winner = 'player2'
    
    def _calculate_rewards(self, prev_health: Dict[str, float]) -> Dict[str, float]:
        """Calculate rewards for both players"""
        rewards = {'player1': 0, 'player2': 0}
        
        # Health-based rewards
        p1_health_change = self.state.players['player1']['health'] - prev_health['player1']
        p2_health_change = self.state.players['player2']['health'] - prev_health['player2']
        
        rewards['player1'] += p1_health_change * 0.1 - p2_health_change * 0.1
        rewards['player2'] += p2_health_change * 0.1 - p1_health_change * 0.1
        
        # Win/lose rewards
        if self.state.game_over:
            if self.state.winner == 'player1':
                rewards['player1'] += 100
                rewards['player2'] -= 100
            else:
                rewards['player1'] -= 100
                rewards['player2'] += 100
        
        return rewards
    
    def reset(self) -> GameState:
        """Reset the game to initial state"""
        self.state = GameState(player1_stats=self.player1_stats, player2_stats=self.player2_stats)
        return self.state