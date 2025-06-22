from enum import Enum

class FrameType(Enum):
    """Types of frames in an action sequence"""
    STARTUP = 'startup'       # Initial frames before hitbox appears
    ACTIVE = 'active'         # Frames where hitbox is active
    RECOVERY = 'recovery'     # Frames after hitbox disappears before new action
    TOTAL = 'total'           # Total frames for the action
