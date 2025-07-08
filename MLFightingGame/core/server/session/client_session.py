from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from ..protocols.message_types import GamePhase

if TYPE_CHECKING:
    from ...players.player import Player  # Avoid circular import by using TYPE_CHECKING

@dataclass
class ClientSession:
    """Tracks a single client's progress through the game"""
    client_id: str
    current_phase: GamePhase = GamePhase.CONNECTING
    player: Optional['Player'] = None
    
    # Shop state
    initial_shop_complete: bool = False
    current_shop_purchases: list = None
    
    # Ready state tracking
    ready_for_next_phase: bool = False 
    
    # Fight state
    current_opponent: Optional['Player'] = None
    current_replay: Optional[dict] = None
    replay_viewed: bool = False

    # Batch state
    current_batch_id: Optional[str] = None
    batch_fights_completed: int = 0
    batch_wins: int = 0
    batch_losses: int = 0
    batch_recorded_replays: list = None
    current_replay_index: int = 0
    
    # Progress tracking
    fights_completed: int = 0
    total_gold_earned: int = 0
    
    def __post_init__(self):
        if self.current_shop_purchases is None:
            self.current_shop_purchases = []