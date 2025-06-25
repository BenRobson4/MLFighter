from dataclasses import dataclass
from typing import Dict, ClassVar
from ..globals.actions import Action
from .action_frame_data import ActionFrameData

@dataclass
class FighterFrameData:
    """Collection of frame data for all actions of a fighter"""
    actions: Dict[Action, ActionFrameData]
    
    def get_action_data(self, action: Action) -> ActionFrameData:
        """Get frame data for a specific action"""
        return self.actions.get(action, self._get_default_action_data(action))
    
    def _get_default_action_data(self, action: Action) -> ActionFrameData:
        """Get default frame data for an action"""
        if action == Action.ATTACK:
            return ActionFrameData(
                action=action,
                startup_frames=10,
                active_frames=20,
                recovery_frames=15
            )
        elif action == Action.JUMP:
            return ActionFrameData(
                action=action,
                startup_frames=5,
                active_frames=1,
                recovery_frames=15
            )
        elif action == Action.BLOCK:
            return ActionFrameData(
                action=action,
                startup_frames=15,
                active_frames=25,
                recovery_frames=10
            )
        else:
            # Default for movement actions
            return ActionFrameData(
                action=action,
                startup_frames=1,
                active_frames=10,
                recovery_frames=0
            )
    
    def to_dict(self) -> Dict:
        """Convert frame data to dictionary representation"""
        return {action.name: data.to_dict() for action, data in self.actions.items()}
    
    @classmethod
    def get_default(cls) -> 'FighterFrameData':
        """Get default frame data for all actions"""
        actions = {}
        # Create a temporary instance to access the instance method
        temp_instance = cls(actions={})
        for action in Action:
            actions[action] = temp_instance._get_default_action_data(action)
        return cls(actions=actions)
    
    @classmethod
    def from_dict(cls, data_dict: Dict) -> 'FighterFrameData':
        """Create frame data from dictionary representation"""
        actions = {}
        for action_name, frame_data in data_dict.items():
            try:
                action = Action[action_name]
                actions[action] = ActionFrameData(
                    action=action,
                    startup_frames=frame_data.get('startup_frames', 0),
                    active_frames=frame_data.get('active_frames', 0),
                    recovery_frames=frame_data.get('recovery_frames', 0)
                )
            except KeyError:
                continue  # Skip invalid action names
        
        return cls(actions=actions)