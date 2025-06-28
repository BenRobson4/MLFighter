from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
from .actions import Action

@dataclass
class ActionFrameData:
    """Defines frame data for a single action"""
    total_frames: int  # Total frames the action takes
    can_cancel_after: Optional[int] = None  # Frame when action can be cancelled (None = cannot cancel)
    movement_locked: bool = True  # Whether movement is locked during action
    
    # Optional animation stages (useful for attacks)
    startup_frames: Optional[int] = None  # Frames before hitbox becomes active
    active_frames: Optional[int] = None   # Frames where hitbox is active
    recovery_frames: Optional[int] = None # Frames after hitbox disappears

@dataclass 
class FighterFrameData:
    """Complete frame data for a fighter"""
    action_frame_data: Dict[Action, ActionFrameData]
    
    @classmethod
    def get_default(cls) -> 'FighterFrameData':
        """Returns default frame data"""
        return cls(
            action_frame_data={
                Action.LEFT: ActionFrameData(total_frames=5, movement_locked=False),
                Action.RIGHT: ActionFrameData(total_frames=5, movement_locked=False),
                Action.JUMP: ActionFrameData(total_frames=3, can_cancel_after=2),
                Action.BLOCK: ActionFrameData(total_frames=1, movement_locked=True),
                Action.ATTACK: ActionFrameData(
                    total_frames=30,  # Matches current cooldown
                    startup_frames=5,
                    active_frames=10,
                    recovery_frames=15,
                    movement_locked=True
                ),
                Action.IDLE: ActionFrameData(total_frames=1, movement_locked=False)
            }
        )