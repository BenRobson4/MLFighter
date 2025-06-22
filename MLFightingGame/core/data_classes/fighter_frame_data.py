from dataclasses import dataclass
from typing import Dict
from ..globals.actions import Action
from . import ActionFrameData

@dataclass
class FighterFrameData:
    """Collection of frame data for all actions of a fighter"""
    actions: Dict[Action, ActionFrameData]
    
    def get_action_data(self, action: Action) -> ActionFrameData:
        """Get frame data for a specific action"""
        return self.actions.get(action, self.get_default_action_data(action))
    
    def get_default_action_data(self, action: Action) -> ActionFrameData:
        """Get default frame data for an action"""
        if action == Action.ATTACK:
            return ActionFrameData(
                action=action,
                startup_frames=3,
                active_frames=2,
                recovery_frames=7,
                damage=10,
                knockback=5,
                stun_frames=10
            )
        elif action == Action.JUMP:
            return ActionFrameData(
                action=action,
                startup_frames=2,
                active_frames=15,
                recovery_frames=3
            )
        elif action == Action.BLOCK:
            return ActionFrameData(
                action=action,
                startup_frames=2,
                active_frames=10,
                recovery_frames=3
            )
        else:
            # Default for movement actions
            return ActionFrameData(
                action=action,
                startup_frames=1,
                active_frames=0,
                recovery_frames=0
            )
    
    @classmethod
    def get_default(cls) -> 'FighterFrameData':
        """Get default frame data for all actions"""
        actions = {}
        for action in Action:
            actions[action] = cls.get_default_action_data(cls, action)
        return cls(actions=actions)    

