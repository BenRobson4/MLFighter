from dataclasses import dataclass
from typing import Dict
from ..globals.actions import Action

@dataclass
class ActionFrameData:
    """Frame data for a specific action"""
    action: Action
    startup_frames: int
    active_frames: int
    recovery_frames: int
    
    @property
    def total_frames(self) -> int:
        """Total number of frames for this action"""
        return self.startup_frames + self.active_frames + self.recovery_frames
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            'startup_frames': self.startup_frames,
            'active_frames': self.active_frames,
            'recovery_frames': self.recovery_frames
        }