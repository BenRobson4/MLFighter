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
        data = asdict(self)
        # Convert Action enums to strings if they're still enums
        for player_id, player_data in data['players'].items():
            if 'current_action' in player_data and hasattr(player_data['current_action'], 'name'):
                player_data['current_action'] = player_data['current_action'].name
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameFrame':
        """Create GameFrame from dictionary"""
        # Convert action strings back to Action enums if needed
        from ..core import Action
        for player_id, player_data in data['players'].items():
            if 'current_action' in player_data and isinstance(player_data['current_action'], str):
                try:
                    player_data['current_action'] = Action[player_data['current_action']]
                except KeyError:
                    player_data['current_action'] = Action.IDLE
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
        
        # Deep copy player states and convert enums to strings
        players_data = {}
        for player_id, player_state in engine.state.players.items():
            player_copy = dict(player_state)
            # Convert current_action enum to string
            if 'current_action' in player_copy and hasattr(player_copy['current_action'], 'name'):
                player_copy['current_action'] = player_copy['current_action'].name
            # Convert input_buffer if it exists
            if 'input_buffer' in player_copy and player_copy['input_buffer'] is not None:
                if hasattr(player_copy['input_buffer'], 'name'):
                    player_copy['input_buffer'] = player_copy['input_buffer'].name
            players_data[player_id] = player_copy
        
        frame = GameFrame(
            frame_number=engine.state.frame_count,
            players=players_data,
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