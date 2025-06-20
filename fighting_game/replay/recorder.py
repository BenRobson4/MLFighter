import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from ..core import GameEngine, Action


@dataclass
class GameFrame:
    """Represents a single frame of game state for replay"""
    frame_number: int
    players: Dict[str, Dict]
    actions: Dict[str, str]  # Store action names as strings
    rewards: Dict[str, float]
    game_over: bool
    winner: Optional[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameFrame':
        """Create GameFrame from dictionary"""
        return cls(**data)


class ReplayRecorder:
    """Records game sessions for later replay"""
    
    def __init__(self, save_directory: str = "fighting_game/replays"):
        self.save_directory = save_directory
        self.current_recording = []
        self.is_recording = False
        self.recording_metadata = {}
        
        # Create replay directory if it doesn't exist
        os.makedirs(save_directory, exist_ok=True)
    
    def start_recording(self, metadata: Dict[str, Any] = None):
        """Start recording a new game session"""
        self.is_recording = True
        self.current_recording = []
        self.recording_metadata = metadata or {}
        self.recording_metadata['start_time'] = datetime.now().isoformat()
    
    def record_frame(self, engine: GameEngine, actions: Dict[str, Action], 
                    rewards: Dict[str, float]):
        """Record a single frame of the game"""
        if not self.is_recording:
            return
        
        # Convert actions to string names for JSON serialization
        action_names = {player: action.name for player, action in actions.items()}
        
        frame = GameFrame(
            frame_number=engine.state.frame_count,
            players={
                'player1': dict(engine.state.players['player1']),
                'player2': dict(engine.state.players['player2'])
            },
            actions=action_names,
            rewards=rewards,
            game_over=engine.state.game_over,
            winner=engine.state.winner
        )
        
        self.current_recording.append(frame)
    
    def stop_recording(self) -> str:
        """Stop recording and save to file"""
        if not self.is_recording:
            return ""
        
        self.is_recording = False
        self.recording_metadata['end_time'] = datetime.now().isoformat()
        self.recording_metadata['total_frames'] = len(self.current_recording)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"replay_{timestamp}.json"
        filepath = os.path.join(self.save_directory, filename)
        
        # Save to file
        replay_data = {
            'metadata': self.recording_metadata,
            'frames': [frame.to_dict() for frame in self.current_recording]
        }
        
        with open(filepath, 'w') as f:
            json.dump(replay_data, f, indent=2)
        
        print(f"Replay saved to {filepath}")
        return filepath