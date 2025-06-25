import unittest
from typing import Dict, List

from ..core.data_classes import PlayerState, Fighter
from ..core.globals import Action, State
from ..core.players.player_state_builder import PlayerStateBuilder
from ..core.game_loop import GameState, GameEngine
from .test_player import TestPlayer


class TestActionSequences(unittest.TestCase):
    """Test that actions properly transition through their state sequences"""
   
    def setUp(self):
        """Set up test players and store their frame data"""
        # Create mock player objects with fighter data
        self.player1 = self._create_mock_player(1, "balanced")
        self.player2 = self._create_mock_player(2, "aggressive")
        
        # Build player states
        self.player1_state = PlayerStateBuilder.build(
            self.player1, 
            player_id=1, 
            spawn_x=100.0, 
            spawn_y=0.0
        )
        self.player2_state = PlayerStateBuilder.build(
            self.player2, 
            player_id=2, 
            spawn_x=200.0, 
            spawn_y=0.0
        )
        
        # Store frame data for easy access
        self.player1_frame_data = self.player1_state.frame_data
        self.player2_frame_data = self.player2_state.frame_data

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
   
    def _create_mock_player(self, player_id: int, fighter_name: str):
        """Create a mock player object with fighter data"""
        return TestPlayer(
            player_id=player_id, 
            fighter_name=fighter_name
        )
   
    def test_attack_sequence(self):
        """Test that attack action properly transitions through startup, active, and recovery states"""
        # Set player1 to always return ATTACK action
        self.player1.set_fixed_action(Action.ATTACK)
        
        # Get frame data for ATTACK action
        attack_data = self.player1_state.frame_data[Action.ATTACK]
        startup_frames = attack_data[0]
        active_frames = attack_data[1]
        recovery_frames = attack_data[2]
        total_frames = startup_frames + active_frames + recovery_frames
        
        # Initial state should be IDLE
        self.assertEqual(self.player1_state.current_state, State.IDLE)
        
        # Step 1: First frame should transition to STARTUP
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_STARTUP)
        self.assertEqual(self.player1_state.state_frame_counter, 1)
        
        # Step 2: Continue through STARTUP phase
        for i in range(1, startup_frames):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.ATTACK_STARTUP)
            self.assertEqual(self.player1_state.state_frame_counter, i + 1)
        
        # Step 3: Transition to ACTIVE phase
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_ACTIVE)
        self.assertEqual(self.player1_state.state_frame_counter, 1)  # Reset counter for new state
        
        # Step 4: Continue through ACTIVE phase
        for i in range(1, active_frames):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.ATTACK_ACTIVE)
            self.assertEqual(self.player1_state.state_frame_counter, i + 1)
        
        # Step 5: Transition to RECOVERY phase
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_RECOVERY)
        self.assertEqual(self.player1_state.state_frame_counter, 1)  # Reset counter for new state
        
        # Step 6: Continue through RECOVERY phase
        for i in range(1, recovery_frames):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.ATTACK_RECOVERY)
            self.assertEqual(self.player1_state.state_frame_counter, i + 1)
        
        # Step 7: Action complete, should return to IDLE
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.IDLE)
        self.assertEqual(self.player1_state.state_frame_counter, 1)
        
        # Verify that total frames elapsed matches expected total
        self.assertEqual(self.player1_state.action_complete, True)
        
        # Verify player is actionable again
        self.assertEqual(self.player1_state.current_state, State.IDLE)

        self.assertEqual(self.player1.actions_taken, 1)
    
    def test_block_sequence(self):
        """Test that block action properly transitions through startup, active, and recovery states"""
        print("\n=== Testing BLOCK sequence ===")
        
        # Set player1 to always return BLOCK action
        self.player1.set_fixed_action(Action.BLOCK)
        
        # Get frame data for BLOCK action
        block_data = self.player1_state.frame_data[Action.BLOCK]
        startup_frames = block_data[0]
        active_frames = block_data[1]
        recovery_frames = block_data[2]
        total_frames = startup_frames + active_frames + recovery_frames
        
        print(f"Block frame data: startup={startup_frames}, active={active_frames}, recovery={recovery_frames}")
        
        # Initial state should be IDLE
        print("Testing initial state...")
        self.assertEqual(self.player1_state.current_state, State.IDLE)
        
        # Step 1: First frame should transition to STARTUP
        print("Testing transition to BLOCK_STARTUP...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.BLOCK_STARTUP)
        self.assertEqual(self.player1_state.state_frame_counter, 1)
        
        # Step 2: Continue through STARTUP phase
        print(f"Testing BLOCK_STARTUP phase ({startup_frames} frames)...")
        for i in range(1, startup_frames):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.BLOCK_STARTUP)
            self.assertEqual(self.player1_state.state_frame_counter, i + 1)
        
        # Step 3: Transition to ACTIVE phase
        print("Testing transition to BLOCK_ACTIVE...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.BLOCK_ACTIVE)
        self.assertEqual(self.player1_state.state_frame_counter, 1)
        
        # Step 4: Continue through ACTIVE phase
        print(f"Testing BLOCK_ACTIVE phase ({active_frames} frames)...")
        for i in range(1, active_frames):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.BLOCK_ACTIVE)
            self.assertEqual(self.player1_state.state_frame_counter, i + 1)
        
        # Step 5: Transition to RECOVERY phase
        print("Testing transition to BLOCK_RECOVERY...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.BLOCK_RECOVERY)
        self.assertEqual(self.player1_state.state_frame_counter, 1)
        
        # Step 6: Continue through RECOVERY phase
        print(f"Testing BLOCK_RECOVERY phase ({recovery_frames} frames)...")
        for i in range(1, recovery_frames):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.BLOCK_RECOVERY)
            self.assertEqual(self.player1_state.state_frame_counter, i + 1)
        
        # Step 7: Action complete, should return to IDLE
        print("Testing return to IDLE...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.IDLE)
        self.assertEqual(self.player1_state.state_frame_counter, 1)
        
        # Verify action completion
        print("Verifying action completion...")
        self.assertEqual(self.player1_state.action_complete, True)
        self.assertEqual(self.player1.actions_taken, 1)
        
        print("✓ BLOCK sequence test passed!")

    def test_jump_sequence(self):
        """Test that jump action properly transitions through startup, active, rising, falling, and recovery states"""
        print("\n=== Testing JUMP sequence ===")
        
        # Set player1 to always return JUMP action
        self.player1.set_fixed_action(Action.JUMP)
        
        # Get frame data for JUMP action
        jump_data = self.player1_state.frame_data[Action.JUMP]
        startup_frames = jump_data[0]
        active_frames = jump_data[1]  # Should be 1 frame
        recovery_frames = jump_data[2]
        
        print(f"Jump frame data: startup={startup_frames}, active={active_frames}, recovery={recovery_frames}")
        
        # Store initial position
        initial_y = self.player1_state.y
        print(f"Initial Y position: {initial_y}")
        
        # Initial state should be IDLE
        print("Testing initial state...")
        self.assertEqual(self.player1_state.current_state, State.IDLE)
        self.assertTrue(self.player1_state.is_grounded)
        
        # Step 1: First frame should transition to STARTUP
        print("Testing transition to JUMP_STARTUP...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.JUMP_STARTUP)
        self.assertEqual(self.player1_state.state_frame_counter, 1)
        
        # Step 2: Continue through STARTUP phase
        print(f"Testing JUMP_STARTUP phase ({startup_frames} frames)...")
        for i in range(1, startup_frames):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.JUMP_STARTUP)
            self.assertEqual(self.player1_state.state_frame_counter, i + 1)
        
        # Step 3: Transition to ACTIVE phase (1 frame where velocity is applied)
        print("Testing transition to JUMP_ACTIVE (velocity application)...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.JUMP_ACTIVE)
        self.assertEqual(self.player1_state.state_frame_counter, 1)
        
        # Verify jump velocity was applied
        print(f"Verifying jump velocity: {self.player1_state.velocity_y}")
        self.assertLess(self.player1_state.velocity_y, 0, "Jump should give negative Y velocity")
        self.assertFalse(self.player1_state.is_grounded, "Player should no longer be grounded")
        
        # Step 4: Transition to RISING phase
        print("Testing transition to JUMP_RISING...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.JUMP_RISING)
        self.assertLess(self.player1_state.velocity_y, 0, "Should still be rising")
        
        # Continue through RISING phase until velocity becomes positive
        print("Testing JUMP_RISING phase...")
        rising_frames = 0
        while self.player1_state.velocity_y < 0:
            self.engine.step(self.state)
            rising_frames += 1
            self.assertEqual(self.player1_state.current_state, State.JUMP_RISING)
            print(f"  Rising frame {rising_frames}: Y={self.player1_state.y:.2f}, velocity={self.player1_state.velocity_y:.2f}")
        
        # Step 5: Transition to FALLING phase when velocity becomes positive
        print("Testing transition to JUMP_FALLING...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.JUMP_FALLING)
        self.assertGreaterEqual(self.player1_state.velocity_y, 0, "Should be falling")
        
        # Continue through FALLING phase until landing
        print("Testing JUMP_FALLING phase...")
        falling_frames = 0
        while not self.player1_state.is_grounded:
            self.engine.step(self.state)
            falling_frames += 1
            if not self.player1_state.is_grounded:
                self.assertEqual(self.player1_state.current_state, State.JUMP_FALLING)
                print(f"  Falling frame {falling_frames}: Y={self.player1_state.y:.2f}, velocity={self.player1_state.velocity_y:.2f}")
        
        # Step 6: Should transition to RECOVERY upon landing
        print("Testing transition to JUMP_RECOVERY upon landing...")
        self.assertEqual(self.player1_state.current_state, State.JUMP_RECOVERY)
        self.assertEqual(self.player1_state.state_frame_counter, 1)
        self.assertTrue(self.player1_state.is_grounded, "Player should be grounded again")
        
        # Step 7: Continue through RECOVERY phase
        print(f"Testing JUMP_RECOVERY phase ({recovery_frames} frames)...")
        for i in range(1, recovery_frames):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.JUMP_RECOVERY)
            self.assertEqual(self.player1_state.state_frame_counter, i + 1)
        
        # Step 8: Action complete, should return to IDLE
        print("Testing return to IDLE...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.IDLE)
        self.assertEqual(self.player1_state.state_frame_counter, 1)
        
        # Verify action completion and final position
        print("Verifying action completion...")
        self.assertEqual(self.player1_state.action_complete, True)
        self.assertEqual(self.player1.actions_taken, 1)
        self.assertEqual(self.player1_state.y, initial_y, "Player should return to ground level")
        
        print(f"Jump completed: {rising_frames} rising frames, {falling_frames} falling frames")
        print("✓ JUMP sequence test passed!")
        
    def test_move_left_sequence(self):
        """Test that left movement action properly transitions through states"""
        print("\n=== Testing LEFT movement sequence ===")
        
        # Set player1 to always return LEFT action
        self.player1.set_fixed_action(Action.LEFT)
        
        # Get frame data for LEFT action
        left_data = self.player1_state.frame_data[Action.LEFT]
        startup_frames = left_data[0]
        active_frames = left_data[1]
        recovery_frames = left_data[2]
        
        print(f"Left frame data: startup={startup_frames}, active={active_frames}, recovery={recovery_frames}")
        
        # Store initial position
        initial_x = self.player1_state.x
        print(f"Initial X position: {initial_x}")
        
        # Initial state should be IDLE
        print("Testing initial state...")
        self.assertEqual(self.player1_state.current_state, State.IDLE)
        
        # Movement actions typically have minimal or no startup
        if startup_frames > 0:
            # Step 1: First frame should transition to STARTUP
            print("Testing transition to LEFT_STARTUP...")
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.LEFT_STARTUP)
            self.assertEqual(self.player1_state.state_frame_counter, 1)
            
            # Step 2: Continue through STARTUP phase
            print(f"Testing LEFT_STARTUP phase ({startup_frames} frames)...")
            for i in range(1, startup_frames):
                self.engine.step(self.state)
                self.assertEqual(self.player1_state.current_state, State.LEFT_STARTUP)
                self.assertEqual(self.player1_state.state_frame_counter, i + 1)
        
        # Transition to ACTIVE phase
        print("Testing LEFT_ACTIVE phase...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.LEFT_ACTIVE)
        
        # Verify movement is happening
        print(f"Verifying leftward movement...")
        self.assertLess(self.player1_state.x, initial_x, "Player should move left")
        
        # Continue through active frames if any
        if active_frames > 1:
            for i in range(1, active_frames):
                self.engine.step(self.state)
                self.assertEqual(self.player1_state.current_state, State.LEFT_ACTIVE)
        
        # Recovery phase if any
        if recovery_frames > 0:
            print("Testing LEFT_RECOVERY phase...")
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.LEFT_RECOVERY)
            
            for i in range(1, recovery_frames):
                self.engine.step(self.state)
                self.assertEqual(self.player1_state.current_state, State.LEFT_RECOVERY)
        
        # Return to IDLE
        print("Testing return to IDLE...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.IDLE)
        
        # Verify action completion
        print("Verifying action completion...")
        self.assertEqual(self.player1_state.action_complete, True)
        self.assertEqual(self.player1.actions_taken, 1)
        
        print("✓ LEFT movement sequence test passed!")

    def test_move_right_sequence(self):
        """Test that right movement action properly transitions through states"""
        print("\n=== Testing RIGHT movement sequence ===")
        
        # Set player1 to always return RIGHT action
        self.player1.set_fixed_action(Action.RIGHT)
        
        # Get frame data for RIGHT action
        right_data = self.player1_state.frame_data[Action.RIGHT]
        startup_frames = right_data[0]
        active_frames = right_data[1]
        recovery_frames = right_data[2]
        
        print(f"Right frame data: startup={startup_frames}, active={active_frames}, recovery={recovery_frames}")
        
        # Store initial position
        initial_x = self.player1_state.x
        print(f"Initial X position: {initial_x}")
        
        # Initial state should be IDLE
        print("Testing initial state...")
        self.assertEqual(self.player1_state.current_state, State.IDLE)
        
        # Movement actions typically have minimal or no startup
        if startup_frames > 0:
            # Step 1: First frame should transition to STARTUP
            print("Testing transition to RIGHT_STARTUP...")
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.RIGHT_STARTUP)
            self.assertEqual(self.player1_state.state_frame_counter, 1)
            
            # Step 2: Continue through STARTUP phase
            print(f"Testing RIGHT_STARTUP phase ({startup_frames} frames)...")
            for i in range(1, startup_frames):
                self.engine.step(self.state)
                self.assertEqual(self.player1_state.current_state, State.RIGHT_STARTUP)
                self.assertEqual(self.player1_state.state_frame_counter, i + 1)
        
        # Transition to ACTIVE phase
        print("Testing RIGHT_ACTIVE phase...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.RIGHT_ACTIVE)
        
        # Verify movement is happening
        print(f"Verifying rightward movement...")
        self.assertGreater(self.player1_state.x, initial_x, "Player should move right")
        
        # Continue through active frames if any
        if active_frames > 1:
            for i in range(1, active_frames):
                self.engine.step(self.state)
                self.assertEqual(self.player1_state.current_state, State.RIGHT_ACTIVE)
        
        # Recovery phase if any
        if recovery_frames > 0:
            print("Testing RIGHT_RECOVERY phase...")
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.RIGHT_RECOVERY)
            
            for i in range(1, recovery_frames):
                self.engine.step(self.state)
                self.assertEqual(self.player1_state.current_state, State.RIGHT_RECOVERY)
        
        # Return to IDLE
        print("Testing return to IDLE...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.IDLE)
        
        # Verify action completion
        print("Verifying action completion...")
        self.assertEqual(self.player1_state.action_complete, True)
        self.assertEqual(self.player1.actions_taken, 1)
        
        print("✓ RIGHT movement sequence test passed!")
if __name__ == '__main__':
    unittest.main(verbosity=2, defaultTest='TestActionSequences.test_jump_sequence')