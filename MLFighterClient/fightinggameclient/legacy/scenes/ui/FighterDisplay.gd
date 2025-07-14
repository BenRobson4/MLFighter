extends Control

# Node references
@onready var player_sprite = $MainContainer/FighterPanel/FighterMargin/SpriteCenter/Player
@onready var sprite_centre = $MainContainer/FighterPanel/FighterMargin/SpriteCenter
@onready var stats_container = $MainContainer/StatsPanel/StatsMargin/VBoxContainer/StatsList
@onready var combat_stats_button = $MainContainer/StatsPanel/StatsMargin/VBoxContainer/MarginContainer/HBoxContainer/CombatStatsButton
@onready var movement_stats_button = $MainContainer/StatsPanel/StatsMargin/VBoxContainer/MarginContainer/HBoxContainer/MovementStatsButton
@onready var learning_stats_button = $MainContainer/StatsPanel/StatsMargin/VBoxContainer/MarginContainer/HBoxContainer/LearningStatsButton

# Animation variables
var entrance_animation_playing = false
var final_y_position: float
var min_scale: float = 4.0   # Minimum zoom when falling
var max_scale: float = 4.0   # Maximum zoom when landed
var base_scale: float = 4.0  # Normal display scale

# UI tracking
var stat_ui_elements: Array[Control] = []
var current_display: String = "combat" # "movement" and "learning" are the other options

# Preview state
var is_previewing: bool = false
var preview_stats: Dictionary = {}
var preview_progress_bars: Array[ProgressBar] = []

func _ready():
	# Connect to FighterDataStore signals
	FighterDataStore.data_updated.connect(_on_fighter_data_updated)
	FighterDataStore.inventory_changed.connect(_on_fighter_inventory_changed)
	FighterDataStore.stats_changed.connect(_on_fighter_stats_changed)
	
	# Add to group for easy access by other systems
	add_to_group("fighter_display")
	
	# Connect stat display buttons
	combat_stats_button.pressed.connect(_on_combat_stats_button_pressed)
	movement_stats_button.pressed.connect(_on_movement_stats_button_pressed)
	learning_stats_button.pressed.connect(_on_learning_stats_button_pressed)
	
	# Set initial scale
	if player_sprite:
		player_sprite.scale = Vector2(base_scale, base_scale)
	
	# Initial display update
	update_display_from_stats()
	
	# Connect to shop item hover signals if shop exists
	_connect_to_shop_signals()

	# Start entrance animation after a brief delay
	await get_tree().create_timer(0.1).timeout
	start_entrance_animation()

func _connect_to_shop_signals():
	"""Connect to shop item hover signals"""
	await get_tree().process_frame
	
	# Find all ItemSlot nodes in the scene
	var item_slots = get_tree().get_nodes_in_group("item_slots")
	for slot in item_slots:
		_connect_item_slot(slot)

func _connect_item_slot(slot: Control):
	"""Connect to an individual item slot's signals"""
	if not slot.is_connected("mouse_entered", _on_item_slot_hover_started):
		slot.mouse_entered.connect(_on_item_slot_hover_started.bind(slot))
	if not slot.is_connected("mouse_exited", _on_item_slot_hover_ended):
		slot.mouse_exited.connect(_on_item_slot_hover_ended.bind(slot))

func _on_item_slot_hover_started(slot: Control):
	"""Handle item slot hover start"""
	if "item_data" in slot:
		preview_item(slot.item_data)

func _on_item_slot_hover_ended(slot: Control):
	"""Handle item slot hover end"""
	clear_preview()

