from typing import Tuple

from . import GameState
from ..data_classes import PlayerState
from ..players import Player
from ..rewards import RewardRegistry
from ..globals.actions import Action

class GameEngine:

    def __init__(self):
        """
        Initialize the game engine with necessary components.
        This includes setting up the game state and player objects.
        """
        self.state = None
        self.player_1 = None
        self.player_2 = None
        self.frame_counter = 0  # Track overall game frames
        self.fight_over = False  # Flag to indicate if the game is over


    def step(self, game_state: GameState, player_1: Player, player_2: Player) -> GameState:
        """
        Perform a single step in the game loop, updating the game state.
        
        Args:
            game_state: Current state of the game
        
        Returns:
            Updated game state after processing actions and rewards
        """
        self.state = game_state

        self.player_1 = player_1
        self.player_2 = player_2

        self.player_1.state = self.state.get_player(1)
        self.player_2.state = self.state.get_player(2)

        self._get_actions()

        self._apply_actions()

        self._update_physics()
        
        self._handle_combat()

        self._update_frames()
        
        self._calculate_rewards()

        self._end_frame_checks()

        return game_state
    
    def _get_actions(self):
        """Get actions from players who can take new actions"""
        for player in [self.player_1, self.player_2]:
            if player.state.can_take_action():
                state_vector = self.state.get_state_vector(player.state.player_id)
                action = player.get_action(state_vector)
                
                # Store for potential commitment
                player.state.requested_action = action
                player.state.last_action_state = state_vector
                player.state.last_action_choice = action

    def _apply_actions(self):
        """Apply requested actions if they are allowed"""
        for player in [self.player_1, self.player_2]:
            if hasattr(player.state, 'requested_action'):
                action = player.state.requested_action
                
                # Check if action is allowed
                if player.state.is_action_allowed(action):
                    # Commit to the action
                    player.state.commit_to_action(action)
                    
                    # Apply physics and state changes based on action
                    if action == Action.LEFT:
                        player.state.velocity_x = -player.state.move_speed
                        player.state.facing_right = False
                    elif action == Action.RIGHT:
                        player.state.velocity_x = player.state.move_speed
                        player.state.facing_right = True
                    elif action == Action.JUMP:
                        player.state.velocity_y = -player.state.jump_force
                        player.state.is_jumping = True
                    elif action == Action.ATTACK:
                        player.state.is_attacking = True # Attack and block cooldowns are applied when the attack/block finishes
                    elif action == Action.BLOCK:
                        player.state.is_blocking = True
                    elif action == Action.IDLE:
                        player.state.velocity_x = 0
                
                # Clear the requested action
                delattr(player.state, 'requested_action')
        

    def _update_physics(self):
        """Update physics for all players"""
        for player in [self.player_1.state, self.player_2.state]:
            # Apply gravity to all players (whether jumping or falling)
            player.velocity_y += player.gravity
            
            # Update positions
            player.x += player.velocity_x
            player.y += player.velocity_y
            
            # Boundary checking
            player.x = max(50, min(self.state.arena_width - 50, player.x))
            
            # Ground collision
            if player.y >= self.state.ground_level:
                player.y = self.state.ground_level
                player.velocity_y = 0
                player.is_jumping = False
                player.jump_cooldown_remaining = player.jump_cooldown  # Reset jump cooldown
            
            # Apply friction/deceleration for horizontal movement
            if not player.is_attacking and player.current_action not in [Action.LEFT, Action.RIGHT]:
                player.velocity_x *= player.friction  # Apply friction coefficient
    
    def _handle_combat(self):
        """Handle combat interactions between players"""
        player1_state = self.player_1.state
        player2_state = self.player_2.state
        
        # Get attack hitboxes for both players
        p1_attack_hitbox = player1_state.get_attack_hitbox()
        p2_attack_hitbox = player2_state.get_attack_hitbox()
        
        # Get player hitboxes
        p1_hitbox = player1_state.get_hitbox()
        p2_hitbox = player2_state.get_hitbox()
        
        # Check collisions
        p1_hits_p2 = False
        p2_hits_p1 = False
        
        if p1_attack_hitbox:
            p1_hits_p2 = self._hitboxes_overlap(p1_attack_hitbox, p2_hitbox)
        
        if p2_attack_hitbox:
            p2_hits_p1 = self._hitboxes_overlap(p2_attack_hitbox, p1_hitbox)
        
        # Handle combat outcomes
        if p1_hits_p2 and p2_hits_p1:
            # Both players hit - both get stunned
            player1_state.stun_frames_remaining = player1_state.on_hit_stun
            player2_state.stun_frames_remaining = player2_state.on_hit_stun

            player1_state.is_stunned = True
            player2_state.is_stunned = True

            player1_state.health -= player2_state.attack_damage * (1 - player1_state.damage_reduction)
            player2_state.health -= player1_state.attack_damage * (1 - player2_state.damage_reduction)

        elif p1_hits_p2:
            # Player 1 hits Player 2
            if player2_state.is_blocking:
                # Player 2 blocks the attack and stuns player 1 for block stun frames
                player1_state.stun_frames_remaining = player2_state.on_block_stun
                player1_state.is_stunned = True

                # Apply block damage reduction and base damage reduction
                player2_state.health -= player1_state.attack_damage * (1 - player2_state.block_efficiency) * (1 - player2_state.damage_reduction)
            else:
                # Player 2 does not block, so they take full damage and get stunned
                player2_state.stun_frames_remaining = player1_state.on_hit_stun
                player2_state.is_stunned = True

                # Player 2 takes damage equal to player 1's attack damage after their damage reduction is applied
                player2_state.health -= player1_state.attack_damage * (1 - player2_state.damage_reduction)
        elif p2_hits_p1:
            # Player 2 hits Player 1 and the same results occur but in reverse
            if player1_state.is_blocking:
                player2_state.stun_frames_remaining = player1_state.on_block_stun
                player2_state.is_stunned = True

                # Apply block damage reduction and base damage reduction
                player1_state.health -= player2_state.attack_damage * (1 - player1_state.block_efficiency) * (1 - player1_state.damage_reduction)
            else:
                player1_state.stun_frames_remaining = player2_state.on_hit_stun
                player1_state.is_stunned = True

                # Apply damage to Player 1
                player1_state.health -= player2_state.attack_damage * (1 - player1_state.damage_reduction)

    def _hitboxes_overlap(self, box1: Tuple[float, float, float, float], 
                        box2: Tuple[float, float, float, float]) -> bool:
        """Check if two hitboxes overlap"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        return not (x2_1 < x1_2 or x2_2 < x1_1 or y2_1 < y1_2 or y2_2 < y1_1)

    def _update_frames(self):
        """Update frame counters and handle action state transitions"""
        # Increment overall game frame counter
        if not hasattr(self, 'frame_counter'):
            self.frame_counter = 0
        self.frame_counter += 1
        
        for player in [self.player_1.state, self.player_2.state]:
            # Increment action frame counter for active actions
            if player.action_frame_counter < player.action_total_frames:
                player.action_frame_counter += 1
            
            # Decrement cooldown counters
            if player.attack_cooldown_remaining > 0:
                player.attack_cooldown_remaining -= 1
            
            if player.block_cooldown_remaining > 0:
                player.block_cooldown_remaining -= 1

            if player.jump_cooldown_remaining > 0:
                player.jump_cooldown_remaining -= 1
            
            # Handle stun state
            if player.stun_frames_remaining > 0:
                player.stun_frames_remaining -= 1
                if player.stun_frames_remaining == 0:
                    player.is_stunned = False
            
            # Reset action flags when actions complete
            if player.action_frame_counter >= player.action_total_frames:
                # Reset action-specific flags
                if player.current_action == Action.ATTACK:
                    player.is_attacking = False
                    # Set attack cooldown when attack finishes
                    player.attack_cooldown_remaining = player.attack_cooldown
                
                if player.current_action == Action.BLOCK:
                    player.is_blocking = False
                    # Set block cooldown when block finishes
                    player.block_cooldown_remaining = player.block_cooldown
                
                # Note: is_jumping and jump_cooldown_remaining is handled in physics update when player hits ground
                
                # Reset to idle state
                player.current_action = Action.IDLE

        
    def _calculate_rewards(self):
        """Calculate and store rewards for players who made decisions this frame"""
        # First, accumulate rewards for all players this frame
        for player in [self.player_1, self.player_2]:
            frame_reward = 0
            reward_weights = player.get_reward_weights()
            
            for event_name, weight in reward_weights.items():
                reward_event_class = RewardRegistry.get_event(event_name)
                if reward_event_class:
                    reward_event = reward_event_class()
                    event_reward = reward_event.measure(self.state, player.state.player_id)
                    frame_reward += event_reward * weight
            
            player.state.accumulated_reward += frame_reward
        
        # Update ML agents for players whose actions have completed
        for player in [self.player_1, self.player_2]:
            if (player.state.last_action_state is not None and 
                player.state.last_action_choice is not None and
                player.state.action_frame_counter >= player.state.action_total_frames):
                
                # Normalize reward by action duration (I think this should stop biases which occur based on action duration)
                normalized_reward = player.state.accumulated_reward / player.state.action_total_frames
                
                # Get state vectors for ML update
                current_state = player.state.last_action_state
                next_state = self.state.get_state_vector(player.state.player_id)
                self.fight_over = self.state.is_game_over()
                
                # Update the ML agent
                player.update(
                    current_state, 
                    player.state.last_action_choice, 
                    normalized_reward, 
                    next_state, 
                    self.fight_over
                )
                
                # Reset for next action
                player.state.last_action_state = None
                player.state.last_action_choice = None
                player.state.accumulated_reward = 0
                player.state.action_frame_counter = 0

    def _end_frame_checks(self):
        """Perform end-of-frame checks and cleanup"""
        
        # Section 1: Health Validation
        self._validate_player_health()
        
        # Section 2: Position Validation
        self._validate_player_positions()
        
        # Section 3: State Consistency Checks
        self._validate_state_consistency()
        
        # Section 4: Fight Recording
        if self.is_recording:
            self._record_frame()
        
        # Section 5: Save Recording on Fight End
        if self.fight_over and self.is_recording:
            self._save_replay()

    def _validate_player_health(self):
        """Ensure player health values are within valid bounds"""
        for player in [self.player_1.state, self.player_2.state]:
            player.health = max(0.0, min(player.health, player.max_health))

    def _validate_player_positions(self):
        """Ensure players are within valid game boundaries"""
        for player in [self.player_1.state, self.player_2.state]:
            if player.y > self.state.ground_level:
                player.y = self.state.ground_level
                player.velocity_y = 0
                player.is_jumping = False
            
            player.x = max(50, min(self.state.arena_width - 50, player.x))

    def _validate_state_consistency(self):
        """Check for and fix any inconsistent state combinations"""
        for player in [self.player_1.state, self.player_2.state]:
            if player.is_stunned and player.stun_frames_remaining <= 0:
                player.is_stunned = False
            
            if player.y >= self.state.ground_level and player.is_jumping:
                player.is_jumping = False
            
            if player.is_blocking and player.is_attacking:
                if player.current_action == Action.BLOCK:
                    player.is_attacking = False
                else:
                    player.is_blocking = False

    def _record_frame(self):
        """Record current frame data for replay"""
        if not hasattr(self, 'replay_data'):
            # Initialize replay data with fight metadata
            self.replay_data = {
                'metadata': {
                    'arena_width': self.state.arena_width,
                    'ground_level': self.state.ground_level,
                    'max_frames': self.state.max_frames,
                    'player_configs': {
                        1: self._get_player_config(self.player_1.state),
                        2: self._get_player_config(self.player_2.state)
                    }
                },
                'frames': []
            }
        
        # Record only essential frame data
        frame_data = {
            'f': self.frame_counter,  # frame number
            'p1': self._compress_player_state(self.player_1.state),
            'p2': self._compress_player_state(self.player_2.state)
        }
        
        self.replay_data['frames'].append(frame_data)

    def _get_player_config(self, player_state: PlayerState) -> dict:
        """Get static player configuration for replay metadata"""
        return {
            'fighter_type': player_state.fighter_type,
            'max_health': player_state.max_health,
            'attack_damage': player_state.attack_damage,
            'width': player_state.width,
            'height': player_state.height,
            'gravity': player_state.gravity,
            'action_durations': player_state.action_durations
        }

    def _compress_player_state(self, player_state: PlayerState) -> dict:
        """Compress player state to minimal data needed for replay"""
        return {
            'x': round(player_state.x, 1),
            'y': round(player_state.y, 1),
            'h': round(player_state.health, 1),  # health
            'a': player_state.current_action.value,  # action
            'fr': player_state.facing_right,
            'flags': self._pack_boolean_flags(player_state)  # Pack multiple booleans into single int
        }

    def _pack_boolean_flags(self, player_state: PlayerState) -> int:
        """Pack boolean flags into a single integer for compression"""
        flags = 0
        if player_state.is_jumping: flags |= 1
        if player_state.is_blocking: flags |= 2
        if player_state.is_attacking: flags |= 4
        if player_state.is_stunned: flags |= 8
        return flags

    def _save_replay(self):
        """Save replay data to compressed file"""
        import json
        import gzip
        from datetime import datetime
        
        # Add final metadata
        self.replay_data['metadata']['total_frames'] = len(self.replay_data['frames'])
        self.replay_data['metadata']['winner'] = getattr(self.state, 'winner', None)
        self.replay_data['metadata']['timestamp'] = datetime.now().isoformat()
        
        # Save compressed replay
        filename = f"replay_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.gz"
        
        with gzip.open(filename, 'wt') as f:
            json.dump(self.replay_data, f, separators=(',', ':'))  # No whitespace for smaller file
        
        print(f"Replay saved: {filename}")