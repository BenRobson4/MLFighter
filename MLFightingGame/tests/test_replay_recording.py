import unittest
import json
import os
from pathlib import Path
from typing import Dict, List
import shutil

from ..core.data_classes import PlayerState, Fighter
from ..core.globals import Action, State
from ..core.players.player_state_builder import PlayerStateBuilder
from ..core.game_loop import GameState, GameEngine
from .test_player import TestPlayer


class TestReplayRecording(unittest.TestCase):
    """Test that replay recording and saving functionality works correctly"""
   
    def setUp(self):
        """Set up test players and game engine"""
        # Create mock player objects with fighter data
        self.player1 = self._create_mock_player(1, "balanced")
        self.player2 = self._create_mock_player(2, "aggressive")
        
        # Build player states with known starting positions
        self.player1_state = PlayerStateBuilder.build(
            self.player1, 
            player_id=1, 
            spawn_x=200.0, 
            spawn_y=0.0
        )
        self.player2_state = PlayerStateBuilder.build(
            self.player2, 
            player_id=2, 
            spawn_x=600.0, 
            spawn_y=0.0
        )
        
        # Store initial values for verification
        self.initial_p1_x = 200.0
        self.initial_p1_y = 0.0
        self.initial_p2_x = 600.0
        self.initial_p2_y = 0.0
        self.initial_p1_health = self.player1_state.max_health
        self.initial_p2_health = self.player2_state.max_health

        self.state = GameState(
            arena_width=800, 
            arena_height=400, 
            player1_state=self.player1_state, 
            player2_state=self.player2_state
        )

        self.engine = GameEngine(
            state=self.state,
            player_1=self.player1,
            player_2=self.player2,
            is_recording=False
        )
        
        # Ensure replay directory exists for tests
        self.replay_dir = Path("replays")
        self.replay_dir.mkdir(exist_ok=True)
        
        # Store any pre-existing replay files to restore later
        self.existing_replays = list(self.replay_dir.glob("*.json"))

    def tearDown(self):
        """Clean up test replay files"""
        # Remove any replay files created during tests
        current_replays = list(self.replay_dir.glob("*.json"))
        for replay_file in current_replays:
            if replay_file not in self.existing_replays:
                replay_file.unlink()

    def _create_mock_player(self, player_id: int, fighter_name: str):
        """Create a mock player object with fighter data"""
        return TestPlayer(
            player_id=player_id, 
            fighter_name=fighter_name
        )
    
    def _get_latest_replay_file(self) -> Path:
        """Get the most recently created replay file"""
        replay_files = list(self.replay_dir.glob("*.json"))
        if not replay_files:
            return None
        return max(replay_files, key=lambda p: p.stat().st_mtime)
    
    def test_recording_disabled_by_default(self):
        """Test that recording is disabled by default"""
        self.assertFalse(self.engine.is_recording)
        
        # Run a few frames
        for _ in range(5):
            self.engine.step(self.state)
        
        # No replay should be created
        self.assertIsNone(self.engine.replay_recorder)
    
    def test_enable_recording(self):
        """Test that recording can be enabled"""
        self.engine.set_recording(True)
        self.assertTrue(self.engine.is_recording)
        
        # Step once to initialize recorder
        self.engine.step(self.state)
        
        # Recorder should be created
        self.assertIsNotNone(self.engine.replay_recorder)
    
    def test_reset_clears_recording(self):
        """Test that reset() clears recording state"""
        self.engine.set_recording(True)
        self.engine.step(self.state)
        
        # Verify recorder exists
        self.assertIsNotNone(self.engine.replay_recorder)
        
        # Reset engine
        self.engine.reset()
        
        # Recording should be disabled and recorder cleared
        self.assertFalse(self.engine.is_recording)
        self.assertIsNone(self.engine.replay_recorder)
    
    def test_simple_movement_recording(self):
        """Test recording of simple movement actions"""
        # Enable recording
        self.engine.set_recording(True)
        
        # Set fixed actions: P1 moves right, P2 moves left
        self.player1.set_fixed_action(Action.RIGHT)
        self.player2.set_fixed_action(Action.LEFT)
        
        # Run for specific number of frames
        frames_to_run = 10
        for _ in range(frames_to_run):
            self.engine.step(self.state)
        
        # Force game over to save replay
        self.engine.fight_over = True
        self.engine.winner = 1
        self.engine._save_replay()
        
        # Load the saved replay
        replay_file = self._get_latest_replay_file()
        self.assertIsNotNone(replay_file)
        
        with open(replay_file, 'r') as f:
            replay_data = json.load(f)
        
        # Verify metadata
        metadata = replay_data['metadata']
        self.assertEqual(metadata['player1_fighter'], 'balanced')
        self.assertEqual(metadata['player2_fighter'], 'aggressive')
        self.assertEqual(metadata['winner'], 1)
        self.assertEqual(metadata['arena_width'], 800)
        self.assertEqual(metadata['arena_height'], 400)
        
        # Verify frame count
        frames = replay_data['frames']
        self.assertEqual(len(frames), frames_to_run)
        
        # Verify first frame data
        first_frame = frames[0]
        self.assertEqual(first_frame['frame'], 1)
        
        # Check initial positions (should be close to spawn points)
        p1_data = first_frame['players']['1']
        p2_data = first_frame['players']['2']
        
        # Positions should be near initial values (may have moved slightly in first frame)
        self.assertAlmostEqual(p1_data['x'], self.initial_p1_x, delta=10)
        self.assertAlmostEqual(p2_data['x'], self.initial_p2_x, delta=10)
        
        # Health should be full
        self.assertEqual(p1_data['health'], self.initial_p1_health)
        self.assertEqual(p2_data['health'], self.initial_p2_health)
        
        # Verify movement over frames
        last_frame = frames[-1]
        p1_last = last_frame['players']['1']
        p2_last = last_frame['players']['2']
        
        # P1 should have moved right (higher X)
        self.assertGreater(p1_last['x'], p1_data['x'])
        # P2 should have moved left (lower X)
        self.assertLess(p2_last['x'], p2_data['x'])
    
    def test_combat_recording(self):
        """Test recording of combat interactions"""
        # Enable recording
        self.engine.set_recording(True)
        
        # Move players close together first
        self.player1_state.x = 350.0
        self.player2_state.x = 400.0
        
        # P1 attacks, P2 idles
        self.player1.set_fixed_action(Action.ATTACK)
        self.player2.set_fixed_action(Action.IDLE)
        
        # Get attack frame data
        attack_data = self.player1_state.frame_data[Action.ATTACK]
        startup_frames = attack_data[0]
        active_frames = attack_data[1]
        
        # Run through attack sequence
        total_frames = startup_frames + active_frames + 5  # Extra frames to see damage
        for _ in range(total_frames):
            self.engine.step(self.state)
        
        # Force save
        self.engine.fight_over = True
        self.engine._save_replay()
        
        # Load replay
        replay_file = self._get_latest_replay_file()
        with open(replay_file, 'r') as f:
            replay_data = json.load(f)
        
        frames = replay_data['frames']
        
        # Find frame where attack becomes active
        attack_active_frame = None
        for i, frame in enumerate(frames):
            if frame['players']['1']['current_state'] == 'ATTACK_ACTIVE':
                attack_active_frame = i
                break
        
        self.assertIsNotNone(attack_active_frame)
        
        # Check health before and after attack
        frame_before = frames[attack_active_frame - 1] if attack_active_frame > 0 else frames[0]
        frame_after = frames[min(attack_active_frame + active_frames, len(frames) - 1)]
        
        health_before = frame_before['players']['2']['health']
        health_after = frame_after['players']['2']['health']
        
        # P2 should have taken damage
        self.assertLess(health_after, health_before)
    
    def test_state_transitions_recorded(self):
        """Test that state transitions are properly recorded"""
        # Enable recording
        self.engine.set_recording(True)
        
        # P1 performs a jump
        self.player1.set_fixed_action(Action.JUMP)
        self.player2.set_fixed_action(Action.IDLE)
        
        # Run for enough frames to complete jump
        frames_to_run = 60
        for _ in range(frames_to_run):
            self.engine.step(self.state)
        
        # Force save
        self.engine.fight_over = True
        self.engine._save_replay()
        
        # Load replay
        replay_file = self._get_latest_replay_file()
        with open(replay_file, 'r') as f:
            replay_data = json.load(f)
        
        frames = replay_data['frames']
        
        # Track state transitions for P1
        states_seen = []
        for frame in frames:
            state = frame['players']['1']['current_state']
            if not states_seen or states_seen[-1] != state:
                states_seen.append(state)
        
        # Should see jump state sequence
        self.assertIn('JUMP_STARTUP', states_seen)
        self.assertIn('JUMP_ACTIVE', states_seen)
        
        # Verify Y position changes (player goes up then down)
        y_positions = [frame['players']['1']['y'] for frame in frames]
        
        # Find highest point
        min_y = min(y_positions)
        max_y_index = y_positions.index(min_y)
        
        # Y should decrease (go up) then increase (fall down)
        # Check that player was on ground at start
        self.assertEqual(y_positions[0], 0.0)
        # Check that player went up
        self.assertLess(min_y, 0.0)
        # Check that player came back down
        if max_y_index < len(y_positions) - 10:  # If there are enough frames after peak
            self.assertGreater(y_positions[-1], min_y)
    
    def test_cooldowns_recorded(self):
        """Test that cooldowns are properly recorded"""
        # Enable recording
        self.engine.set_recording(True)
        
        # P1 attacks once
        self.player1.set_fixed_action(Action.ATTACK)
        
        # Run attack to completion
        attack_data = self.player1_state.frame_data[Action.ATTACK]
        total_attack_frames = sum(attack_data)
        
        for _ in range(total_attack_frames + 5):
            self.engine.step(self.state)
        
        # Switch to idle to see cooldown counting down
        self.player1.set_fixed_action(Action.IDLE)
        
        for _ in range(10):
            self.engine.step(self.state)
        
        # Force save
        self.engine.fight_over = True
        self.engine._save_replay()
        
        # Load replay
        replay_file = self._get_latest_replay_file()
        with open(replay_file, 'r') as f:
            replay_data = json.load(f)
        
        frames = replay_data['frames']
        
        # Find when attack completes and cooldown starts
        cooldown_frames = []
        for frame in frames:
            cooldown = frame['players']['1']['attack_cooldown_remaining']
            cooldown_frames.append(cooldown)
        
        # Find max cooldown value (when it was set)
        max_cooldown = max(cooldown_frames)
        self.assertGreater(max_cooldown, 0)
        
        # Verify cooldown counts down
        cooldown_start_index = cooldown_frames.index(max_cooldown)
        if cooldown_start_index < len(cooldown_frames) - 5:
            # Check next few frames show decreasing cooldown
            for i in range(1, min(5, len(cooldown_frames) - cooldown_start_index)):
                if cooldown_frames[cooldown_start_index + i] > 0:
                    self.assertLess(
                        cooldown_frames[cooldown_start_index + i],
                        cooldown_frames[cooldown_start_index + i - 1]
                    )
    
    def test_multiple_fights_separate_replays(self):
        """Test that multiple fights create separate replay files"""
        initial_replay_count = len(list(self.replay_dir.glob("*.json")))
        
        # Fight 1 - Record
        self.engine.set_recording(True)
        for _ in range(10):
            self.engine.step(self.state)
        self.engine.fight_over = True
        self.engine.winner = 1
        self.engine._save_replay()
        
        # Reset for Fight 2
        self.engine.reset()
        
        # Fight 2 - Record
        self.engine.set_recording(True)
        for _ in range(15):
            self.engine.step(self.state)
        self.engine.fight_over = True
        self.engine.winner = 2
        self.engine._save_replay()
        
        # Should have 2 new replay files
        final_replay_count = len(list(self.replay_dir.glob("*.json")))
        self.assertEqual(final_replay_count - initial_replay_count, 2)
        
        # Load both replays and verify they're different
        replay_files = sorted(
            [f for f in self.replay_dir.glob("*.json") if f not in self.existing_replays],
            key=lambda p: p.stat().st_mtime
        )
        
        with open(replay_files[0], 'r') as f:
            replay1 = json.load(f)
        with open(replay_files[1], 'r') as f:
            replay2 = json.load(f)
        
        # Different frame counts
        self.assertEqual(len(replay1['frames']), 10)
        self.assertEqual(len(replay2['frames']), 15)
        
        # Different winners
        self.assertEqual(replay1['metadata']['winner'], 1)
        self.assertEqual(replay2['metadata']['winner'], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2, defaultTest='TestReplayRecording')