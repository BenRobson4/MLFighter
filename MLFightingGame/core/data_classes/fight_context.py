from dataclasses import dataclass 
from typing import TYPE_CHECKING
from typing import Optional, Dict, Any
from datetime import datetime

if TYPE_CHECKING:
    from ..players import Player
    from ..game_loop import GameEngine, GameState
    from ..globals import FightStatus

@dataclass
class FightContext:
    """Container for all data related to a single fight"""
    fight_id: str
    client_1_id: str
    client_2_id: str
    player_1: 'Player'
    player_2: 'Player'
    game_engine: 'GameEngine'
    game_state: 'GameState'
    status: 'FightStatus'
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    winner: Optional[int] = None  # 1, 2, or 0 for draw
    total_frames: int = 0
    replay_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
