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
        self.previous_frame_data: Optional[Dict[str, Any]] = None  # NEW: Store previous frame for delta compression
        
        # Create replays directory if it doesn't exist
        self.replay_directory.mkdir(exist_ok=True, parents=True)
    
    def start_recording(self, game_state: GameState):
        """Start recording a new fight"""
        self.frames = []
        self.previous_frame_data = None  # NEW: Reset previous frame data
        self.start_time = time.time()
        
        # Initialize metadata with shorter property names
        self.metadata = {
            "v": "1.0",  # version
            "aw": game_state.arena_width,  # arena_width
            "ah": game_state.arena_height,  # arena_height
            "gl": game_state.ground_level,  # ground_level
            "mf": game_state.max_frames,  # max_frames
            "ts": datetime.now().isoformat(),  # timestamp_start
            "p1": game_state.get_player(1).fighter_name,  # player1_fighter
            "p2": game_state.get_player(2).fighter_name,  # player2_fighter
        }
    
    def record_frame(self, game_state: GameState, frame_counter: int):
        """Record the current frame's state with delta compression"""
        
        # Build current frame data
        current_frame_data = {
            "f": frame_counter,  # frame
            "p": {}  # players
        }
        
        # Collect current player data
        for player_id in [1, 2]:
            player_state = game_state.get_player(player_id)
            
            current_frame_data["p"][player_id] = {
                "x": round(player_state.x, 2),
                "y": round(player_state.y, 2),
                "h": player_state.health,                         # health
                "vx": round(player_state.velocity_x, 2),          # velocity_x
                "vy": round(player_state.velocity_y, 2),          # velocity_y
                "fr": player_state.facing_right,                  # facing_right
                "s": player_state.current_state.name,             # current_state
                "sf": player_state.state_frame_counter,           # state_frame_counter
                "g": player_state.is_grounded,                    # is_grounded
                "ac": player_state.attack_cooldown_remaining,     # attack_cooldown_remaining
                "bc": player_state.block_cooldown_remaining,      # block_cooldown_remaining
                "jc": player_state.jump_cooldown_remaining,       # jump_cooldown_remaining
                "st": player_state.stun_frames_remaining,         # stun_frames_remaining
            }
        
        # Apply delta compression
        if self.previous_frame_data is None:
            # First frame - store everything
            compressed_frame = current_frame_data
        else:
            # Subsequent frames - only store differences
            compressed_frame = {
                "f": frame_counter,
                "p": {}
            }
            
            for player_id in [1, 2]:
                current_player = current_frame_data["p"][player_id]
                previous_player = self.previous_frame_data["p"].get(player_id, {})
                
                # Find differences
                player_diff = {}
                for key, value in current_player.items():
                    if key not in previous_player or previous_player[key] != value:
                        player_diff[key] = value
                
                # Only include player data if there are changes
                if player_diff:
                    compressed_frame["p"][player_id] = player_diff
        
        # Store the compressed frame
        self.frames.append(compressed_frame)
        
        # Update previous frame data for next comparison
        self.previous_frame_data = current_frame_data
    
    def save_replay(self, winner: int = 0):
        """Save the recorded replay to a file"""
        if not self.frames:
            return None  # Nothing to save
        
        self.end_time = time.time()
        
        # Update metadata with fight results (using short property names)
        self.metadata["te"] = datetime.now().isoformat()  # timestamp_end
        self.metadata["tf"] = len(self.frames)  # total_frames
        self.metadata["d"] = round(self.end_time - self.start_time, 2)  # duration_seconds
        self.metadata["w"] = winner  # winner
        
        # Create replay data structure
        replay_data = {
            "meta": self.metadata,  # metadata -> meta
            "frames": self.frames
        }
        
        # Generate filename with timestamp and winner info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        p1_name = self.metadata["p1"] or "p1"
        p2_name = self.metadata["p2"] or "p2"
        winner_suffix = f"_winner_p{winner}" if winner in [1, 2] else "_draw"
        
        filename = f"{timestamp}_{p1_name}_vs_{p2_name}{winner_suffix}.json"
        filepath = self.replay_directory / filename
        
        # Save to file with minimal formatting
        with open(filepath, 'w') as f:
            json.dump(replay_data, f, separators=(',', ':'))  # No whitespace
        
        print(f"Replay saved to {filepath}")
        return filepath