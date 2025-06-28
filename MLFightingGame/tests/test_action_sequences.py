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
        print(f"  After step: state={self.player1_state.current_state}, velocity_y={self.player1_state.velocity_y:.2f}")
        self.assertEqual(self.player1_state.current_state, State.JUMP_ACTIVE)
        self.assertEqual(self.player1_state.state_frame_counter, 1)
        
        # Verify jump velocity was applied
        print(f"Verifying jump velocity: {self.player1_state.velocity_y}")
        self.assertLess(self.player1_state.velocity_y, 0, "Jump should give negative Y velocity")
        
        # Step 4: Transition to RISING phase
        print("Testing transition to JUMP_RISING...")
        self.engine.step(self.state)
        self.assertFalse(self.player1_state.is_grounded, "Player should no longer be grounded")
        self.assertEqual(self.player1_state.current_state, State.JUMP_RISING)
        self.assertLess(self.player1_state.velocity_y, 0, "Should still be rising")
        
        # Continue through RISING phase until velocity becomes positive
        print("Testing JUMP_RISING phase...")
        rising_frames = 0
        while self.player1_state.velocity_y < 0:
            self.engine.step(self.state)
            if self.player1_state.velocity_y < 0:
                rising_frames += 1
                self.assertEqual(self.player1_state.current_state, State.JUMP_RISING)
            else:
                print("Testing transition to JUMP_FALLING...")
                self.assertEqual(self.player1_state.current_state, State.JUMP_FALLING)
        
        # Step 5: Transition to FALLING phase when velocity becomes positive
        print("Testing JUMP_FALLING phase...")
        self.engine.step(self.state)
        print(f"  After step: state={self.player1_state.current_state}, velocity_y={self.player1_state.velocity_y:.2f}")
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
        
        self.engine.step(self.state)

        # Verify movement is happening
        print(f"Verifying leftward movement...")
        self.assertLess(self.player1_state.x, initial_x, "Player should move left")
        
        # Continue through active frames if any
        if active_frames > 1:
            for i in range(1, active_frames - 1):
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
        
        # Step the engine 1 step to apply the movement as it is only applied the frame after the state is updated
        self.engine.step(self.state)

        # Verify movement is happening
        print(f"Verifying rightward movement...")
        self.assertGreater(self.player1_state.x, initial_x, "Player should move right")
        
        # Continue through remaining active frames if any
        if active_frames > 1:
            for i in range(1, active_frames - 1):
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

    def test_attack_hits_idle_player(self):
        """Test that an attack hitting an idle player causes damage and stun, then stun wears off"""
        print("\n=== Testing ATTACK hits IDLE player ===")
        
        # Position players close enough for attack to connect
        # Assuming attack range is around 50-100 units
        self.player1_state.x = 100.0
        self.player2_state.x = 150.0  # 50 units apart
        
        # Set player1 to attack, player2 to idle
        self.player1.set_fixed_action(Action.ATTACK)
        self.player2.set_fixed_action(Action.IDLE)
        
        # Get frame data
        attack_data = self.player1_state.frame_data[Action.ATTACK]
        startup_frames = attack_data[0]
        active_frames = attack_data[1]
        recovery_frames = attack_data[2]
        
        # Store initial values
        p2_initial_health = self.player2_state.health
        p1_attack_damage = self.player1_state.attack_damage
        p2_damage_reduction = self.player2_state.damage_reduction
        expected_damage = p1_attack_damage * (1 - p2_damage_reduction)
        on_hit_stun_duration = self.player1_state.on_hit_stun
        
        print(f"Initial P2 health: {p2_initial_health}")
        print(f"P1 attack damage: {p1_attack_damage}, P2 damage reduction: {p2_damage_reduction}")
        print(f"Expected damage: {expected_damage}")
        print(f"On hit stun duration: {on_hit_stun_duration} frames")
        
        # Progress through startup frames
        print(f"Progressing through {startup_frames} startup frames...")
        self.engine.step(self.state)  # Enter ATTACK_STARTUP
        for _ in range(startup_frames - 1):
            self.engine.step(self.state)
            # No damage should occur during startup
            self.assertEqual(self.player2_state.health, p2_initial_health)
            self.assertNotEqual(self.player2_state.current_state, State.STUNNED)
        
        # Enter active frames - this is when the hit should occur
        print("Entering ATTACK_ACTIVE phase...")
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_ACTIVE)

        # Step forward 1 frame to allow the attack to deal damage
        self.engine.step(self.state)
        
        # Check that damage was dealt
        print(f"P2 health after hit: {self.player2_state.health}")
        self.assertAlmostEqual(
            self.player2_state.health, 
            p2_initial_health - expected_damage,
            places=2,
            msg="Player 2 should take damage"
        )
        
        # Check that player 2 got stunned
        self.assertTrue(self.player2_state.current_state, State.STUNNED)
        self.assertEqual(
            self.player2_state.stun_frames_remaining,
            on_hit_stun_duration,
            "Player 2 should be stunned for attacker's on_hit_stun duration"
        )
        
        # Store the state player 2 was in when hit (should be IDLE)
        p2_state_when_hit = self.player2_state.current_state
        print(f"P2 state when hit: {p2_state_when_hit}")
        
        # Now verify stun countdown
        print(f"\nVerifying stun countdown over {on_hit_stun_duration} frames...")
        
        # Player 2 should remain in their current state while stunned
        # and not be able to take new actions
        for frame in range(on_hit_stun_duration):
            # Try to make player 2 do something (they shouldn't be able to)
            self.player2.set_fixed_action(Action.ATTACK)
            
            self.engine.step(self.state)
            
            # Check stun is counting down correctly
            expected_stun_remaining = on_hit_stun_duration - frame - 1
            self.assertEqual(
                self.player2_state.stun_frames_remaining,
                expected_stun_remaining,
                f"Stun should countdown: expected {expected_stun_remaining} frames remaining"
            )
            
            # Player should still be in stunned state (can't take new actions)
            if expected_stun_remaining > 0:
                print(f"  Frame {frame + 1}: Stun remaining = {self.player2_state.stun_frames_remaining}")
                # They should NOT have entered attack state despite requesting it
                self.assertNotEqual(
                    self.player2_state.current_state, 
                    State.ATTACK_STARTUP,
                    "Stunned player should not be able to start new actions"
                )
        
        # After stun wears off, player should be able to act again
        print("\nVerifying player can act after stun wears off...")
        
        # Clear the got_stunned flag (this might happen automatically in your engine)
        # Check that stun has worn off
        self.assertEqual(self.player2_state.stun_frames_remaining, 0, "Stun should be fully worn off")
        
        # Now player 2 should be able to take a new action
        self.player2.set_fixed_action(Action.BLOCK)
        self.engine.step(self.state)
        
        # Verify player 2 can now take actions
        self.assertEqual(
            self.player2_state.current_state,
            State.BLOCK_STARTUP,
            "Player should be able to take new actions after stun wears off"
        )
        
        # Also verify player 1 has completed their attack sequence
        print(f"\nVerifying attacker completed their sequence...")
        # Player 1 should have gone through remaining active + recovery frames
        # and returned to IDLE
        if self.player1_state.current_state != State.IDLE:
            # Continue until player 1 returns to IDLE
            frames_to_idle = 0
            while self.player1_state.current_state != State.IDLE and frames_to_idle < 60:
                self.engine.step(self.state)
                frames_to_idle += 1
            
            self.assertEqual(
                self.player1_state.current_state,
                State.IDLE,
                "Attacker should return to IDLE after attack sequence"
            )
        
        print("✓ Attack hits idle player test passed!")
        
    def test_attack_hits_blocking_player(self):
        """Test that a blocked attack causes reduced damage and stuns the attacker"""
        print("\n=== Testing ATTACK blocked by opponent ===")
        
        # Position players close enough for attack to connect
        self.player1_state.x = 100.0
        self.player2_state.x = 150.0
        
        # Get frame data
        attack_data = self.player1_state.frame_data[Action.ATTACK]
        block_data = self.player2_state.frame_data[Action.BLOCK]
        attack_startup = attack_data[0]
        block_startup = block_data[0]
        
        print(f"Attack startup: {attack_startup}, Block startup: {block_startup}")
        
        # Store initial health
        initial_p2_health = self.player2_state.health
        
        # IMPORTANT: Set up the actions with proper timing
        # Player 2 needs to start blocking BEFORE player 1's attack becomes active
        
        # Calculate when P1's attack will become active
        attack_active_frame = attack_startup + 1  # +1 because of state-after-physics
        
        # Start P2's block early enough
        if block_startup >= attack_active_frame:
            # Block takes too long, start it first
            frames_to_prestart_block = block_startup - attack_active_frame + 2
            print(f"Pre-starting block by {frames_to_prestart_block} frames")
            
            self.player2.set_fixed_action(Action.BLOCK)
            self.player1.set_fixed_action(Action.IDLE)  # P1 waits
            
            for i in range(frames_to_prestart_block):
                self.engine.step(self.state)
            
            # Now start P1's attack
            self.player1.set_fixed_action(Action.ATTACK)
        else:
            # Both can start together
            self.player1.set_fixed_action(Action.ATTACK)
            self.player2.set_fixed_action(Action.BLOCK)
        
        # Progress until P1 attack becomes active
        print("\nProgressing to attack active...")
        frame_count = 0
        while self.player1_state.current_state != State.ATTACK_ACTIVE and frame_count < 20:
            self.engine.step(self.state)
            frame_count += 1
            
            # Check P2 isn't stunned during startup
            if self.player2_state.current_state == State.STUNNED and self.player1_state.current_state != State.ATTACK_ACTIVE:
                self.fail("P2 got stunned before P1's attack became active!")
        
        # Verify P2 is in BLOCK_ACTIVE when attack lands
        self.assertEqual(self.player1_state.current_state, State.ATTACK_ACTIVE)
        self.assertEqual(self.player2_state.current_state, State.BLOCK_ACTIVE, 
                        "P2 should be in BLOCK_ACTIVE when attack lands")
        
        # The hit should happen this frame (first frame of ATTACK_ACTIVE hitting BLOCK_ACTIVE)
        print("\nAttack hitting block...")
        self.engine.step(self.state)
        
        # Verify reduced damage from block
        expected_damage = (self.player1_state.attack_damage * 
                        (1 - self.player2_state.block_efficiency) * 
                        (1 - self.player2_state.damage_reduction))
        expected_health = initial_p2_health - expected_damage
        
        print(f"\nDamage calculation:")
        print(f"  Base damage: {self.player1_state.attack_damage}")
        print(f"  Block efficiency: {self.player2_state.block_efficiency}")
        print(f"  Damage reduction: {self.player2_state.damage_reduction}")
        print(f"  Expected chip damage: {expected_damage: .2f}")
        print(f"  P2 health: {initial_p2_health} -> {self.player2_state.health}")
        
        self.assertAlmostEqual(self.player2_state.health, expected_health, places=2,
                            msg="Blocker should take reduced damage")
        
        # Verify attacker got stunned (not the defender)
        print(f"\nStun states:")
        print(f"  P1 stunned: {self.player1_state.current_state == State.STUNNED}")
        print(f"  P2 stunned: {self.player2_state.current_state == State.STUNNED}")
        print(f"  P1 stun remaining: {self.player1_state.stun_frames_remaining}")
        
        self.assertEqual(self.player1_state.current_state, State.STUNNED, "Attacker should be stunned when blocked")
        self.assertNotEqual(self.player2_state.current_state, State.STUNNED, "Defender should not be stunned when blocking")
        
        # Verify stun duration matches defender's on_block_stun
        # Note: -1 because one frame has passed since the stun was applied
        self.assertEqual(self.player1_state.stun_frames_remaining, 
                        self.player2_state.on_block_stun,
                        "Attacker should be stunned for defender's on_block_stun duration")
        
        print("✓ Attack blocked test passed!")
        
    def test_simultaneous_attacks(self):
        """Test that simultaneous attacks cause both players to take damage and get stunned"""
        print("\n=== Testing simultaneous ATTACKS ===")
        
        # Position players close enough for attacks to connect
        self.player1_state.x = 100.0
        self.player2_state.x = 150.0
        
        # Store initial values
        p1_initial_health = self.player1_state.health
        p2_initial_health = self.player2_state.health
        p1_damage = self.player1_state.attack_damage
        p2_damage = self.player2_state.attack_damage
        p1_reduction = self.player1_state.damage_reduction
        p2_reduction = self.player2_state.damage_reduction
        p1_on_hit_stun = self.player1_state.on_hit_stun
        p2_on_hit_stun = self.player2_state.on_hit_stun
        
        print(f"Initial healths: P1={p1_initial_health}, P2={p2_initial_health}")
        print(f"Attack damages: P1={p1_damage}, P2={p2_damage}")
        print(f"Damage reductions: P1={p1_reduction}, P2={p2_reduction}")
        print(f"On-hit stun durations: P1={p1_on_hit_stun}, P2={p2_on_hit_stun}")
        
        # Get frame data
        p1_attack_data = self.player1_state.frame_data[Action.ATTACK]
        p2_attack_data = self.player2_state.frame_data[Action.ATTACK]
        p1_startup = p1_attack_data[0]
        p2_startup = p2_attack_data[0]
        
        print(f"\nAttack startups: P1={p1_startup}, P2={p2_startup}")
        
        # Calculate when each attack will become active
        # Remember: state changes happen AFTER physics, so active state appears on frame startup+1
        p1_active_frame = p1_startup + 1
        p2_active_frame = p2_startup + 1
        
        print(f"P1 will be ATTACK_ACTIVE on frame {p1_active_frame}")
        print(f"P2 will be ATTACK_ACTIVE on frame {p2_active_frame}")
        
        # Start the player with longer startup first
        if p1_startup > p2_startup:
            # P1 needs to start first
            frames_to_delay_p2 = p1_startup - p2_startup
            print(f"\nP1 has longer startup, starting P1 attack {frames_to_delay_p2} frames early")
            
            self.player1.set_fixed_action(Action.ATTACK)
            self.player2.set_fixed_action(Action.IDLE)
            
            # Run P1's early startup frames
            for frame in range(frames_to_delay_p2):
                self.engine.step(self.state)
                print(f"  Early frame {frame+1}: P1={self.player1_state.current_state}, P2=IDLE")
            
            # Now start P2's attack
            self.player2.set_fixed_action(Action.ATTACK)
            
        elif p2_startup > p1_startup:
            # P2 needs to start first
            frames_to_delay_p1 = p2_startup - p1_startup
            print(f"\nP2 has longer startup, starting P2 attack {frames_to_delay_p1} frames early")
            
            self.player1.set_fixed_action(Action.IDLE)
            self.player2.set_fixed_action(Action.ATTACK)
            
            # Run P2's early startup frames
            for frame in range(frames_to_delay_p1):
                self.engine.step(self.state)
                print(f"  Early frame {frame+1}: P1=IDLE, P2={self.player2_state.current_state}")
            
            # Now start P1's attack
            self.player1.set_fixed_action(Action.ATTACK)
            
        else:
            # Same startup, both can start together
            print("\nBoth have same startup, starting together")
            self.player1.set_fixed_action(Action.ATTACK)
            self.player2.set_fixed_action(Action.ATTACK)
        
        # Now both attacks are in progress, continue until both reach ACTIVE on the same frame
        remaining_startup = min(p1_startup, p2_startup)
        print(f"\nProgressing through {remaining_startup} synchronized startup frames...")
        
        for frame in range(remaining_startup):
            self.engine.step(self.state)
            print(f"  Sync frame {frame+1}: P1={self.player1_state.current_state}, P2={self.player2_state.current_state}")
        
        # Next frame should transition both to ACTIVE
        print("\nBoth attacks becoming active...")
        self.engine.step(self.state)
        print(f"  Active frame: P1={self.player1_state.current_state}, P2={self.player2_state.current_state}")
        
        # Verify both are in ATTACK_ACTIVE
        self.assertEqual(self.player1_state.current_state, State.ATTACK_ACTIVE,
                        "P1 should be in ATTACK_ACTIVE")
        self.assertEqual(self.player2_state.current_state, State.ATTACK_ACTIVE,
                        "P2 should be in ATTACK_ACTIVE")
        
        # DEBUG: Check hitboxes before collision
        print("\nDEBUG - Checking hitboxes before collision:")
        p1_hitbox = self.player1.get_hitbox()
        p2_hitbox = self.player2.get_hitbox()
        p1_attack_hitbox = self.player1.get_attack_hitbox()
        p2_attack_hitbox = self.player2.get_attack_hitbox()
        
        print(f"  P1 hitbox: {p1_hitbox}")
        print(f"  P2 hitbox: {p2_hitbox}")
        print(f"  P1 attack hitbox: {p1_attack_hitbox}")
        print(f"  P2 attack hitbox: {p2_attack_hitbox}")
        
        if p1_attack_hitbox and p2_hitbox:
            overlap1 = self.engine._hitboxes_overlap(p1_attack_hitbox, p2_hitbox)
            print(f"  P1 attack overlaps P2: {overlap1}")
        
        if p2_attack_hitbox and p1_hitbox:
            overlap2 = self.engine._hitboxes_overlap(p2_attack_hitbox, p1_hitbox)
            print(f"  P2 attack overlaps P1: {overlap2}")
        
        # The collision happens on the first frame of ACTIVE (due to state-after-physics)
        # So we need one more step for the hit to register
        print("\nCollision frame...")
        self.engine.step(self.state)
        print(f"  After collision: P1={self.player1_state.current_state}, P2={self.player2_state.current_state}")
                
        # Both should now be stunned
        self.assertEqual(self.player1_state.current_state, State.STUNNED, 
                        "Player 1 should be stunned after trading hits")
        self.assertEqual(self.player2_state.current_state, State.STUNNED, 
                        "Player 2 should be stunned after trading hits")
        
        # Calculate expected damage
        expected_p1_health = p1_initial_health - (p2_damage * (1 - p1_reduction))
        expected_p2_health = p2_initial_health - (p1_damage * (1 - p2_reduction))
        
        print(f"\nHealth after trade:")
        print(f"  P1: {p1_initial_health} -> {self.player1_state.health} (expected {expected_p1_health})")
        print(f"  P2: {p2_initial_health} -> {self.player2_state.health} (expected {expected_p2_health})")
        
        # Verify damage was dealt correctly
        self.assertAlmostEqual(
            self.player1_state.health,
            expected_p1_health,
            places=2,
            msg="Player 1 should take damage from Player 2's attack"
        )
        self.assertAlmostEqual(
            self.player2_state.health,
            expected_p2_health,
            places=2,
            msg="Player 2 should take damage from Player 1's attack"
        )
        
        # Verify stun durations (minus 1 because a frame has passed)
        print(f"\nStun remaining: P1={self.player1_state.stun_frames_remaining}, P2={self.player2_state.stun_frames_remaining}")
        
        self.assertEqual(self.player1_state.stun_frames_remaining, p1_on_hit_stun,
                        "Player 1 should have correct stun duration")
        self.assertEqual(self.player2_state.stun_frames_remaining, p2_on_hit_stun,
                        "Player 2 should have correct stun duration")
        
        print("✓ Simultaneous attacks test passed!")

    def test_attack_priority_and_punish(self):
        """Test that faster attack wins, then stunned player punishes during recovery"""
        print("\n=== Testing attack priority and recovery punish ===")
        
        # Position players close enough for attacks to connect
        self.player1_state.x = 100.0
        self.player2_state.x = 150.0
        
        # Get frame data
        p1_attack_data = self.player1_state.frame_data[Action.ATTACK]
        p2_attack_data = self.player2_state.frame_data[Action.ATTACK]
        p1_startup = p1_attack_data[0]
        p1_active = p1_attack_data[1]
        p1_recovery = p1_attack_data[2]
        p2_startup = p2_attack_data[0]
        p2_active = p2_attack_data[1]
        p2_recovery = p2_attack_data[2]
        
        # Determine who has faster startup (will hit first)
        if p1_startup < p2_startup:
            first_attacker = "P1"
            first_player = self.player1
            first_state = self.player1_state
            second_player = self.player2
            second_state = self.player2_state
            first_startup = p1_startup
            first_active = p1_active
            first_recovery = p1_recovery
            second_startup = p2_startup
        elif p2_startup < p1_startup:
            first_attacker = "P2"
            first_player = self.player2
            first_state = self.player2_state
            second_player = self.player1
            second_state = self.player1_state
            first_startup = p2_startup
            first_active = p2_active
            first_recovery = p2_recovery
            second_startup = p1_startup
        else:
            # Equal startup - arbitrarily choose P1 to go first by delaying P2
            print("Equal startup times - P1 will attack one frame earlier")
            first_attacker = "P1"
            first_player = self.player1
            first_state = self.player1_state
            second_player = self.player2
            second_state = self.player2_state
            first_startup = p1_startup
            first_active = p1_active
            first_recovery = p1_recovery
            second_startup = p2_startup
        
        stun_duration = first_state.on_hit_stun
        
        print(f"\nFrame data:")
        print(f"  {first_attacker} (first): startup={first_startup}, active={first_active}, recovery={first_recovery}")
        print(f"  {'P2' if first_attacker == 'P1' else 'P1'} (second): startup={second_startup}, stun={stun_duration}")
        
        # Store initial health values
        first_initial_health = first_state.health
        second_initial_health = second_state.health
        
        # === PHASE 1: First attacker hits and stuns second player ===
        print(f"\n=== PHASE 1: {first_attacker} attacks first ===")
        
        # Both players attempt to attack
        self.player1.set_fixed_action(Action.ATTACK)
        self.player2.set_fixed_action(Action.ATTACK)
        
        # If we need to ensure P1 goes first when they have equal startup
        if p1_startup == p2_startup and first_attacker == "P1":
            # Let P1 start one frame earlier
            self.player2.set_fixed_action(Action.IDLE)
            self.engine.step(self.state)
            self.player2.set_fixed_action(Action.ATTACK)
        
        # Progress through first attacker's startup
        print(f"Progressing through {first_attacker}'s startup...")
        for frame in range(first_startup):
            self.engine.step(self.state)
            print(f"  Frame {frame + 1}: {first_attacker}={first_state.current_state}, "
                f"{'P2' if first_attacker == 'P1' else 'P1'}={second_state.current_state}")
        
        # First attacker enters ACTIVE
        self.engine.step(self.state)
        print(f"\n{first_attacker} enters ACTIVE: {first_state.current_state}")
        self.assertEqual(first_state.current_state, State.ATTACK_ACTIVE)
        
        # Hit occurs on next frame (state-after-physics)
        self.engine.step(self.state)
        print(f"After hit: {first_attacker}={first_state.current_state}, "
            f"{'P2' if first_attacker == 'P1' else 'P1'}={second_state.current_state}")
        
        # Verify second player got stunned
        self.assertEqual(second_state.current_state, State.STUNNED,
                        f"Second attacker should be stunned")
        self.assertLess(second_state.health, second_initial_health,
                        "Second attacker should take damage")
        
        # === PHASE 2: Calculate punish window ===
        print(f"\n=== PHASE 2: Setting up punish ===")
        
        # First attacker has already been in ACTIVE for 2 frames
        # They have (active - 2) + recovery frames remaining
        remaining_first_attack = (first_active - 2) + first_recovery
        
        # Second player needs: stun duration + startup to hit
        frames_to_second_hit = stun_duration + second_startup + 1  # +1 for state-after-physics
        
        print(f"{first_attacker} has {remaining_first_attack} frames left in attack")
        print(f"{'P2' if first_attacker == 'P1' else 'P1'} needs {frames_to_second_hit} frames to hit")
        
        # Verify this is punishable
        if frames_to_second_hit >= remaining_first_attack:
            print("WARNING: Second attack might not punish - adjusting test expectations")
            can_punish = False
        else:
            can_punish = True
            print(f"Punish window: {remaining_first_attack - frames_to_second_hit} frames")
        
        # Progress through stun
        print(f"\nWaiting for stun to wear off ({stun_duration} frames)...")
        
        # Second player tries to attack immediately when unstunned
        second_player.set_fixed_action(Action.ATTACK)
        
        for frame in range(stun_duration):
            self.engine.step(self.state)
            if frame % 5 == 0 or frame == stun_duration - 1:
                print(f"  Stun frame {frame + 1}/{stun_duration}: "
                    f"{second_state.current_state}, stun_remaining={second_state.stun_frames_remaining}")
        
        # === PHASE 3: Second player attacks during first player's recovery ===
        print(f"\n=== PHASE 3: Punish attempt ===")
        
        # Second player should now be starting their attack
        self.engine.step(self.state)
        print(f"After unstun: {'P2' if first_attacker == 'P1' else 'P1'}={second_state.current_state}")
        self.assertEqual(second_state.current_state, State.ATTACK_STARTUP,
                        "Second player should start attacking after unstun")
        
        # Progress through second player's startup
        print(f"\nProgressing through {'P2' if first_attacker == 'P1' else 'P1'}'s startup...")
        for frame in range(second_startup - 1):  # -1 because we already did one frame
            self.engine.step(self.state)
            print(f"  Frame {frame + 2}: {first_attacker}={first_state.current_state}, "
                f"{'P2' if first_attacker == 'P1' else 'P1'}={second_state.current_state}")
        
        # Second player enters ACTIVE
        self.engine.step(self.state)
        print(f"\n{'P2' if first_attacker == 'P1' else 'P1'} enters ACTIVE")
        self.assertEqual(second_state.current_state, State.ATTACK_ACTIVE)
        
        # Check first player's state - should be in RECOVERY if punishable
        print(f"{first_attacker} is in: {first_state.current_state}")
        if can_punish:
            self.assertIn(first_state.current_state, 
                        [State.ATTACK_RECOVERY, State.IDLE],
                        f"{first_attacker} should be in recovery or idle")
        
        # Hit occurs on next frame
        self.engine.step(self.state)
        print(f"\nAfter punish hit: {first_attacker}={first_state.current_state}, "
            f"{'P2' if first_attacker == 'P1' else 'P1'}={second_state.current_state}")
        
        if can_punish:
            # Verify first player got hit during recovery
            self.assertEqual(first_state.current_state, State.STUNNED,
                            f"{first_attacker} should be stunned from punish")
            self.assertLess(first_state.health, first_initial_health,
                        f"{first_attacker} should take damage from punish")
            
            print(f"\n✓ {first_attacker} successfully punished during recovery!")
        else:
            print(f"\n! Could not punish - frame data doesn't allow it")
        
        # Final health summary
        print(f"\nFinal health:")
        print(f"  P1: {self.player1_state.health}/{self.player1_state.max_health}")
        print(f"  P2: {self.player2_state.health}/{self.player2_state.max_health}")
        
        print("\n✓ Attack priority and punish test completed!")

    def test_hit_during_jump_rising(self):
        """Test that a player hit while rising returns to JUMP_RISING after stun"""
        print("\n=== Testing hit during JUMP_RISING ===")
        
        # Position players close enough for attacks
        self.player1_state.x = 100.0
        self.player2_state.x = 150.0
        
        # Modify P1's vertical attack range to hit airborne opponents
        original_y_range = self.player1_state.y_attack_range
        self.player1_state.y_attack_range = 400  # Massive vertical range
        print(f"Increased P1 y_attack_range: {original_y_range} -> 400")
        
        # Get frame data
        jump_data = self.player2_state.frame_data[Action.JUMP]
        jump_startup = jump_data[0]
        jump_active = jump_data[1]  # Should be 1 frame
        attack_data = self.player1_state.frame_data[Action.ATTACK]
        attack_startup = attack_data[0]
        
        # Calculate jump physics
        jump_force = self.player2_state.jump_force
        gravity = self.player2_state.gravity
        
        # Frames from jump start to various points
        frames_to_velocity_applied = jump_startup + jump_active  # When upward velocity is applied
        time_to_peak_after_velocity = jump_force / gravity  # Frames from velocity application to peak
        total_frames_to_peak = frames_to_velocity_applied + time_to_peak_after_velocity
        total_frames_in_air = frames_to_velocity_applied + (time_to_peak_after_velocity * 2)
        
        print(f"\nJump timeline (from action start):")
        print(f"  Jump startup: {jump_startup} frames")
        print(f"  Velocity applied at: frame {frames_to_velocity_applied}")
        print(f"  Peak reached at: frame {total_frames_to_peak:.1f}")
        print(f"  Landing at: frame {total_frames_in_air:.1f}")
        print(f"  Total air time after velocity: {time_to_peak_after_velocity * 2:.1f} frames")
        
        # Calculate when P2 will be in JUMP_RISING state
        # JUMP_RISING starts after velocity is applied and lasts until peak
        rising_start_frame = frames_to_velocity_applied + 1  # +1 for state-after-physics
        rising_end_frame = total_frames_to_peak
        
        print(f"\nJUMP_RISING window: frames {rising_start_frame:.0f} to {rising_end_frame:.0f}")
        
        # Determine when to start attack to hit during JUMP_RISING
        # We want to hit in the middle of the rising period
        target_hit_frame = rising_start_frame + (rising_end_frame - rising_start_frame) * 0.5
        
        # Account for attack timing (startup + 1 for state-after-physics + 1 for hit detection)
        attack_needs_frames = attack_startup + 2
        ideal_attack_start = target_hit_frame - attack_needs_frames
        
        print(f"\nAttack timing:")
        print(f"  Target hit frame: {target_hit_frame:.1f}")
        print(f"  Attack needs: {attack_needs_frames} frames")
        print(f"  Ideal attack start: frame {ideal_attack_start:.1f}")
        
        # Ensure attack starts at a valid time (not negative)
        actual_attack_start = max(0, ideal_attack_start)
        
        # Predict when hit will actually occur
        predicted_hit_frame = actual_attack_start + attack_needs_frames
        
        # Check if we can hit during JUMP_RISING
        if predicted_hit_frame > rising_end_frame:
            print(f"\nWARNING: Attack too slow to hit during JUMP_RISING")
            print(f"  Hit would occur at frame {predicted_hit_frame:.1f}, but rising ends at {rising_end_frame:.1f}")
            print("  Adjusting to hit during early JUMP_FALLING instead")
            can_hit_rising = False
        else:
            can_hit_rising = True
            print(f"\nHit predicted at frame {predicted_hit_frame:.1f} (during JUMP_RISING)")
        
        # Reduce stun duration to ensure aerial recovery
        original_stun = self.player1_state.on_hit_stun
        # Ensure stun is short enough that P2 is still airborne after
        max_stun = int((total_frames_in_air - predicted_hit_frame) * 0.7)  # 70% of remaining air time
        self.player1_state.on_hit_stun = min(3, max_stun)
        print(f"Reduced on_hit_stun: {original_stun} -> {self.player1_state.on_hit_stun}")
        
        # === PHASE 1: Execute the synchronized actions ===
        print("\n=== PHASE 1: Executing jump and attack ===")
        
        # Start both actions with proper timing
        if actual_attack_start == 0:
            # Both start together
            self.player1.set_fixed_action(Action.ATTACK)
            self.player2.set_fixed_action(Action.JUMP)
            print("Starting both actions simultaneously")
        else:
            # Jump starts first
            self.player1.set_fixed_action(Action.IDLE)
            self.player2.set_fixed_action(Action.JUMP)
            print(f"Starting jump first, attack will begin at frame {actual_attack_start:.0f}")
        
        # Progress frame by frame
        for frame in range(int(predicted_hit_frame) + 1):
            # Start attack at the right time
            if frame == int(actual_attack_start) and actual_attack_start > 0:
                print(f"\nFrame {frame}: Starting P1's attack")
                self.player1.set_fixed_action(Action.ATTACK)
            
            # Step the engine
            self.engine.step(self.state)
            
            # Log important frames
            if frame % 5 == 0 or frame in [int(actual_attack_start), int(predicted_hit_frame)]:
                print(f"  Frame {frame}: P1={self.player1_state.current_state}, "
                    f"P2={self.player2_state.current_state}, "
                    f"P2_Y={self.player2_state.y:.1f}, P2_Vy={self.player2_state.velocity_y:.1f}")
        
        # === PHASE 2: Verify the hit occurred ===
        print("\n=== PHASE 2: Verifying hit ===")
        
        # Check that P2 got stunned
        self.assertEqual(self.player2_state.current_state, State.STUNNED,
                        "P2 should be stunned from the hit")
        
        # Store velocity to verify proper state after stun
        velocity_when_hit = self.player2_state.velocity_y
        print(f"P2 velocity when hit: {velocity_when_hit:.1f}")
        
        # === PHASE 3: P2 stunned in air ===
        print(f"\n=== PHASE 3: P2 stunned in air ===")
        
        for frame in range(self.player1_state.on_hit_stun):
            self.engine.step(self.state)
            if frame == 0 or frame == self.player1_state.on_hit_stun - 1:
                print(f"  Stun frame {frame + 1}: Y={self.player2_state.y:.1f}, "
                    f"Vy={self.player2_state.velocity_y:.1f}")
        
        # === PHASE 4: P2 recovers from stun ===
        print(f"\n=== PHASE 4: P2 recovers from aerial stun ===")
        
        self.engine.step(self.state)
        
        print(f"After stun recovery:")
        print(f"  State: {self.player2_state.current_state}")
        print(f"  Y position: {self.player2_state.y:.1f}")
        print(f"  Y velocity: {self.player2_state.velocity_y:.1f}")
        print(f"  Still airborne: {not self.player2_state.is_grounded}")
        
        # P2 should return to appropriate jump state based on velocity
        if not self.player2_state.is_grounded:
            if self.player2_state.velocity_y < 0:
                self.assertEqual(self.player2_state.current_state, State.JUMP_RISING,
                                "P2 should return to JUMP_RISING with upward velocity")
            else:
                self.assertEqual(self.player2_state.current_state, State.JUMP_FALLING,
                                "P2 should return to JUMP_FALLING with downward velocity")
        else:
            self.assertIn(self.player2_state.current_state,
                        [State.JUMP_RECOVERY, State.IDLE],
                        "P2 should be in landing state if grounded")
        
        # Restore original values
        self.player1_state.y_attack_range = original_y_range
        self.player1_state.on_hit_stun = original_stun
        
        print("\n✓ Hit during jump test passed!")


    def test_hit_during_jump_falling(self):
        """Test that a player hit while falling returns to JUMP_FALLING after stun"""
        print("\n=== Testing hit during JUMP_FALLING ===")
        
        # Position players
        self.player1_state.x = 100.0
        self.player2_state.x = 150.0
        
        # Modify P1's vertical attack range
        original_y_range = self.player1_state.y_attack_range
        self.player1_state.y_attack_range = 400
        print(f"Increased P1 y_attack_range: {original_y_range} -> 400")
        
        # Get frame data
        jump_data = self.player2_state.frame_data[Action.JUMP]
        jump_startup = jump_data[0]
        jump_active = jump_data[1]
        attack_data = self.player1_state.frame_data[Action.ATTACK]
        attack_startup = attack_data[0]
        
        # Calculate complete jump timeline
        jump_force = self.player2_state.jump_force
        gravity = self.player2_state.gravity
        
        frames_to_velocity_applied = jump_startup + jump_active
        time_to_peak_after_velocity = jump_force / gravity
        total_frames_to_peak = frames_to_velocity_applied + time_to_peak_after_velocity
        total_frames_in_air = frames_to_velocity_applied + (time_to_peak_after_velocity * 2)
        
        # JUMP_FALLING starts after peak
        falling_start_frame = total_frames_to_peak
        falling_end_frame = total_frames_in_air
        
        print(f"\nJump timeline:")
        print(f"  Total frames to peak: {total_frames_to_peak:.1f}")
        print(f"  Total frames to landing: {total_frames_in_air:.1f}")
        print(f"  JUMP_FALLING window: frames {falling_start_frame:.0f} to {falling_end_frame:.0f}")
        
        # Target middle of falling phase
        target_hit_frame = falling_start_frame + (falling_end_frame - falling_start_frame) * 0.5
        
        # Calculate when to start attack
        attack_needs_frames = attack_startup + 2
        ideal_attack_start = target_hit_frame - attack_needs_frames
        actual_attack_start = max(0, ideal_attack_start)
        predicted_hit_frame = actual_attack_start + attack_needs_frames
        
        print(f"\nAttack timing:")
        print(f"  Target hit frame: {target_hit_frame:.1f}")
        print(f"  Ideal attack start: frame {ideal_attack_start:.1f}")
        print(f"  Actual attack start: frame {actual_attack_start:.1f}")
        print(f"  Predicted hit: frame {predicted_hit_frame:.1f}")
        
        # Check feasibility
        if predicted_hit_frame >= falling_end_frame:
            print(f"\nWARNING: Attack too slow, P2 would land before hit")
            # Adjust to hit earlier in fall
            actual_attack_start = max(0, falling_start_frame + 2 - attack_needs_frames)
            predicted_hit_frame = actual_attack_start + attack_needs_frames
            print(f"  Adjusted to hit at frame {predicted_hit_frame:.1f}")
        
        # Reduce stun
        original_stun = self.player1_state.on_hit_stun
        max_stun = int((total_frames_in_air - predicted_hit_frame) * 0.7)
        self.player1_state.on_hit_stun = min(3, max_stun)
        print(f"Reduced on_hit_stun: {original_stun} -> {self.player1_state.on_hit_stun}")
        
        # === Execute the test ===
        print("\n=== Executing jump and timed attack ===")
        
        # Start with proper timing
        if actual_attack_start == 0:
            self.player1.set_fixed_action(Action.ATTACK)
            self.player2.set_fixed_action(Action.JUMP)
        else:
            self.player1.set_fixed_action(Action.IDLE)
            self.player2.set_fixed_action(Action.JUMP)
        
        # Progress to hit
        for frame in range(int(predicted_hit_frame) + 1):
            if frame == int(actual_attack_start) and actual_attack_start > 0:
                print(f"\nFrame {frame}: Starting P1's attack")
                self.player1.set_fixed_action(Action.ATTACK)
            
            self.engine.step(self.state)
            
            if frame % 5 == 0 or frame in [int(total_frames_to_peak), int(predicted_hit_frame)]:
                print(f"  Frame {frame}: P2={self.player2_state.current_state}, "
                    f"Y={self.player2_state.y:.1f}, Vy={self.player2_state.velocity_y:.1f}")
        
        # Verify hit
        self.assertEqual(self.player2_state.current_state, State.STUNNED,
                        "P2 should be stunned from the hit")
        
        # Process stun
        print(f"\n=== P2 stunned while falling ===")
        for frame in range(self.player1_state.on_hit_stun):
            self.engine.step(self.state)
        
        # Check recovery
        self.engine.step(self.state)
        
        print(f"\nAfter recovery:")
        print(f"  State: {self.player2_state.current_state}")
        print(f"  Grounded: {self.player2_state.is_grounded}")
        
        if not self.player2_state.is_grounded:
            self.assertEqual(self.player2_state.current_state, State.JUMP_FALLING,
                            "P2 should return to JUMP_FALLING if still airborne")
        
        # Restore
        self.player1_state.y_attack_range = original_y_range
        self.player1_state.on_hit_stun = original_stun
        
        print("\n✓ Hit during JUMP_FALLING test passed!")

    def test_aerial_attack_sequence(self):
        """Test that a player can attack mid-air and returns to the correct aerial state"""
        # Get frame data for JUMP and ATTACK actions
        jump_data = self.player1_state.frame_data[Action.JUMP]
        attack_data = self.player1_state.frame_data[Action.ATTACK]
        
        jump_startup_frames = jump_data[0]
        jump_active_frames = jump_data[1]
        
        attack_startup_frames = attack_data[0]
        attack_active_frames = attack_data[1]
        attack_recovery_frames = attack_data[2]
        
        # Initial state should be IDLE
        self.assertEqual(self.player1_state.current_state, State.IDLE)
        
        # Store original physics values
        original_jump_force = self.player1_state.jump_force
        original_gravity = self.player1_state.gravity
        
        # Boost jump force and reduce gravity for this test to ensure player stays airborne
        self.player1_state.jump_force = original_jump_force * 2.0
        self.player1_state.gravity = original_gravity * 0.3
        
        # Phase 1: Start jump sequence
        self.player1.set_fixed_action(Action.JUMP)
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.JUMP_STARTUP)
        
        # Complete jump startup
        for i in range(1, jump_startup_frames):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.JUMP_STARTUP)
        
        # Transition to jump active (applies upward velocity)
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.JUMP_ACTIVE)
        
        # Complete jump active phase
        for i in range(1, jump_active_frames):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.JUMP_ACTIVE)
        
        # Transition to jump rising (player is airborne with upward velocity)
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.JUMP_RISING)
        self.assertFalse(self.player1_state.is_grounded)
        self.assertLess(self.player1_state.velocity_y, 0)  # Negative velocity = upward
        
        # Phase 2: Attack while in JUMP_RISING state
        # Let player rise for a few frames first
        self.player1.set_fixed_action(Action.IDLE)  # No input for a few frames
        for _ in range(3):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.JUMP_RISING)
        
        # Now initiate attack while still rising
        self.player1.set_fixed_action(Action.ATTACK)
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_STARTUP)
        self.assertFalse(self.player1_state.is_grounded)  # Still airborne
        
        # Complete attack startup
        for i in range(1, attack_startup_frames):
            # Keep player airborne by maintaining upward position and velocity if needed
            if self.player1_state.y >= self.state.ground_level - 20:
                self.player1_state.y = self.state.ground_level - 30
                self.player1_state.velocity_y = -2.0  # Slight upward velocity
            
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.ATTACK_STARTUP)
            self.assertFalse(self.player1_state.is_grounded, f"Player landed during attack startup frame {i}")
        
        # Transition to attack active
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_ACTIVE)
        
        # Complete attack active phase
        for i in range(1, attack_active_frames):
            # Keep player airborne
            if self.player1_state.y >= self.state.ground_level - 20:
                self.player1_state.y = self.state.ground_level - 30
                self.player1_state.velocity_y = min(self.player1_state.velocity_y, 0)
            
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.ATTACK_ACTIVE)
            self.assertFalse(self.player1_state.is_grounded, f"Player landed during attack active frame {i}")
        
        # Transition to attack recovery
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_RECOVERY)
        
        # Complete attack recovery phase
        self.player1.set_fixed_action(Action.IDLE)  # No more inputs
        for i in range(1, attack_recovery_frames):
            # Keep player airborne
            if self.player1_state.y >= self.state.ground_level - 20:
                self.player1_state.y = self.state.ground_level - 30
                self.player1_state.velocity_y = 1.0  # Now falling
            
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.ATTACK_RECOVERY)
            self.assertFalse(self.player1_state.is_grounded, f"Player landed during attack recovery frame {i}")
        
        # Phase 3: Attack complete - should return to appropriate aerial state
        self.engine.step(self.state)
        
        # Player should return to either JUMP_RISING or JUMP_FALLING based on velocity
        if self.player1_state.velocity_y < 0:
            self.assertEqual(self.player1_state.current_state, State.JUMP_RISING)
        else:
            self.assertEqual(self.player1_state.current_state, State.JUMP_FALLING)
        
        # Player should still be airborne
        self.assertFalse(self.player1_state.is_grounded)
        
        # Verify player can take another action (should be actionable in air)
        self.assertTrue(self.player1.can_take_action())
        
        # Restore original physics values
        self.player1_state.jump_force = original_jump_force
        self.player1_state.gravity = original_gravity

    def test_aerial_attack_while_falling(self):
        """Test attacking while falling and returning to falling state"""
        # This test ensures the player can attack while falling and returns to falling
        
        # Set up player in falling state (simulate by setting state directly for this test)
        self.player1_state.current_state = State.JUMP_FALLING
        self.player1_state.is_grounded = False
        self.player1_state.velocity_y = 5.0  # Positive velocity = falling
        self.player1_state.y = -100.0  # Well above ground (negative Y is up)
        
        # Reduce gravity for this test to ensure we stay airborne
        original_gravity = self.player1_state.gravity
        self.player1_state.gravity = 0.5
        
        attack_data = self.player1_state.frame_data[Action.ATTACK]
        attack_startup_frames = attack_data[0]
        attack_active_frames = attack_data[1]
        attack_recovery_frames = attack_data[2]
        
        # Initial state should be JUMP_FALLING
        self.assertEqual(self.player1_state.current_state, State.JUMP_FALLING)
        self.assertFalse(self.player1_state.is_grounded)
        
        # Initiate attack while falling
        self.player1.set_fixed_action(Action.ATTACK)
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_STARTUP)
        
        # Complete full attack sequence
        # Startup phase
        for i in range(1, attack_startup_frames):
            # Keep player airborne
            if self.player1_state.y >= self.state.ground_level - 20:
                self.player1_state.y = self.state.ground_level - 50
                self.player1_state.velocity_y = 2.0  # Keep falling
            
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.ATTACK_STARTUP)
            self.assertFalse(self.player1_state.is_grounded, f"Player landed during startup frame {i}")
        
        # Active phase
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_ACTIVE)
        
        for i in range(1, attack_active_frames):
            # Keep player airborne
            if self.player1_state.y >= self.state.ground_level - 20:
                self.player1_state.y = self.state.ground_level - 50
                self.player1_state.velocity_y = 2.0  # Keep falling
            
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.ATTACK_ACTIVE)
            self.assertFalse(self.player1_state.is_grounded, f"Player landed during active frame {i}")
        
        # Recovery phase
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_RECOVERY)
        
        self.player1.set_fixed_action(Action.IDLE)
        for i in range(1, attack_recovery_frames):
            # Keep player airborne
            if self.player1_state.y >= self.state.ground_level - 20:
                self.player1_state.y = self.state.ground_level - 50
                self.player1_state.velocity_y = 2.0  # Keep falling
            
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.ATTACK_RECOVERY)
            self.assertFalse(self.player1_state.is_grounded, f"Player landed during recovery frame {i}")
        
        # Attack complete - should return to JUMP_FALLING (assuming still airborne)
        self.engine.step(self.state)
        
        if self.player1_state.is_grounded:
            self.assertEqual(self.player1_state.current_state, State.IDLE)
        else:
            # Should return to appropriate aerial state based on velocity
            if self.player1_state.velocity_y < 0:
                self.assertEqual(self.player1_state.current_state, State.JUMP_RISING)
            else:
                self.assertEqual(self.player1_state.current_state, State.JUMP_FALLING)
        
        # Restore original gravity
        self.player1_state.gravity = original_gravity

    def test_aerial_attack_lands_during_recovery(self):
        """Test that if player lands during attack recovery, they return to IDLE"""
        # Set up player in falling state close to ground
        self.player1_state.current_state = State.JUMP_FALLING
        self.player1_state.is_grounded = False
        self.player1_state.velocity_y = 2.0  # Falling slowly
        self.player1_state.y = -10.0  # Close to ground (10 units above)
        
        attack_data = self.player1_state.frame_data[Action.ATTACK]
        attack_startup_frames = attack_data[0]
        attack_active_frames = attack_data[1]
        attack_recovery_frames = attack_data[2]
        
        # Start attack
        self.player1.set_fixed_action(Action.ATTACK)
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_STARTUP)
        
        # Fast forward through attack phases
        self.player1.set_fixed_action(Action.IDLE)
        
        # Complete startup phase
        for _ in range(attack_startup_frames - 1):
            self.engine.step(self.state)
        
        # Transition to active
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_ACTIVE)
        
        # Complete active phase
        for _ in range(attack_active_frames - 1):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.ATTACK_ACTIVE)
        
        # Transition to recovery
        self.engine.step(self.state)
        self.assertEqual(self.player1_state.current_state, State.ATTACK_RECOVERY)
        
        # Set player position to ensure they land during recovery
        self.player1_state.y = -5.0  # Very close to ground
        self.player1_state.velocity_y = 3.0  # Falling faster
        
        # Continue recovery until completion
        landed = False
        for i in range(attack_recovery_frames - 1):
            self.engine.step(self.state)
            self.assertEqual(self.player1_state.current_state, State.ATTACK_RECOVERY)
            # Check if player has landed
            if self.player1_state.is_grounded:
                landed = True
        
        # Final step to complete recovery and transition to idle (hopefully)
        self.engine.step(self.state)

        # Final state check
        if landed:
            self.assertEqual(self.player1_state.current_state, State.IDLE)
        else:
            # If still airborne, should be in appropriate aerial state
            if self.player1_state.current_state != State.ATTACK_RECOVERY:
                # Attack completed
                self.assertIn(self.player1_state.current_state, [State.JUMP_RISING, State.JUMP_FALLING])
            
if __name__ == '__main__':
    unittest.main(verbosity=2, defaultTest='TestActionSequences.test_aerial_attack_lands_during_recovery')