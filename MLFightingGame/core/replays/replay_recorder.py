import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..game_loop.game_state import GameState

class ReplayRecorder:
    """Handles recording and saving fight replays"""
    
    def __init__(self):
        self.frames: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.replay_directory = Path("replays")
        
        # Create replays directory if it doesn't exist
        self.replay_directory.mkdir(exist_ok=True, parents=True)
    
    def start_recording(self, game_state: GameState):
        """Start recording a new fight"""
        self.frames = []
        self.start_time = time.time()
        
        # Initialize metadata
        self.metadata = {
            "version": "1.0",
            "arena_width": game_state.arena_width,
            "arena_height": game_state.arena_height,
            "ground_level": game_state.ground_level,
            "max_frames": game_state.max_frames,
            "timestamp_start": datetime.now().isoformat(),
            "player1_fighter": game_state.get_player(1).fighter_name,
            "player2_fighter": game_state.get_player(2).fighter_name,
        }
    
    def record_frame(self, game_state: GameState, frame_counter: int):
        """Record the current frame's state"""
        frame_data = {
            "frame": frame_counter,
            "players": {}
        }
        
        # Record data for each player
        for player_id in [1, 2]:
            player_state = game_state.get_player(player_id)
            
            frame_data["players"][player_id] = {
                "x": player_state.x,
                "y": player_state.y,
                "health": player_state.health,
                "velocity_x": player_state.velocity_x,
                "velocity_y": player_state.velocity_y,
                "facing_right": player_state.facing_right,
                "current_state": player_state.current_state.name,
                "state_frame_counter": player_state.state_frame_counter,
                "is_grounded": player_state.is_grounded,
                "attack_cooldown_remaining": player_state.attack_cooldown_remaining,
                "block_cooldown_remaining": player_state.block_cooldown_remaining,
                "jump_cooldown_remaining": player_state.jump_cooldown_remaining,
                "stun_frames_remaining": player_state.stun_frames_remaining,
            }
        
        self.frames.append(frame_data)
    
    def save_replay(self, winner: int = 0):
        """Save the recorded replay to a file"""
        if not self.frames:
            return None  # Nothing to save
        
        self.end_time = time.time()
        
        # Update metadata with fight results
        self.metadata["timestamp_end"] = datetime.now().isoformat()
        self.metadata["total_frames"] = len(self.frames)
        self.metadata["duration_seconds"] = round(self.end_time - self.start_time, 2)
        self.metadata["winner"] = winner
        
        # Create replay data structure
        replay_data = {
            "metadata": self.metadata,
            "frames": self.frames
        }
        
        # Generate filename with timestamp and winner info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        p1_name = self.metadata["player1_fighter"] or "p1"
        p2_name = self.metadata["player2_fighter"] or "p2"
        winner_suffix = f"_winner_p{winner}" if winner in [1, 2] else "_draw"
        
        filename = f"{timestamp}_{p1_name}_vs_{p2_name}{winner_suffix}.json"
        filepath = self.replay_directory / filename
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(replay_data, f, indent=2)
        
        print(f"Replay saved to {filepath}")
        return filepath