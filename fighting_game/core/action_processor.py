from typing import Dict, Optional
from .actions import Action
from ..config.fighter_config import Fighter
from .frame_data import ActionFrameData

class ActionProcessor:
    """Handles frame-based action processing"""
    
    def __init__(self, fighter_stats: Fighter):
        self.fighter_stats = fighter_stats
        self.frame_data = fighter_stats.frame_data
        self.attack_counter = 0  # Track unique attack IDs
    
    def can_perform_action(self, player_state: Dict, action: Action) -> bool:
        """Check if player can perform the requested action"""
        # If player is locked in an action, check if it can be cancelled
        if player_state['action_locked']:
            current_action_data = self.frame_data.action_frame_data[player_state['current_action']]
            
            # Check if action can be cancelled
            if current_action_data.can_cancel_after is not None:
                if player_state['action_frame'] >= current_action_data.can_cancel_after:
                    return True
            
            return False
        
        # Additional checks for specific actions
        if action == Action.JUMP and player_state['is_jumping']:
            return False
            
        return True
    
    def start_action(self, player_state: Dict, action: Action):
        """Start a new action"""
        player_state['current_action'] = action
        player_state['action_frame'] = 0
        
        action_data = self.frame_data.action_frame_data[action]
        player_state['action_locked'] = action_data.movement_locked
        
        # Clear input buffer
        player_state['input_buffer'] = None
        
        # Reset hit tracking for new attacks
        if action == Action.ATTACK:
            self.attack_counter += 1
            player_state['attack_id'] = self.attack_counter
            player_state['has_hit_opponent'] = False
    
    def update_action_frame(self, player_state: Dict):
        """Update the current action frame"""
        current_action_data = self.frame_data.action_frame_data[player_state['current_action']]
        
        player_state['action_frame'] += 1
        
        # Check if action is complete
        if player_state['action_frame'] >= current_action_data.total_frames:
            self.complete_action(player_state)
    
    def complete_action(self, player_state: Dict):
        """Complete the current action"""
        # Reset attack hit tracking when attack ends
        if player_state['current_action'] == Action.ATTACK:
            player_state['has_hit_opponent'] = False
            player_state['attack_id'] = 0
        
        player_state['action_locked'] = False
        player_state['current_action'] = Action.IDLE
        player_state['action_frame'] = 0
        
        # Process buffered input if any
        if player_state['input_buffer'] is not None:
            return player_state['input_buffer']
        
        return None
    
    def buffer_input(self, player_state: Dict, action: Action):
        """Buffer an input for later processing"""
        player_state['input_buffer'] = action
    
    def is_in_attack_active_frames(self, player_state: Dict) -> bool:
        """Check if attack is in active frames"""
        if player_state['current_action'] != Action.ATTACK:
            return False
            
        action_data = self.frame_data.action_frame_data[Action.ATTACK]
        if action_data.startup_frames is None or action_data.active_frames is None:
            # Fallback to old behavior
            return player_state['is_attacking']
        
        frame = player_state['action_frame']
        return (frame >= action_data.startup_frames and 
                frame < action_data.startup_frames + action_data.active_frames)
    
    def can_hit_opponent(self, player_state: Dict) -> bool:
        """Check if the attack can hit (hasn't hit yet and is in active frames)"""
        return (self.is_in_attack_active_frames(player_state) and 
                not player_state['has_hit_opponent'])
    
    def register_hit(self, player_state: Dict):
        """Register that the attack has hit"""
        player_state['has_hit_opponent'] = True