func preview_item(item_data: Dictionary):
	"""Preview stats with the given item"""
	if item_data.is_empty() or not item_data.has("item_id"):
		return
	
	var item_id = item_data.get("item_id", "")
	var category = item_data.get("category", "")
	
	# Parse category from item_id if not provided
	if category.is_empty():
		var parts = item_id.split("_")
		if parts.size() > 0:
			category = parts[0]
			# Handle compound categories
			if parts.size() > 1 and parts[1] == "modifiers":
				category = parts[0] + "_" + parts[1]
	
	# Determine item type for StatManager
	var item_type = ""
	if category == "weapons":
		item_type = "weapon"
	elif category == "armour":
		item_type = "armour"
	elif category == "learning_modifiers" or (category == "learning" and "modifiers" in item_id):
		item_type = "learning_modifier"
	elif category == "reward_modifiers" or (category == "reward" and "modifiers" in item_id):
		# Reward modifiers don't affect displayed stats
		return
	elif category == "features":
		# Features might need special handling
		return
	else:
		print("Unknown item category: ", category)
		return
	
	# Get preview stats from StatManager
	preview_stats = StatManager.preview_item_stats(item_id, item_type)
	is_previewing = true
	
	# Update display with preview
	_update_preview_display()

func clear_preview():
	"""Clear the preview and return to normal display"""
	is_previewing = false
	preview_stats.clear()
	
	# Remove preview progress bars
	for bar in preview_progress_bars:
		if is_instance_valid(bar):
			bar.queue_free()
	preview_progress_bars.clear()
	
	# Restore normal display
	update_display_from_stats()

func _update_preview_display():
	"""Update the display to show preview stats"""
	if not is_previewing or preview_stats.is_empty():
		return
	
	var current_stats_dict = _get_current_fighter_stats()
	var display_stats = _get_display_stats(preview_stats)
	var current_display_stats = _get_display_stats(current_stats_dict)
	
	# Update each stat with preview
	var stat_index = 0
	for stat_container in stat_ui_elements:
		if not is_instance_valid(stat_container):
			continue
			
		var stat_name = display_stats.keys()[stat_index] if stat_index < display_stats.size() else ""
		if stat_name.is_empty():
			continue
		
		var preview_data = display_stats[stat_name]
		var current_data = current_display_stats.get(stat_name, {"current": 0, "max": 100})
		
		# Find the progress bar in this container
		var progress_bar: ProgressBar = null
		for child in stat_container.get_children():
			if child is ProgressBar:
				progress_bar = child
				break
		
		if progress_bar:
			# Create preview overlay bar
			var preview_bar = _create_preview_bar(progress_bar, preview_data, current_data)
			if preview_bar:
				stat_container.add_child(preview_bar)
				preview_progress_bars.append(preview_bar)
		
		# Update value label to show comparison
		var header_container = stat_container.get_child(0) if stat_container.get_child_count() > 0 else null
		if header_container and header_container is HBoxContainer:
			var value_label = header_container.get_child(1) if header_container.get_child_count() > 1 else null
			if value_label and value_label is Label:
				_update_preview_label(value_label, current_data.current, preview_data.current, preview_data.max)
		
		stat_index += 1

func _create_preview_bar(original_bar: ProgressBar, preview_data: Dictionary, current_data: Dictionary) -> ProgressBar:
	"""Create a preview progress bar overlay"""
	var preview_value = preview_data.get("current", 0)
	var current_value = current_data.get("current", 0)
	var max_value = preview_data.get("max", 100)
	
	# Don't create preview if values are the same
	if abs(preview_value - current_value) < 0.01:
		return null
	
	var preview_bar = ProgressBar.new()
	preview_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	preview_bar.custom_minimum_size = original_bar.custom_minimum_size
	preview_bar.max_value = max_value
	preview_bar.value = preview_value
	
	# Position it exactly over the original
	preview_bar.position = original_bar.position
	preview_bar.size = original_bar.size
	
	# Style based on increase/decrease
	if preview_value > current_value:
		# Increase - green translucent
		preview_bar.modulate = Color(0.3, 1.0, 0.3, 0.6)
	else:
		# Decrease - red translucent
		preview_bar.modulate = Color(1.0, 0.3, 0.3, 0.6)
	
	# Copy the original bar's style
	preview_bar.show_percentage = false
	
	return preview_bar

