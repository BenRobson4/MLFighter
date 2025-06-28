from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json
from .actions import Action
from .game_state import GameState

@dataclass
class RewardEvent:
    """Represents a single reward event that occurred"""
    reward_type: str
    value: float
    player_id: str
    frame: int
    details: Dict = field(default_factory=dict)

class RewardCalculator:
    """Handles all reward calculations for the game"""
    
    def __init__(self, config_path: str = "fighting_game/config/game_config.json"):
        # Load reward configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.reward_config = config['reward_system']['available_rewards']
        self.default_active = set(config['reward_system']['default_active_rewards'])
        
        # Track reward statistics
        self.reward_stats = defaultdict(lambda: defaultdict(float))
        self.reward_events = []
        
        # State tracking for reward calculations
        self.previous_state = None
        self.previous_actions = None
        
    def calculate_rewards(self, 
                         current_state: GameState,
                         actions: Dict[str, Action],
                         player_reward_weights: Dict[str, Dict[str, float]]) -> Tuple[Dict[str, float], List[RewardEvent]]:
        """Calculate all rewards for both players"""
        rewards = {'player1': 0.0, 'player2': 0.0}
        events = []
        
        # Skip first frame
        if self.previous_state is None:
            self.previous_state = current_state
            self.previous_actions = actions
            return rewards, events
        
        # Calculate each type of reward
        for player_id in ['player1', 'player2']:
            opponent_id = 'player2' if player_id == 'player1' else 'player1'
            player_weights = player_reward_weights.get(player_id, {})
            
            # Only calculate rewards that the player cares about (weight != 0)
            active_rewards = {k: v for k, v in player_weights.items() if v != 0}
            
            for reward_type in active_rewards:
                if reward_type in self.reward_config:
                    reward_value = self._calculate_specific_reward(
                        reward_type, player_id, opponent_id,
                        current_state, actions
                    )
                    
                    if reward_value != 0:
                        weighted_value = reward_value * active_rewards[reward_type]
                        rewards[player_id] += weighted_value
                        
                        # Track event
                        event = RewardEvent(
                            reward_type=reward_type,
                            value=weighted_value,
                            player_id=player_id,
                            frame=current_state.frame_count,
                            details={'base_value': reward_value, 'weight': active_rewards[reward_type]}
                        )
                        events.append(event)
                        
                        # Update statistics
                        self.reward_stats[player_id][reward_type] += weighted_value
        
        # Store events for analysis
        self.reward_events.extend(events)
        
        # Update state tracking
        self.previous_state = current_state
        self.previous_actions = actions
        
        return rewards, events
    
    def _calculate_specific_reward(self, reward_type: str, player_id: str, 
                                  opponent_id: str, state: GameState, 
                                  actions: Dict[str, Action]) -> float:
        """Calculate a specific type of reward"""
        
        # Get player states
        player = state.players[player_id]
        opponent = state.players[opponent_id]
        prev_player = self.previous_state.players[player_id]
        prev_opponent = self.previous_state.players[opponent_id]
        
        # Delegate to specific reward calculation method
        method_name = f"_calc_{reward_type}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(
                player, opponent, prev_player, prev_opponent,
                actions[player_id], actions[opponent_id]
            )
        
        return 0.0
    
    # Specific reward calculation methods
    
    def _calc_attack_landed(self, player, opponent, prev_player, prev_opponent, 
                           player_action, opponent_action) -> float:
        """Reward for successfully landing an attack"""
        # Check if player is attacking and opponent lost health
        if (player.get('is_attacking') and 
            opponent['health'] < prev_opponent['health'] and
            not opponent.get('is_blocking')):
            return 1.0  # Base reward, will be multiplied by weight
        return 0.0
    
    def _calc_attack_missed(self, player, opponent, prev_player, prev_opponent,
                           player_action, opponent_action) -> float:
        """Penalty for missing an attack"""
        # Check if player attacked but opponent didn't lose health
        if (player.get('is_attacking') and 
            player.get('action_frame', 0) > 5 and  # Past startup frames
            opponent['health'] == prev_opponent['health']):
            return 1.0  # Base penalty
        return 0.0
    
    def _calc_successful_block(self, player, opponent, prev_player, prev_opponent,
                              player_action, opponent_action) -> float:
        """Reward for successfully blocking an attack"""
        # Player is blocking and would have been hit
        if (player.get('is_blocking') and 
            opponent.get('is_attacking') and
            player['health'] == prev_player['health'] and
            self._players_in_range(player, opponent)):
            return 1.0
        return 0.0
    
    def _calc_failed_block(self, player, opponent, prev_player, prev_opponent,
                          player_action, opponent_action) -> float:
        """Penalty for failed block attempt"""
        # Player is blocking but still lost health
        if (player.get('is_blocking') and 
            player['health'] < prev_player['health']):
            return 1.0
        return 0.0
    
    def _calc_distance_penalty(self, player, opponent, prev_player, prev_opponent,
                              player_action, opponent_action) -> float:
        """Penalty based on distance from opponent"""
        distance = abs(player['x'] - opponent['x']) / 100.0  # Normalize
        return distance
    
    def _calc_jump_penalty(self, player, opponent, prev_player, prev_opponent,
                          player_action, opponent_action) -> float:
        """Penalty for jumping"""
        if player_action == Action.JUMP and not prev_player.get('is_jumping'):
            return 1.0
        return 0.0
    
    def _calc_health_lost(self, player, opponent, prev_player, prev_opponent,
                         player_action, opponent_action) -> float:
        """Penalty for health lost"""
        health_lost = prev_player['health'] - player['health']
        return max(0, health_lost)
    
    def _calc_win_bonus(self, player, opponent, prev_player, prev_opponent,
                       player_action, opponent_action) -> float:
        """Bonus for winning"""
        state = self.previous_state  # Use stored state reference
        if state.game_over and state.winner == player:
            return 1.0
        return 0.0
    
    def _calc_loss_penalty(self, player, opponent, prev_player, prev_opponent,
                          player_action, opponent_action) -> float:
        """Penalty for losing"""
        state = self.previous_state
        if state.game_over and state.winner != player and state.winner is not None:
            return 1.0
        return 0.0
    
    def _calc_dodged_attack(self, player, opponent, prev_player, prev_opponent,
                           player_action, opponent_action) -> float:
        """Reward for dodging an attack without blocking"""
        # Opponent attacked but missed, and player wasn't blocking
        if (opponent.get('is_attacking') and 
            not player.get('is_blocking') and
            player['health'] == prev_player['health'] and
            self._players_in_range(player, opponent)):
            return 1.0
        return 0.0
    
    def _calc_opponent_in_range(self, player, opponent, prev_player, prev_opponent,
                               player_action, opponent_action) -> float:
        """Bonus when opponent is in attack range"""
        if self._players_in_range(player, opponent):
            return 1.0
        return 0.0
    
    def _players_in_range(self, player, opponent) -> bool:
        """Check if players are in attack range"""
        x_distance = abs(player['x'] - opponent['x'])
        y_distance = abs(player['y'] - opponent['y'])
        # Approximate range check (you might want to use actual fighter stats)
        return x_distance <= 80 and y_distance <= 60
    
    def get_reward_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of all rewards accumulated"""
        return dict(self.reward_stats)
    
    def reset_stats(self):
        """Reset reward statistics"""
        self.reward_stats.clear()
        self.reward_events.clear()
        self.previous_state = None
        self.previous_actions = None
    
    def save_reward_summary(self, filepath: str):
        """Save reward summary to file"""
        summary = {
            'total_rewards': self.get_reward_summary(),
            'event_count': {
                player: {
                    reward_type: len([e for e in self.reward_events 
                                    if e.player_id == player and e.reward_type == reward_type])
                    for reward_type in self.reward_config.keys()
                }
                for player in ['player1', 'player2']
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)