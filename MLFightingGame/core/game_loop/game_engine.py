from typing import Tuple, Optional
import logging

from . import GameState
from ..data_classes import PlayerState
from ..players import Player
from ..rewards import RewardRegistry
from ..globals.actions import Action
from ..globals.states import State
from ..replays import ReplayRecorder

logger = logging.getLogger(__name__)

class GameEngine:

    def __init__(self,
                state: GameState = None,
                player_1: Player = None,
                player_2: Player = None,
                is_recording: bool = False):
        """
        Initialize the game engine with necessary components.
        This includes setting up the game state and player objects.
        """
        self.state = state
        self.player_1 = player_1
        self.player_2 = player_2
        self.is_recording = is_recording
        self.frame_counter: int = 0  # Track frames this fight
        self.fight_over: bool = False 
        self.winner: int = 0
        self.replay_recorder: Optional[ReplayRecorder] = None


    def set_player(self, player_id: int, player: Player):
        """
        Set a player for the game engine.
        
        Args:
            player: Player object to be added
            player_id: ID of the player (1 or 2)
        """
        if player_id == 1:
            self.player_1 = player

        elif player_id == 2:
            self.player_2 = player

        else:
            raise ValueError("Player ID must be 1 or 2")

    def set_state(self, game_state: GameState):
        """
        Set the current game state.
        
        Args:
            game_state: GameState object representing the current state of the game
        """
        self.state = game_state

    def set_recording(self, is_recording: bool):
        """
        Enable or disable recording for the next fight.
        
        Args:
            is_recording: Whether to record the next fight
        """
        self.is_recording = is_recording
        logger.debug(f"Recording set to: {is_recording}")


    def step(self, game_state: GameState) -> GameState:
        """
        Perform a single step in the game loop, updating the game state.
        
        Args:
            game_state: Current state of the game
        
        Returns:
            Updated game state after processing actions and rewards
        """
        self.state = game_state

        self.player_1.state = self.state.get_player(1)
        self.player_2.state = self.state.get_player(2)

        self._get_actions()

        self._apply_actions()

        self._update_physics()
        
        self._handle_combat()

        self._update_frames()

        self._check_game_over()
        
        self._calculate_rewards()

        self._end_frame_checks()

        return game_state
    
    def reset(self) -> None:
        """
        Reset the game engine for a new fight.
        Resets player health, positions, and action states without recreating player objects.
        """
        if self.player_1 is None or self.player_2 is None:
            logger.warning("Cannot reset game engine: players not initialized")
            return
        
        # Reset fight status
        self.fight_over = False
        self.winner = 0
        self.frame_counter = 0
        
        # Clear any existing replay recorder
        self.replay_recorder = None
        
        # Reset recording status to False (must be explicitly enabled for each fight)
        self.is_recording = False
        
        # Reset player positions to starting positions
        self.player_1.state.x = self.player_1.state.start_x
        self.player_1.state.y = self.player_1.state.start_y
        self.player_2.state.x = self.player_2.state.start_x
        self.player_2.state.y = self.player_2.state.start_y
        
        # Reset velocities
        self.player_1.state.velocity_x = 0.0
        self.player_1.state.velocity_y = 0.0
        self.player_2.state.velocity_x = 0.0
        self.player_2.state.velocity_y = 0.0
        
        # Reset health
        self.player_1.state.health = self.player_1.state.max_health
        self.player_2.state.health = self.player_2.state.max_health
        
        # Reset action states
        for player_state in [self.player_1.state, self.player_2.state]:
            player_state.current_state = State.IDLE
            player_state.state_frame_counter = 0
            
            # Reset status flags
            player_state.current_state = State.IDLE
            player_state.got_stunned = False
            
            # Reset total reward for this fight
            player_state.total_reward = 0.0

            # Reset last action info
            player_state.last_action_state = None
            player_state.last_action_choice = None
            player_state.requested_action = None
        
        # Reset facing directions
        self.player_1.state.facing_right = True
        self.player_2.state.facing_right = False
        
        logger.debug("Game engine reset for new fight")
    
    def _get_actions(self):
        """Get actions from players who can take new actions"""
        for player in [self.player_1, self.player_2]:
            if player.can_take_action():
                state_vector = self.state.get_state_vector(player.state.player_id)
                action = player.get_action(state_vector)
                
                # Store for potential commitment
                player.state.requested_action = action
                player.state.last_action_state = state_vector
                player.state.last_action_choice = action

    def _apply_actions(self):
        """Apply requested actions and update states using state machines"""
        for player in [self.player_1, self.player_2]:
            # Process requested actions
            if hasattr(player.state, 'requested_action') and player.state.requested_action is not None:
                action = player.state.requested_action
                
                if player.is_action_off_cooldown(action):
                    # Use state machine to check if transition is allowed
                    if player.state_machine.can_transition(player.state.current_state, action):
                        # Get the new state from state machine
                        new_state = player.state_machine.get_next_state(player.state, player.state.current_state, action)
                        
                        # Enter the new state
                        player._enter_state(new_state)
                        player.state.last_action_frame = self.frame_counter
                        player.state.action_complete = False
                
                # Clear requested action
                delattr(player.state, 'requested_action')
            
    def _update_physics(self):
        """Update physics for all players"""
        for player_state in [self.player_1.state, self.player_2.state]:
            # Apply gravity to all players (whether jumping or falling)
            player_state.velocity_y += player_state.gravity
            player_state.x += player_state.velocity_x
            player_state.y += player_state.velocity_y
            
            # Boundary checking - account for player width (position is at center)
            half_width = player_state.width / 2
            player_state.x = max(half_width, min(self.state.arena_width - half_width, player_state.x))
            
            # Ground collision - account for player height (position is at center)
            half_height = player_state.height / 2
            if player_state.y + half_height > self.state.ground_level:
                player_state.y = self.state.ground_level - half_height
                player_state.velocity_y = 0
                player_state.is_grounded = True
            else:
                player_state.is_grounded = False
            
            # Apply friction/deceleration for horizontal movement
            if not player_state.current_state == State.ATTACK_ACTIVE and player_state.current_state not in [State.LEFT_ACTIVE, State.RIGHT_ACTIVE]:
                player_state.velocity_x *= player_state.friction
    
    def _handle_combat(self):
        """Handle combat interactions between players"""
        p1_attack_hitbox = self.player_1.get_attack_hitbox()
        p2_attack_hitbox = self.player_2.get_attack_hitbox()
        
        p1_hitbox = self.player_1.get_hitbox()
        p2_hitbox = self.player_2.get_hitbox()
        
        p1_hits_p2 = False
        p2_hits_p1 = False
                
        player1_state = self.player_1.state
        player2_state = self.player_2.state
        
        if p1_attack_hitbox:
            p1_hits_p2 = self._hitboxes_overlap(p1_attack_hitbox, p2_hitbox) and player1_state.current_attack_landed == False
        if p2_attack_hitbox:
            p2_hits_p1 = self._hitboxes_overlap(p2_attack_hitbox, p1_hitbox) and player2_state.current_attack_landed == False

        if p1_hits_p2 and p2_hits_p1:
            # Both players hit - both get stunned
            player1_state.stun_frames_remaining = player1_state.on_hit_stun
            player2_state.stun_frames_remaining = player2_state.on_hit_stun

            player1_state.got_stunned = True
            player2_state.got_stunned = True

            player1_state.health -= player2_state.attack_damage * (1 - player1_state.damage_reduction)
            player2_state.health -= player1_state.attack_damage * (1 - player2_state.damage_reduction)

            player1_state.current_attack_landed = True
            player2_state.current_attack_landed = True

        elif p1_hits_p2:
            # Player 1 hits Player 2
            if player2_state.current_state == State.BLOCK_ACTIVE:
                # Player 2 blocks the attack and stuns player 1 for block stun frames
                player1_state.stun_frames_remaining = player2_state.on_block_stun
                player1_state.got_stunned = True
                player1_state.current_attack_landed = True

                # Apply block damage reduction and base damage reduction
                player2_state.health -= player1_state.attack_damage * (1 - player2_state.block_efficiency) * (1 - player2_state.damage_reduction)
            else:
                # Player 2 does not block, so they take full damage and get stunned
                player2_state.stun_frames_remaining = player1_state.on_hit_stun
                player2_state.got_stunned = True
                player1_state.current_attack_landed = True

                # Player 2 takes damage equal to player 1's attack damage after their damage reduction is applied
                player2_state.health -= player1_state.attack_damage * (1 - player2_state.damage_reduction)
        elif p2_hits_p1:
            # Player 2 hits Player 1 and the same results occur but in reverse
            if player1_state.current_state == State.BLOCK_ACTIVE:
                player2_state.stun_frames_remaining = player1_state.on_block_stun
                player2_state.got_stunned = True
                player2_state.current_attack_landed = True

                player1_state.health -= player2_state.attack_damage * (1 - player1_state.block_efficiency) * (1 - player1_state.damage_reduction)
            else:
                player1_state.stun_frames_remaining = player2_state.on_hit_stun
                player1_state.got_stunned = True
                player2_state.current_attack_landed = True

                player1_state.health -= player2_state.attack_damage * (1 - player1_state.damage_reduction)

    def _hitboxes_overlap(self, box1: Tuple[float, float, float, float], 
                        box2: Tuple[float, float, float, float]) -> bool:
        """Check if two hitboxes overlap"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        return not (x2_1 < x1_2 or x2_2 < x1_1 or y2_1 < y1_2 or y2_2 < y1_1)

    def _update_frames(self):
        """Update frame counters and handle action state transitions"""
        if not hasattr(self, 'frame_counter'):
            self.frame_counter = 0
        self.frame_counter += 1
        
        for player in [self.player_1, self.player_2]:

            if player.state.attack_cooldown_remaining > 0:
                player.state.attack_cooldown_remaining -= 1
            
            if player.state.block_cooldown_remaining > 0:
                player.state.block_cooldown_remaining -= 1

            if player.state.jump_cooldown_remaining > 0:
                player.state.jump_cooldown_remaining -= 1
            
            if player.state.stun_frames_remaining > 0 and player.state.got_stunned == False:
                player.state.stun_frames_remaining -= 1

            previous_state = player.state.current_state
            # Check for automatic transitions (frame completion, physics events, combat events)
            player.update_state()

            # Reset the got stunned flag if the stun has been administered by the state machine
            if player.state.got_stunned and player.state.current_state == State.STUNNED:
                player.state.got_stunned = False
            if player.state.current_state == State.IDLE and previous_state != State.IDLE:
                player.state.action_complete = True
                player.state.current_attack_landed = False
            
            # Increment state frame counter
            player.state.state_frame_counter += 1


    def _check_game_over(self) -> None:
        """Check if game is over"""
        # Game ends if time is up or a player has 0 health
        if self.frame_counter >= self.state.max_frames:
            self.fight_over = True
            # Determine winner based on health
            p1_health = self.player_1.state.health
            p2_health = self.player_2.state.health
            if p1_health > p2_health:
                self.winner = 1
            elif p2_health > p1_health:
                self.winner = 2
            else:
               # Tiebreak condition is whichever player is closer to the centre
                p1_distance_from_center = abs(self.player_1.state.x - self.state.arena_width / 2)
                p2_distance_from_center = abs(self.player_2.state.x - self.state.arena_width / 2)
                if p1_distance_from_center < p2_distance_from_center:
                    self.winner = 1
                else:
                    self.winner = 2

        
        # Check for KO
        for player in [self.player_1.state, self.player_2.state]:
            player_id = player.player_id
            if player.health <= 0:
                self.game_over = True
                self.winner = 2 if player_id == 1 else 1

        
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
                player.state.last_action_choice is not None):
                
                player.total_reward += player.state.accumulated_reward

                if player.state.action_complete == True:
                    # Normalize reward by action duration (I think this should stop biases which occur based on action duration)
                    normalized_reward = player.state.accumulated_reward / (self.frame_counter - player.state.last_action_frame)
                    
                    current_state = player.state.last_action_state
                    next_state = self.state.get_state_vector(player.state.player_id)
                    
                    player.update(
                        current_state, 
                        player.state.last_action_choice.value, 
                        normalized_reward, 
                        next_state, 
                        self.fight_over
                    )
                    
                    # Reset for next action
                    player.state.last_action_state = None
                    player.state.last_action_choice = None
                    player.state.accumulated_reward = 0

    def _end_frame_checks(self):
        """Perform end-of-frame checks and cleanup"""
        
        self._validate_player_health()
        
        self._validate_player_positions()
            
        if self.is_recording:
            self._record_frame()
        
        if self.fight_over and self.is_recording:
            self._save_replay()

    def _validate_player_health(self):
        """Ensure player health values are within valid bounds"""
        for player in [self.player_1.state, self.player_2.state]:
            player.health = max(0.0, min(player.health, player.max_health))

    def _validate_player_positions(self):
        """Ensure players are within valid game boundaries"""
        for player in [self.player_1.state, self.player_2.state]:
            # Ground collision - account for player height
            half_height = player.height / 2
            if player.y + half_height > self.state.ground_level:
                player.y = self.state.ground_level - half_height
                player.velocity_y = 0
            
            # Horizontal boundaries - account for player width
            half_width = player.width / 2
            player.x = max(half_width, min(self.state.arena_width - half_width, player.x))
            
    def _initialize_recording(self):
        """Initialize the replay recorder"""
        self.replay_recorder = ReplayRecorder()
        self.replay_recorder.start_recording(self.state)

    def _record_frame(self):
        """Record the current frame's state"""
        # Initialize recorder on first frame if recording is enabled
        if self.is_recording and self.replay_recorder is None:
            self.replay_recorder = ReplayRecorder()
            self.replay_recorder.start_recording(self.state)
        
        # Record frame if recorder exists
        if self.replay_recorder is not None:
            self.replay_recorder.record_frame(self.state, self.frame_counter)

    def _save_replay(self):
        """Save the recorded replay to a file"""
        if self.replay_recorder is not None:
            self.replay_recorder.save_replay(self.winner)
            self.replay_recorder = None  # Clear recorder after saving