func _update_preview_label(label: Label, current_value: float, preview_value: float, max_value: float):
	"""Update value label to show preview comparison"""
	if preview_value == -1:
		label.text = "N/A"
		label.add_theme_color_override("font_color", Color.GRAY)
		return
	
	var current_str = _format_value(current_value)
	var preview_str = _format_value(preview_value)
	var max_str = _format_value(max_value)
	
	if abs(preview_value - current_value) < 0.01:
		# No change
		label.text = "%s / %s" % [current_str, max_str]
		label.add_theme_color_override("font_color", Color.YELLOW)
	else:
		# Show change
		var diff = preview_value - current_value
		var diff_str = _format_value(abs(diff))
		var arrow = "↑" if diff > 0 else "↓"
		var color = Color.GREEN if diff > 0 else Color.RED
		
		label.text = "%s %s %s" % [preview_str, arrow, diff_str]
		label.add_theme_color_override("font_color", color)

func _get_current_fighter_stats() -> Dictionary:
	"""Get current fighter stats from FighterDataStore"""
	var fighter_data = FighterDataStore.get_active_fighter_data()
	if fighter_data.has("calculated_stats"):
		return fighter_data["calculated_stats"]
	
	# Fallback to StatManager if calculated stats not in store
	return StatManager.get_current_stats()

func _get_display_stats(stats: Dictionary) -> Dictionary:
	"""Convert stats to display format based on current display mode"""
	var display_stats = {}
	
	if current_display == "combat":
		display_stats = {
			"health": {
				"current": stats.get("health", -1),
				"max": 200
			},
			"attack": {
				"current": stats.get("attack_damage", -1),
				"max": 100
			},
			"defense": {
				"current": stats.get("damage_reduction", -1),
				"max": 50
			},
			"block efficiency": {
				"current": stats.get("block_efficiency", -1),
				"max": 1
			},
			"attack cooldown": {
				"current": stats.get("attack_cooldown", -1),
				"max": 50
			},
			"block cooldown": {
				"current": stats.get("block_cooldown", -1),
				"max": 50
			},
			"x attack range": {
				"current": stats.get("x_attack_range", -1),
				"max": 500
			},
			"y attack range": {
				"current": stats.get("y_attack_range", -1),
				"max": 400
			}
		}
	elif current_display == "movement":
		display_stats = {
			"move speed": {
				"current": stats.get("move_speed", -1),
				"max": 20
			},
			"jump force": {
				"current": stats.get("jump_force", -1),
				"max": 20
			},
			"jump cooldown": {
				"current": stats.get("jump_cooldown", -1),
				"max": 50
			},
			"gravity": {
				"current": stats.get("gravity", -1),
				"max": 20
			},
			"friction": {
				"current": stats.get("friction", -1),
				"max": 1
			}
		}
	else:
		var learning_params = stats.get("learning_parameters", {})
		display_stats = {
			"epsilon": {
				"current": learning_params.get("epsilon", -1),
				"max": 1
			},
			"decay": {
				"current": learning_params.get("decay", -1),
				"max": 0.1
			},
			"learning rate": {
				"current": learning_params.get("learning_rate", -1),
				"max": 0.1
			}
		}
	
	return display_stats

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
	var stats = _get_current_fighter_stats()
	var gravity = stats.get("gravity", 1.0)
	
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

# Signal handlers for FighterDataStore
func _on_fighter_data_updated(fighter_id: String):
	"""Handle fighter data updates"""
	if fighter_id == FighterDataStore.active_fighter_id:
		update_display_from_stats()

func _on_fighter_inventory_changed(fighter_id: String):
	"""Handle inventory changes"""
	if fighter_id == FighterDataStore.active_fighter_id:
		update_display_from_stats()

func _on_fighter_stats_changed(fighter_id: String):
	"""Handle stats changes"""
	if fighter_id == FighterDataStore.active_fighter_id:
		update_display_from_stats()

# Button handlers
func _on_combat_stats_button_pressed():
	current_display = "combat"
	if is_previewing:
		_update_preview_display()
	else:
		update_display_from_stats()
	
func _on_movement_stats_button_pressed():
	current_display = "movement"
	if is_previewing:
		_update_preview_display()
	else:
		update_display_from_stats()

