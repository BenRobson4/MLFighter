extends Node2D

@onready var sprite = $Sprite2D
@onready var animation_player = $AnimationPlayer
@onready var health_bar = $HealthBar

var player_config = null
var facing_right = true
var current_action = 5  # IDLE by default
var previous_position = Vector2.ZERO

# State enum to match your Python code
enum State {
	NONE = 0,
	STARTUP = 1,
	ACTIVE = 2,
	RECOVERY = 3,
	WAIT = 4
}

# Action enum to match your Python code
enum Action {
	LEFT = 0,
	RIGHT = 1,
	JUMP = 2,
	BLOCK = 3,
	ATTACK = 4,
	IDLE = 5
}

# Current states
var attack_state = State.NONE
var block_state = State.NONE
var jump_state = State.NONE
var is_stunned = false

func setup_from_config(config):
	player_config = config
	health_bar.max_value = 100 # Edit this later
	health_bar.value = 100

func update_from_frame_data(data):
	# Store previous position for movement detection
	previous_position = position
	
	# Update position
	position.x = data.x
	position.y = data.y
	
	# Update health
	health_bar.value = data.h
	
	# Update action
	current_action = data.a
	
	# Update direction
	if facing_right != data.fr:
		facing_right = data.fr
		scale.x = 1 if facing_right else -1
	
	# Unpack states from flags
	unpack_states(data.flags)
	
	# Play appropriate animation based on states
	play_animation_for_current_state()

func unpack_states(flags: int):
	"""Unpack state information from compressed flags integer"""
	# Extract attack_state (bits 0-2)
	attack_state = flags & 0x7
	
	# Extract block_state (bits 3-5)
	block_state = (flags >> 3) & 0x7
	
	# Extract jump_state (bits 6-8)
	jump_state = (flags >> 6) & 0x7
	
	# Extract is_stunned (bit 9)
	is_stunned = bool((flags >> 9) & 0x1)
func play_animation_for_current_state():
	"""Play animation based on current state priorities"""
	
	# Priority order: stunned > attack > block > jump > movement
	
	if is_stunned:
		play_if_different("stunned")
		return
	
	# Attack animations
	if attack_state != State.NONE:
		match attack_state:
			State.STARTUP:
				play_if_different("attack_startup")
			State.ACTIVE:
				play_if_different("attack_active")
			State.RECOVERY:
				play_if_different("attack_recovery")
			State.WAIT:
				play_if_different("attack_wait")
		return
	
	# Block animations
	if block_state != State.NONE:
		match block_state:
			State.STARTUP:
				play_if_different("block_startup")
			State.ACTIVE:
				play_if_different("block_active")
			State.RECOVERY:
				play_if_different("block_recovery")
			State.WAIT:
				play_if_different("block_wait")
		return
	
	# Jump animations
	if jump_state != State.NONE:
		match jump_state:
			State.STARTUP:
				play_if_different("jump_startup")
			State.ACTIVE:
				play_if_different("jump_active")
			State.WAIT:
				play_if_different("jump_wait")  # In-air waiting state
			State.RECOVERY:
				play_if_different("jump_recovery")  # Landing animation
		return
	
	# Movement and idle animations - FIXED HERE
	var is_moving = abs(position.x - previous_position.x) > 0.5
	
	if is_moving:
		play_if_different("run")
	else:
		play_if_different("idle")

func play_if_different(anim_name: String):
	"""Play animation only if it's different from current"""
	if not animation_player.has_animation(anim_name):
		push_warning("Animation not found: " + anim_name)
		# Fallback to idle if animation doesn't exist
		if animation_player.has_animation("idle"):
			anim_name = "idle"
		else:
			return
	
	if not animation_player.is_playing() or animation_player.current_animation != anim_name:
		animation_player.play(anim_name)

func get_state_name(state_value: int) -> String:
	"""Helper function to get state name for debugging"""
	match state_value:
		State.NONE:
			return "NONE"
		State.STARTUP:
			return "STARTUP"
		State.ACTIVE:
			return "ACTIVE"
		State.RECOVERY:
			return "RECOVERY"
		State.WAIT:
			return "WAIT"
		_:
			return "UNKNOWN"

func debug_print_states():
	"""Debug function to print current states"""
	print("Attack: ", get_state_name(attack_state), 
		  " Block: ", get_state_name(block_state),
		  " Jump: ", get_state_name(jump_state),
		  " Stunned: ", is_stunned)
