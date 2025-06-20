from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum
from .actions import Action

class ActionState(Enum):
    """States an action can be in"""
    STARTUP = "startup"
    ACTIVE = "active"
    RECOVERY = "recovery"
    COMPLETE = "complete"

@dataclass
class ActionFrameData:
    """Frame data for a single action"""
    total_frames: int
    startup_frames: int = 0
    active_frames: int = 0
    recovery_frames: int = 0
    
    # Movement data (for movement actions)
    movement_per_frame: Optional[Dict[str, float]] = None  # {'x': 5, 'y': 0}
    
    # Can this action be cancelled into other actions?
    cancellable_into: List[Action] = field(default_factory=list)
    
    # Can this action be performed in air?
    air_ok: bool = True
    
    def __post_init__(self):
        # If specific frame counts aren't provided, use total_frames
        if self.startup_frames == 0 and self.active_frames == 0 and self.recovery_frames == 0:
            self.active_frames = self.total_frames

@dataclass
class FighterFrameData:
    """Complete frame data for a fighter"""
    action_frame_data: Dict[Action, ActionFrameData] = field(default_factory=dict)
    
    def get_action_data(self, action: Action) -> ActionFrameData:
        """Get frame data for an action, with defaults if not specified"""
        if action in self.action_frame_data:
            return self.action_frame_data[action]
        
        # Default frame data for actions not explicitly defined
        defaults = {
            Action.IDLE: ActionFrameData(total_frames=1),
            Action.LEFT: ActionFrameData(total_frames=1, movement_per_frame={'x': -5, 'y': 0}),
            Action.RIGHT: ActionFrameData(total_frames=1, movement_per_frame={'x': 5, 'y': 0}),
            Action.JUMP: ActionFrameData(total_frames=1),
            Action.BLOCK: ActionFrameData(total_frames=1),
            Action.ATTACK: ActionFrameData(total_frames=30)  # Default attack cooldown
        }
        return defaults.get(action, ActionFrameData(total_frames=1))