func _on_learning_stats_button_pressed():
	current_display = "learning"
	if is_previewing:
		_update_preview_display()
	else:
		update_display_from_stats()

func update_display_from_stats():
	"""Update display using fighter stats from FighterDataStore"""
	var stats = _get_current_fighter_stats()
	
	if stats.is_empty():
		# Use default values if no stats available
		update_display({
			"health": {"current": 100, "max": 100},
			"attack": {"current": 50, "max": 100},
			"defense": {"current": 30, "max": 100},
			"speed": {"current": 40, "max": 100},
			"gravity": {"current": 1.0, "max": 2.0}
		})
		return
	
	var display_stats = _get_display_stats(stats)
	update_display(display_stats)

func update_display(stats: Dictionary):
	"""Update all stat displays"""
	# Clear existing UI elements
	_clear_stat_ui()
	
	# Create UI elements for each stat
	for stat_name in stats.keys():
		var stat_data = stats[stat_name]
		var current_value = stat_data.get("current", 0)
		var max_value = stat_data.get("max", 100)
		
		# Create container for this stat
		var stat_container = VBoxContainer.new()
		stat_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		
		# Create header with stat name and values
		var header_container = HBoxContainer.new()
		header_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		
		# Stat name label
		var name_label = Label.new()
		name_label.text = stat_name.capitalize()
		name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		name_label.add_theme_color_override("font_color", Color.WHITE)
		
		# Value label
		var value_label = Label.new()
		if current_value == -1:
			value_label.text = "N/A"
			value_label.add_theme_color_override("font_color", Color.GRAY)
		else:
			value_label.text = "%s / %s" % [_format_value(current_value), _format_value(max_value)]
			value_label.add_theme_color_override("font_color", Color.YELLOW)
		
		value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		
		# Add labels to header
		header_container.add_child(name_label)
		header_container.add_child(value_label)
		
		# Create progress bar
		var progress_bar = ProgressBar.new()
		progress_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		progress_bar.custom_minimum_size.y = 8
		progress_bar.max_value = max_value
		
		if current_value == -1:
			progress_bar.value = 0
			progress_bar.modulate = Color.GRAY
		else:
			progress_bar.value = current_value
			progress_bar.modulate = Color.WHITE
		
		# Style the progress bar
		_style_progress_bar(progress_bar, stat_name)
		
		# Add elements to stat container
		stat_container.add_child(header_container)
		stat_container.add_child(progress_bar)
		
		# Add some spacing
		var spacer = Control.new()
		spacer.custom_minimum_size.y = 5
		stat_container.add_child(spacer)
		
		# Add to stats container
		stats_container.add_child(stat_container)
		
		# Track for cleanup
		stat_ui_elements.append(stat_container)

func _clear_stat_ui():
	"""Clear all existing stat UI elements"""
	for element in stat_ui_elements:
		if is_instance_valid(element):
			element.queue_free()
	stat_ui_elements.clear()
	
	# Also clear preview bars
	for bar in preview_progress_bars:
		if is_instance_valid(bar):
			bar.queue_free()
	preview_progress_bars.clear()

func _format_value(value) -> String:
	"""Format numeric values for display"""
	if typeof(value) == TYPE_FLOAT:
		if value < 0.01:
			return "%.4f" % value
		elif value < 0.1:
			return "%.3f" % value
		elif value < 1.0:
			return "%.2f" % value
		else:
			return "%.1f" % value
	else:
		return str(value)

func _style_progress_bar(progress_bar: ProgressBar, stat_name: String):
	"""Apply styling to progress bars based on stat type"""
	match stat_name:
		"health":
			progress_bar.modulate = Color.RED
		"attack", "attack damage":
			progress_bar.modulate = Color.ORANGE_RED
		"defense", "damage reduction":
			progress_bar.modulate = Color.BLUE
		"speed", "move speed":
			progress_bar.modulate = Color.GREEN
		"epsilon", "decay", "learning rate":
			progress_bar.modulate = Color.PURPLE
		_:
			progress_bar.modulate = Color.WHITE
