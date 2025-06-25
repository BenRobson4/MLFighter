from enum import Enum, auto

class State(Enum):

    IDLE = auto()
    LEFT_STARTUP = auto()
    LEFT_ACTIVE = auto()
    LEFT_RECOVERY = auto()
    RIGHT_STARTUP = auto()
    RIGHT_ACTIVE = auto()
    RIGHT_RECOVERY = auto()
    ATTACK_STARTUP = auto()
    ATTACK_ACTIVE = auto()
    ATTACK_RECOVERY = auto()
    BLOCK_STARTUP = auto()
    BLOCK_ACTIVE = auto()
    BLOCK_RECOVERY = auto()
    JUMP_STARTUP = auto()
    JUMP_ACTIVE = auto()
    JUMP_RISING = auto()
    JUMP_FALLING = auto()
    JUMP_RECOVERY = auto()
    STUNNED = auto()

