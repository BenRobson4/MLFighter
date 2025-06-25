from ..data_classes import PlayerState
from ..globals.actions import Action
from ..globals.states import State

class StateMachine:
    def __init__(self, player_state: PlayerState):
        """Initialize with frame data configuration only"""
        self.frame_data = player_state.frame_data
        self.transitions = self._setup_transitions()
    
    def _setup_transitions(self) -> dict:
        """Set up state transitions"""
        transitions = {}
        
        # Attack sequence
        transitions[(State.ATTACK_STARTUP, 'frame_complete')] = State.ATTACK_ACTIVE
        transitions[(State.ATTACK_ACTIVE, 'frame_complete')] = State.ATTACK_RECOVERY
        transitions[(State.ATTACK_RECOVERY, 'frame_complete')] = State.IDLE
        
        # Block sequence
        transitions[(State.BLOCK_STARTUP, 'frame_complete')] = State.BLOCK_ACTIVE
        transitions[(State.BLOCK_ACTIVE, 'frame_complete')] = State.BLOCK_RECOVERY
        transitions[(State.BLOCK_RECOVERY, 'frame_complete')] = State.IDLE
        
        # Jump sequence
        transitions[(State.JUMP_STARTUP, 'frame_complete')] = State.JUMP_ACTIVE
        transitions[(State.JUMP_ACTIVE, 'frame_complete')] = State.JUMP_RISING
        transitions[(State.JUMP_RISING, 'peak_reached')] = State.JUMP_FALLING
        transitions[(State.JUMP_FALLING, 'landed')] = State.JUMP_RECOVERY
        transitions[(State.JUMP_RECOVERY, 'frame_complete')] = State.IDLE

        # Movement sequence
        transitions[(State.LEFT_STARTUP, 'frame_complete')] = State.LEFT_ACTIVE
        transitions[(State.LEFT_ACTIVE, 'frame_complete')] = State.LEFT_RECOVERY
        transitions[(State.LEFT_RECOVERY, 'frame_complete')] = State.IDLE

        transitions[(State.RIGHT_STARTUP, 'frame_complete')] = State.RIGHT_ACTIVE
        transitions[(State.RIGHT_ACTIVE, 'frame_complete')] = State.RIGHT_RECOVERY
        transitions[(State.RIGHT_RECOVERY, 'frame_complete')] = State.IDLE

        # Stun cases
        for state in [
            State.IDLE,
            State.LEFT_STARTUP,
            State.LEFT_ACTIVE,
            State.LEFT_RECOVERY,
            State.RIGHT_STARTUP,
            State.RIGHT_ACTIVE,
            State.RIGHT_RECOVERY,
            State.ATTACK_STARTUP,
            State.ATTACK_ACTIVE,
            State.ATTACK_RECOVERY,
            State.BLOCK_STARTUP,
            State.BLOCK_RECOVERY,
            State.JUMP_STARTUP,
            State.JUMP_RISING,
            State.JUMP_FALLING,
            State.JUMP_RECOVERY
            ]:
            transitions[(state, 'stunned')] = State.STUNNED
        transitions[(State.STUNNED, 'stun_over')] = State.IDLE
        
        # Input-based transitions
        transitions[(State.IDLE, Action.LEFT)] = State.LEFT_STARTUP
        transitions[(State.IDLE, Action.RIGHT)] = State.RIGHT_STARTUP
        transitions[(State.IDLE, Action.ATTACK)] = State.ATTACK_STARTUP
        transitions[(State.IDLE, Action.BLOCK)] = State.BLOCK_STARTUP
        transitions[(State.IDLE, Action.JUMP)] = State.JUMP_STARTUP
        
        return transitions
    
    def get_state_duration(self, state: State) -> int:
        """Get duration for a specific state based on frame data"""
        if state == State.LEFT_STARTUP:
            return self.frame_data[Action.LEFT][0]
        elif state == State.LEFT_ACTIVE:
            return self.frame_data[Action.LEFT][1]
        elif state == State.LEFT_RECOVERY:
            return self.frame_data[Action.LEFT][2]
        elif state == State.RIGHT_STARTUP:
            return self.frame_data[Action.RIGHT][0]
        elif state == State.RIGHT_ACTIVE:
            return self.frame_data[Action.RIGHT][1]
        elif state == State.RIGHT_RECOVERY:
            return self.frame_data[Action.RIGHT][2]
        elif state == State.ATTACK_STARTUP:
            return self.frame_data[Action.ATTACK][0]
        elif state == State.ATTACK_ACTIVE:
            return self.frame_data[Action.ATTACK][1]
        elif state == State.ATTACK_RECOVERY:
            return self.frame_data[Action.ATTACK][2]
        elif state == State.BLOCK_STARTUP:
            return self.frame_data[Action.BLOCK][0]
        elif state == State.BLOCK_ACTIVE:
            return self.frame_data[Action.BLOCK][1]   
        elif state == State.BLOCK_RECOVERY:
            return self.frame_data[Action.BLOCK][2]
        elif state == State.JUMP_STARTUP:
            return self.frame_data[Action.JUMP][0]
        elif state == State.JUMP_ACTIVE:
            return self.frame_data[Action.JUMP][1]
        elif state == State.JUMP_RECOVERY:
            return self.frame_data[Action.JUMP][2]
        return 0
    
    def can_transition(self, current_state: State, action) -> bool: # action is either an Action or a string event
        """Check if a transition is allowed"""
        return (current_state, action) in self.transitions
    
    def get_next_state(self, current_state: State, event) -> State:
        """Get the next state based on current state and event"""
        if (current_state, event) in self.transitions:
            return self.transitions[(current_state, event)]
        return current_state
    
    def should_auto_transition(self, player_state: PlayerState) -> tuple[bool, str]:
        """Check if an automatic transition should occur based on player state"""
        duration = self.get_state_duration(player_state.current_state)
        
        # Check frame-based transitions
        if duration >= 0 and player_state.state_frame_counter >= duration:
            return True, 'frame_complete'
        
        # Check physics-based transitions
        if player_state.current_state == State.JUMP_RISING and player_state.velocity_y >= 0:
            return True, 'peak_reached'
        elif player_state.current_state == State.JUMP_FALLING and player_state.is_grounded:
            return True, 'landed'
        
        if player_state.got_stunned and player_state.current_state != State.STUNNED:
            return True, 'stunned'
        elif player_state.current_state == State.STUNNED and player_state.stun_frames_remaining <= 0:
            return True, 'stun_over'
        
        return False, None
    
    def get_state_effects(self, new_state: State) -> dict:
        """Get the effects that should be applied when entering a state"""
        effects = {}
        
        if new_state == State.LEFT_ACTIVE:
            effects['velocity_x'] = 'negative_move_speed'
            effects['facing_right'] = False
        elif new_state == State.RIGHT_ACTIVE:
            effects['velocity_x'] = 'positive_move_speed'
            effects['facing_right'] = True
        elif new_state == State.JUMP_ACTIVE:
            effects['velocity_y'] = 'negative_jump_force'
        elif new_state == State.IDLE:
            effects['velocity_x'] = 0
        
        return effects