from enum import Enum

class Action(Enum):
    """Available actions for players"""
    LEFT = 0
    RIGHT = 1
    JUMP = 2
    BLOCK = 3
    ATTACK = 4
    IDLE = 5