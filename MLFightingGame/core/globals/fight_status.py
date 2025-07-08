from enum import Enum

class FightStatus(Enum):
    """Status of a fight in progress"""
    INITIALIZING = "initializing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"
