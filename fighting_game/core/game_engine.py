from typing import Dict, Tuple
from .game_state import GameState
from .actions import Action

class GameEngine:
    """Main game engine that handles physics and game logic"""
    
    def __init__(self):
        self.state = GameState()
        self.physics_config = {
            'gravity': 0.8,
            'jump_force': -15,
            'move_speed': 5,
            'attack_range': 80,
            'attack_damage': 10,
            'attack_cooldown': 30
        }
    
    def step(self, player1_action: Action, player2_action: Action) -> Tuple[GameState, Dict[str, float]]:
        """Execute one game step and return new state + rewards"""
        if self.state.game_over:
            return self.state, {'player1': 0, 'player2': 0}
        
        # Store previous health for reward calculation
        prev_health = {
            'player1': self.state.players['player1']['health'],
            'player2': self.state.players['player2']['health']
        }
        
        # Apply actions
        self._apply_action('player1', player1_action)
        self._apply_action('player2', player2_action)
        
        # Update physics
        self._update_physics()
        
        # Handle combat
        self._handle_combat()
        
        # Update cooldowns
        self._update_cooldowns()
        
        # Check win conditions
        self._check_game_over()
        
        # Calculate rewards
        rewards = self._calculate_rewards(prev_health)
        
        self.state.frame_count += 1
        
        return self.state, rewards
    
    def _apply_action(self, player_id: str, action: Action):
        """Apply player action to game state"""
        player = self.state.players[player_id]
        
        # Reset action states
        player['is_blocking'] = False
        player['is_attacking'] = False
        
        if action == Action.LEFT:
            player['velocity_x'] = -self.physics_config['move_speed']
            player['facing_right'] = False
        elif action == Action.RIGHT:
            player['velocity_x'] = self.physics_config['move_speed']
            player['facing_right'] = True
        elif action == Action.JUMP and not player['is_jumping']:
            player['velocity_y'] = self.physics_config['jump_force']
            player['is_jumping'] = True
        elif action == Action.BLOCK:
            player['is_blocking'] = True
            player['velocity_x'] = 0
        elif action == Action.ATTACK and player['attack_cooldown'] <= 0:
            player['is_attacking'] = True
            player['attack_cooldown'] = self.physics_config['attack_cooldown']
        else:  # IDLE
            player['velocity_x'] = 0
    
    def _update_physics(self):
        """Update physics for all players"""
        for player in self.state.players.values():
            # Apply gravity
            if player['is_jumping']:
                player['velocity_y'] += self.physics_config['gravity']
            
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
        distance = abs(p1['x'] - p2['x'])
        
        # Player 1 attacking Player 2
        if (p1['is_attacking'] and distance <= self.physics_config['attack_range'] 
            and not p2['is_blocking']):
            p2['health'] -= self.physics_config['attack_damage']
        
        # Player 2 attacking Player 1
        if (p2['is_attacking'] and distance <= self.physics_config['attack_range'] 
            and not p1['is_blocking']):
            p1['health'] -= self.physics_config['attack_damage']
    
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
        self.state = GameState()
        return self.state