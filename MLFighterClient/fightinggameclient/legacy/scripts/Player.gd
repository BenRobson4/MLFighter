extends Node2D
class_name Player

@onready var sprite = $Sprite2D
@onready var animation_player = $AnimationPlayer

var current_state: String = ""
var max_health: float = 100.0
var current_health: float = 100.0  # Store health value

func _ready():
	pass  # No health bar initialization needed

func update_player_data(player_data: Dictionary):
	# Update position
	position.x = player_data.x
	position.y = player_data.y
	
	# Store health value
	current_health = player_data.health
	
	# Update sprite direction
	if player_data.facing_right:
		sprite.scale.x = abs(sprite.scale.x)  # Face right
	else:
		sprite.scale.x = -abs(sprite.scale.x)  # Face left
	
	# Update animation based on state
	var new_state = player_data.current_state
	if new_state != current_state:
		current_state = new_state
		play_animation_for_state(new_state)

func play_animation_for_state(state: String):
	var animation_name = map_state_to_animation(state)
	
	if animation_player.has_animation(animation_name):
		animation_player.play(animation_name)
	else:
		# Fallback to idle if animation doesn't exist
		if animation_player.has_animation("idle"):
			animation_player.play("idle")
		else:
			print("Warning: No animation found for state: ", state)

func map_state_to_animation(state: String) -> String:
	# State to animation mapping
	var state_map = {
		"LEFT_STARTUP": "run_startup",
		"RIGHT_STARTUP": "run_startup",
		"LEFT_ACTIVE": "run_active",
		"RIGHT_ACTIVE": "run_active",
		"LEFT_RECOVERY": "run_recovery",
		"RIGHT_RECOVERY": "run_recovery",
		"IDLE": "idle",
		"ATTACK_STARTUP": "attack_startup",
		"ATTACK_ACTIVE": "attack_active",
		"ATTACK_RECOVERY": "attack_recovery",
		"BLOCK_STARTUP": "block_startup",
		"BLOCK_ACTIVE": "block_active",
		"BLOCK_RECOVERY": "block_recovery",
		"JUMP_STARTUP": "jump_startup",
		"JUMP_ACTIVE": "jump_active",
		"JUMP_RISING": "jump_rising",
		"JUMP_FALLING": "jump_falling",
		"JUMP_RECOVERY": "jump_recovery",
		"STUNNED": "stunned"
	}
	
	return state_map.get(state, state.to_lower())
