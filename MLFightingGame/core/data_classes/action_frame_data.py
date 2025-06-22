from dataclasses import dataclass
from typing import Optional
from ..globals import FrameType
from ..globals import Action

@dataclass
class ActionFrameData:
    """Frame data for a specific action"""
    action: Action
    startup_frames: int
    active_frames: int
    recovery_frames: int
    
    # Optional hitbox data
    hitbox_width: Optional[int] = None
    hitbox_height: Optional[int] = None
    hitbox_x_offset: Optional[int] = None
    hitbox_y_offset: Optional[int] = None
    
    # Action properties
    damage: Optional[int] = None
    knockback: Optional[int] = None
    stun_frames: Optional[int] = None
    is_cancelable: bool = False
    
    @property
    def total_frames(self) -> int:
        """Total frames for this action"""
        return self.startup_frames + self.active_frames + self.recovery_frames
    
    def get_frame_count(self, frame_type: FrameType) -> int:
        """Get frame count for a specific frame type"""
        if frame_type == FrameType.STARTUP:
            return self.startup_frames
        elif frame_type == FrameType.ACTIVE:
            return self.active_frames
        elif frame_type == FrameType.RECOVERY:
            return self.recovery_frames
        elif frame_type == FrameType.TOTAL:
            return self.total_frames
        else:
            raise ValueError(f"Unknown frame type: {frame_type}")
    
    def is_hitbox_active(self, frame: int) -> bool:
        """Check if hitbox is active on a specific frame"""
        return self.startup_frames <= frame < (self.startup_frames + self.active_frames)
