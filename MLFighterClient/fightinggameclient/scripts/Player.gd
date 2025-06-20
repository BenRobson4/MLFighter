extends Node2D

@export var player_id: String = "player1"
@export var interpolation_speed: float = 10.0

# Visual components
@onready var sprite = $Sprite2D
@onready var health_bar = $HealthBar
@onready var animation_player = $AnimationPlayer

# State variables
var current_state: Dictionary = {}
var target_state: Dictionary = {}
var is_interpolating: bool = false

func _ready():
	# Initialize player visuals
	if player_id == "player2":
		sprite.flip_h = true
		position.x = 800  # Adjust based on your screen size

func _process(delta):
	if is_interpolating and target_state.size() > 0:
		interpolate_state(delta)

func update_state(new_state: Dictionary, instant: bool = false):
	"""Update player state from replay data"""
	target_state = new_state
	
	if instant:
		apply_state(new_state)
		current_state = new_state.duplicate()
	else:
		is_interpolating = true

func interpolate_state(delta: float):
	"""Smoothly interpolate between states"""
	if not current_state.has("x") or not target_state.has("x"):
		current_state = target_state.duplicate()
		return
	
	# Interpolate position
	var target_pos = Vector2(target_state.get("x", position.x), 
							 target_state.get("y", position.y))
	position = position.lerp(target_pos, interpolation_speed * delta)
	
	# Interpolate health
	if health_bar and target_state.has("health"):
		var current_health = current_state.get("health", 100)
		var target_health = target_state.get("health", 100)
		var interpolated_health = lerp(current_health, target_health, interpolation_speed * delta)
		health_bar.value = interpolated_health
		current_state["health"] = interpolated_health
	
	# Check if interpolation is complete
	if position.distance_to(target_pos) < 1.0:
		is_interpolating = false
		current_state = target_state.duplicate()

func apply_state(state: Dictionary):
	"""Immediately apply state without interpolation"""
	if state.has("x") and state.has("y"):
		position = Vector2(state["x"], state["y"])
	
	if health_bar and state.has("health"):
		health_bar.value = state["health"]
	
	# Apply other state properties
	if state.has("is_blocking"):
		play_animation("block" if state["is_blocking"] else "idle")

func play_animation(anim_name: String):
	"""Play animation based on action"""
	if animation_player and animation_player.has_animation(anim_name):
		animation_player.play(anim_name)

func perform_action(action_name: String):
	"""Trigger action animation"""
	match action_name:
		"PUNCH":
			play_animation("punch")
		"KICK":
			play_animation("kick")
		"BLOCK":
			play_animation("block")
		"SPECIAL":
			play_animation("special")
		"MOVE_LEFT":
			play_animation("walk")
			sprite.flip_h = true
		"MOVE_RIGHT":
			play_animation("walk")
			sprite.flip_h = false
		"JUMP":
			play_animation("jump")
		_:
			play_animation("idle")
