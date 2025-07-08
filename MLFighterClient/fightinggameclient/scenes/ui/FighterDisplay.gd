extends Control

# Node references
@onready var player_sprite = $MainContainer/FighterPanel/FighterMargin/SpriteCenter/Player
@onready var sprite_centre = $MainContainer/FighterPanel/FighterMargin/SpriteCenter
@onready var health_label = $MainContainer/StatsPanel/StatsMargin/StatsList/HealthStat/HealthLabel
@onready var health_bar = $MainContainer/StatsPanel/StatsMargin/StatsList/HealthStat/HealthBar
@onready var attack_label = $MainContainer/StatsPanel/StatsMargin/StatsList/AttackStat/AttackLabel
@onready var attack_bar = $MainContainer/StatsPanel/StatsMargin/StatsList/AttackStat/AttackBar
@onready var defense_label = $MainContainer/StatsPanel/StatsMargin/StatsList/DefenseStat/DefenseLabel
@onready var defense_bar = $MainContainer/StatsPanel/StatsMargin/StatsList/DefenseStat/DefenseBar
@onready var speed_label = $MainContainer/StatsPanel/StatsMargin/StatsList/SpeedStat/SpeedLabel
@onready var speed_bar = $MainContainer/StatsPanel/StatsMargin/StatsList/SpeedStat/SpeedBar
@onready var special_label = $MainContainer/StatsPanel/StatsMargin/StatsList/SpecialStat/SpecialLabel
@onready var special_bar = $MainContainer/StatsPanel/StatsMargin/StatsList/SpecialStat/SpecialBar

# Fighter data
var fighter_id: String = ""
var base_stats = {}
var current_stats = {}
var inventory = {}

# Animation variables
var entrance_animation_playing = false
var final_y_position: float
var fall_speed: float = 500.0
var fall_start_offset: float = -600.0
var min_scale: float = 4.0   # Minimum zoom when falling
var max_scale: float = 4.0   # Maximum zoom when landed
var base_scale: float = 4.0  # Normal display scale


func _ready():
	# Generate test stats
	StatManager.update_player_data(
		'aggressive', 
		{
			'weapons': [
				{
					'item_id': 'weapons_sword_steel_sword',  # Changed from 'id' to 'item_id'
					'equipped': true,
					'index': 0
				}
			],
			'armour': []
		}, 
		{'epsilon': 0.5, 'decay': 0.005, 'learning_rate': 0.002}
	)
	
	update_display_from_stats()
	
	update_display_from_stats()
	
	# Set initial scale
	if player_sprite:
		player_sprite.scale = Vector2(base_scale, base_scale)
	

	# Start entrance animation after a brief delay
	await get_tree().create_timer(0.1).timeout
	start_entrance_animation()
	
func start_entrance_animation():
	"""Start the player entrance animation with physics-based acceleration"""
	if not player_sprite:
		return
		
	entrance_animation_playing = true
	
	# Store the final position
	final_y_position = player_sprite.position.y
	
	# Move player above the container
	var fall_start_offset = -600.0
	player_sprite.position.y = final_y_position + fall_start_offset
	
	# Start with smaller scale (zoomed out)
	player_sprite.scale = Vector2(min_scale, min_scale)
	
	# Start falling animation
	player_sprite.play_animation_for_state("JUMP_FALLING")
	
	# Get gravity from current stats or use default
	var gravity = 1.0
	if StatManager.calculated_stats.has("gravity"):
		gravity = StatManager.calculated_stats.gravity
	
	# Create tween for falling motion and zoom
	var tween = create_tween()
	tween.set_parallel(true)
	tween.set_ease(Tween.EASE_IN)
	tween.set_trans(Tween.TRANS_QUART)
	
	# Calculate fall duration using physics and gravity
	var fall_distance = abs(fall_start_offset)
	var initial_velocity = 500.0 * gravity
	var final_velocity = 750.0 * gravity
	var avg_velocity = (initial_velocity + final_velocity) / 2.0
	var fall_duration = fall_distance / avg_velocity
	
	# Animate the fall
	tween.tween_property(player_sprite, "position:y", final_y_position, fall_duration)
	
	# Animate the zoom
	tween.tween_property(player_sprite, "scale", Vector2(max_scale, max_scale), fall_duration)
	
	# When fall completes, play landing sequence
	tween.chain().tween_callback(play_landing_sequence)

func play_landing_sequence():
	"""Play the landing recovery sequence"""
	if not player_sprite:
		return
	
	# Play landing recovery animation
	player_sprite.play_animation_for_state("JUMP_RECOVERY")
	
	# Wait for recovery animation to complete
	await get_tree().create_timer(0.7).timeout
	
	# Play idle animation
	player_sprite.play_animation_for_state("IDLE")
	
	entrance_animation_playing = false

func set_fighter_data(fighter_id: String, inventory: Dictionary, learning_parameters: Dictionary = {}):
	"""Set fighter and inventory data, then update display"""
	StatManager.update_player_data(fighter_id, inventory, learning_parameters)
	update_display_from_stats()

func update_display_from_stats():
	"""Update display using StatManager's calculated stats"""
	var stats = StatManager.get_current_stats()
	
	if stats.is_empty():
		# Use default values if no stats available
		update_display({
			"health": {"current": 0, "max": 100},
			"attack": {"current": 50, "max": 100},
			"defense": {"current": 30, "max": 100},
			"speed": {"current": 40, "max": 100},
			"gravity": {"current": 1.0, "max": 2.0}
		})
		return
	
	# Convert stats to display format
	var display_stats = {
		"health": {
			"current": stats.get("health", 100),
			"max": 200  # You can adjust max values as needed
		},
		"attack": {
			"current": stats.get("attack_damage", 50),
			"max": 100
		},
		"defense": {
			"current": stats.get("damage_reduction", 0),
			"max": 50
		},
		"speed": {
			"current": stats.get("move_speed", 40),
			"max": 100
		},
		"gravity": {
			"current": stats.get("gravity", 1.0),
			"max": 2.0
		}
	}
	
	update_display(display_stats)

func update_display(stats: Dictionary):
	"""Update all stat displays"""
	# Update health
	if stats.has("health"):
		var health = stats["health"]
		health_label.text = "Health: %d" % health["current"]
		health_bar.max_value = health["max"]
		health_bar.value = health["current"]
	
	# Update attack
	if stats.has("attack"):
		var attack = stats["attack"]
		attack_label.text = "Attack: %d" % attack["current"]
		attack_bar.max_value = attack["max"]
		attack_bar.value = attack["current"]
	
	# Update defense
	if stats.has("defense"):
		var defense = stats["defense"]
		defense_label.text = "Defense: %d" % defense["current"]
		defense_bar.max_value = defense["max"]
		defense_bar.value = defense["current"]
	
	# Update speed
	if stats.has("speed"):
		var speed = stats["speed"]
		speed_label.text = "Speed: %d" % speed["current"]
		speed_bar.max_value = speed["max"]
		speed_bar.value = speed["current"]
	
	# Update gravity (replace special stat)
	if stats.has("gravity"):
		var gravity = stats["gravity"]
		special_label.text = "Gravity: %.2f" % gravity["current"]
		special_bar.max_value = gravity["max"]
		special_bar.value = gravity["current"]
