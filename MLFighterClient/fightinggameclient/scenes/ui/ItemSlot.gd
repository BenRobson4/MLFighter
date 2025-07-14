extends Control
class_name ItemSlot

signal item_clicked(item_data: Dictionary)
signal item_right_clicked(item_data: Dictionary)

# Add an enum for visual/behavior modes
enum SlotMode {
	INVENTORY,  # Used in fighter inventory
	SHOP        # Used in shop
}

@export var slot_mode: SlotMode = SlotMode.INVENTORY

@onready var item_background = $ItemBackground
@onready var item_sprite = $ItemSprite
@onready var item_border = $ItemBorder
@onready var item_button = $ItemButton
@onready var tooltip_container = $TooltipContainer
@onready var item_name_label = $TooltipContainer/TooltipContent/ItemName
@onready var item_description_label = $TooltipContainer/TooltipContent/ItemDescription
@onready var stats_container = $TooltipContainer/TooltipContent/StatsContainer
@onready var clipping_container = $TooltipContainer/ClippingContainer

# Border textures
@export var default_border: Texture2D
@export var hover_border: Texture2D  
@export var selected_border: Texture2D  

# Define stats to display for each category
const CATEGORY_DISPLAY_STATS = {
	"weapons": [
		"attack_damage_modifier", "attack_cooldown_modifier", 
		"move_speed_modifier", "jump_force_modifier",
		"gravity_modifier", "x_attack_range_modifier", "y_attack_range_modifier",
		"rarity", "cost", "stock"
	],
	"armour": [
		"health_modifier", "damage_received_modifier",
		"move_speed_modifier", "jump_force_modifier", 
		"gravity_modifier", "rarity", "cost", "stock"
	],
	"reward_modifiers": [
		"delta", "tier", "cost", "stock"
	],
	"learning_modifiers": [
		"delta", "tier", "cost", "stock"
	],
	"features": [
		"category", "cost", "stock"
	]
}

# Human-readable stat labels
const STAT_LABELS = {
	# Combat stats
	"attack_damage_modifier": "Damage",
	"attack_cooldown_modifier": "Attack CD", 
	"x_attack_range_modifier": "X-Range",
	"y_attack_range_modifier": "Y-Range",
	
	# Movement stats
	"move_speed_modifier": "Speed",
	"jump_force_modifier": "Jump Power",
	"gravity_modifier": "Gravity",
	
	# Defense stats
	"health_modifier": "Health",
	"damage_received_modifier": "Damage Reduction",
	
	# Modifier stats
	"delta": "Effect",
	"tier": "Tier",
	
	# General stats
	"cost": "Cost",
	"stock": "Stock",
	"rarity": "Rarity",
	"category": "Type"
}

# Define which stats should show positive/negative indicators
const SIGNED_STATS = [
	"attack_damage_modifier", "attack_cooldown_modifier",
	"move_speed_modifier", "jump_force_modifier",
	"x_attack_range_modifier", "y_attack_range_modifier",
	"health_modifier", "damage_received_modifier",
	"delta"
]

var item_data: Dictionary = {}
var is_empty: bool = true
var is_selected: bool = false
var is_hovered: bool = false
var stat_rows: Array[Control] = []
var stat_counter: int = 0

# Cache for loaded item data
static var items_cache: Dictionary = {}


func _ready():
	# Connect signals
	item_button.mouse_entered.connect(_on_mouse_entered)
	item_button.mouse_exited.connect(_on_mouse_exited)
	item_button.pressed.connect(_on_item_clicked)
	
	# Add right-click handling
	item_button.gui_input.connect(_on_button_input)
	
	# Initialize empty state
	clear_slot()
	
func _process(_delta):
	# Update border based on state
	if is_selected and slot_mode == SlotMode.INVENTORY:
		item_border.texture = selected_border
	elif is_hovered:
		item_border.texture = hover_border
	else:
		item_border.texture = default_border
	
	# Show/hide tooltip based on hover state
	tooltip_container.visible = is_hovered and not is_empty

func set_item(data: Dictionary):
	"""Set item data and update display"""
	item_data = data
	is_empty = false
	
	# Load item info from files if we have an item_id
	var item_id = data.get("item_id", "")
	if not item_id.is_empty():
		var loaded_data = load_item_data(item_id)
		# Merge loaded data with provided data (provided data takes precedence)
		for key in loaded_data:
			if not item_data.has(key):
				item_data[key] = loaded_data[key]
	
	# Load and set item sprite
	var item_texture = load_item_texture(item_data.get("item_id", ""))
	if item_texture:
		item_sprite.texture = item_texture
		item_sprite.visible = true
	else:
		item_sprite.visible = false
	
	# Update tooltip content
	_update_tooltip_content()
	
	# Show background
	item_background.visible = true
	item_background.modulate = Color.WHITE

func clear_slot():
	"""Clear the slot"""
	item_data = {}
	is_empty = true
	is_selected = false
	is_hovered = false
	
	# Hide sprite
	item_sprite.visible = false
	
	# Reset border
	if default_border:
		item_border.texture = default_border
	item_border.modulate = Color(0.5, 0.5, 0.5, 0.5)  # Dim gray for empty slots
	
	# Hide tooltip
	tooltip_container.visible = false
	
	# Dim background
	item_background.visible = true
	item_background.modulate = Color(0.7, 0.7, 0.7)
	
	# Clear stat rows
	_clear_stat_rows()

func _update_tooltip_content():
	"""Update tooltip with item data"""
	if is_empty or item_data.is_empty():
		return
	
	# Set item name with bold formatting
	var item_name = item_data.get("name", "Unknown Item")
	item_name_label.text = "[b]%s[/b]" % item_name
	
	# Set description if available
	var description = item_data.get("description", "")
	item_description_label.text = description
	item_description_label.add_theme_font_size_override("normal_font_size", 18)
	item_description_label.visible = not description.is_empty()
	
	# Update stats
	_update_stats_section()
	
	# Position tooltip above the item slot
	_position_tooltip()

func _update_stats_section():
	"""Update stats section based on item category"""
	# Clear existing stat rows
	_clear_stat_rows()
	stat_counter = 0
	
	# Get the category-specific stats to display
	var category = item_data.get("category", "")
	var stats_to_display = CATEGORY_DISPLAY_STATS.get(category, [])
	
	# If no specific stats defined, show all non-empty stats
	if stats_to_display.is_empty():
		stats_to_display = item_data.keys()
	
	# Add rows for relevant stats
	for stat_key in stats_to_display:
		if not item_data.has(stat_key):
			continue
			
		var value = item_data[stat_key]
		var should_show = _should_show_stat(stat_key, value)
		
		if should_show:
			_add_stat_row(stat_key, value)
			stat_counter += 1

func _should_show_stat(stat_key: String, value) -> bool:
	"""Determine if a stat should be shown"""
	# Special handling for gravity_modifier
	if stat_key == "gravity_modifier":
		return value != 1.0
	
	# Check if value is non-default
	match typeof(value):
		TYPE_INT, TYPE_FLOAT:
			# Special case for stock - show if >= 0
			if stat_key == "stock":
				return value >= 0
			return value != 0
		TYPE_STRING:
			return value != "" and value != "0"
		_:
			return value != null

func _add_stat_row(stat_key: String, value):
	"""Add a stat row to the stats container"""
	# Create row container
	var row = HBoxContainer.new()
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	
	var row_size = 25 if stat_counter == 2 else 26
	row.custom_minimum_size = Vector2(0, row_size)
	var spacer = VSeparator.new()
	
	# Create spacer to align stats with the bullet points
	var spacing = _calculate_spacing(stat_counter)
	spacer.custom_minimum_size = Vector2(spacing, 0)
	spacer.modulate = Color(0, 0, 0, 0)
	row.add_child(spacer)
	
	# Create stat label
	var label = Label.new()
	label.text = STAT_LABELS.get(stat_key, stat_key.capitalize().replace("_", " ")) + ":"
	label.add_theme_color_override("font_color", Color.BLACK)
	label.add_theme_font_size_override("font_size", 18)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	
	# Create value label
	var value_label = Label.new()
	value_label.text = _format_stat_value(stat_key, value)
	value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	
	# Apply color styling
	_apply_stat_color(value_label, stat_key, value)
	
	# Add labels to row
	row.add_child(label)
	row.add_child(value_label)
	
	# Add row to container
	stats_container.add_child(row)
	
	# Track for cleanup
	stat_rows.append(row)

func _format_stat_value(stat_key: String, value) -> String:
	"""Format the stat value for display"""
	var formatted = str(value)
	
	# Add + prefix for positive values on signed stats
	if stat_key in SIGNED_STATS and typeof(value) in [TYPE_INT, TYPE_FLOAT]:
		if value > 0:
			formatted = "+" + formatted
	
	# Special formatting for specific stats
	match stat_key:
		"tier":
			formatted = "Tier " + formatted
		"rarity":
			formatted = formatted.capitalize()
		"cost":
			formatted = formatted + "g"
		"delta":
			# For modifiers, show the effect direction
			if typeof(value) in [TYPE_INT, TYPE_FLOAT]:
				if value > 0:
					formatted = "+" + formatted
	
	return formatted

func _apply_stat_color(label: Label, stat_key: String, value):
	"""Apply color to stat value based on type and value"""
	var color = Color.BLACK
	
	# Category-based coloring
	var category = item_data.get("category", "")
	
	match stat_key:
		"cost":
			color = Color(1.0, 0.8, 0.0)  # Gold
		"stock":
			if typeof(value) in [TYPE_INT, TYPE_FLOAT]:
				if value == 0:
					color = Color(1.0, 0.3, 0.3)  # Red for out of stock
				elif value < 5:
					color = Color(1.0, 0.6, 0.0)  # Orange for low stock
				else:
					color = Color(0.5, 1.0, 0.5)  # Green for good stock
		"rarity":
			match value.to_lower():
				"common":
					color = Color(0.7, 0.7, 0.7)
				"uncommon":
					color = Color(0.3, 1.0, 0.3)
				"rare":
					color = Color(0.3, 0.6, 1.0)
				"epic":
					color = Color(0.7, 0.3, 1.0)
				"legendary":
					color = Color(1.0, 0.6, 0.0)
		"tier":
			if typeof(value) in [TYPE_INT, TYPE_FLOAT]:
				var tier_colors = [
					Color(0.7, 0.7, 0.7),  # Tier 1 - Gray
					Color(0.3, 1.0, 0.3),  # Tier 2 - Green
					Color(0.3, 0.6, 1.0),  # Tier 3 - Blue
					Color(0.7, 0.3, 1.0),  # Tier 4 - Purple
					Color(1.0, 0.6, 0.0)   # Tier 5+ - Orange
				]
				var tier_index = min(int(value) - 1, tier_colors.size() - 1)
				color = tier_colors[max(0, tier_index)]
		_:
			# For modifier stats, color based on positive/negative
			if stat_key in SIGNED_STATS and typeof(value) in [TYPE_INT, TYPE_FLOAT]:
				if value > 0:
					color = Color(0.3, 1.0, 0.3)  # Green for positive
				elif value < 0:
					color = Color(1.0, 0.3, 0.3)  # Red for negative
	
	label.add_theme_color_override("font_color", color)

func _calculate_spacing(counter: int) -> int:
	"""Calculate spacing for stat alignment"""
	if counter < 3:
		return 6
	elif counter < 7:
		return 9
	elif counter < 10:
		return 6
	elif counter < 13:
		return 3
	else:
		return 0

func _clear_stat_rows():
	"""Clear all stat rows"""
	for row in stat_rows:
		if is_instance_valid(row):
			row.queue_free()
	stat_rows.clear()

func _position_tooltip():
	"""Position tooltip above the item slot"""
	var base_tooltip_height = 130
	var stat_height = 26
	var tooltip_container_height = -(base_tooltip_height + stat_counter * stat_height)
	tooltip_container.position = Vector2(0, tooltip_container_height) 
	clipping_container.custom_minimum_size = Vector2(180, -tooltip_container_height)

func _on_button_input(event: InputEvent):
	"""Handle button input events for right-click"""
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_RIGHT and event.pressed:
			if not is_empty:
				emit_signal("item_right_clicked", item_data)


func _on_item_clicked():
	"""Handle left click"""
	if is_empty:
		return
		
	# Don't toggle selection in shop mode
	if slot_mode == SlotMode.INVENTORY:
		is_selected = not is_selected
	
	emit_signal("item_clicked", item_data)

func _on_mouse_entered():
	is_hovered = true
	# Notify FighterDisplay about hover
	var fighter_display = get_tree().get_first_node_in_group("fighter_display")
	if fighter_display and fighter_display.has_method("preview_item"):
		fighter_display.preview_item(item_data)

func _on_mouse_exited():
	is_hovered = false
	# Clear preview in FighterDisplay
	var fighter_display = get_tree().get_first_node_in_group("fighter_display")
	if fighter_display and fighter_display.has_method("clear_preview"):
		fighter_display.clear_preview()
	
func load_item_data(item_id: String) -> Dictionary:
	"""Load item info from local JSON files"""
	if item_id.is_empty():
		return {}
	
	# Check cache first
	if items_cache.has(item_id):
		return items_cache[item_id]
	
	# Parse item ID: weapons_sword_steel_sword -> weapons, sword, steel_sword
	var parts = item_id.split("_")
	if parts.size() < 3:
		return {}
	
	var category = parts[0]  # "weapons"
	var subcategory = parts[1]  # "sword"
	var item_name = "_".join(parts.slice(2))  # "steel_sword"
	
	# Handle special cases for modifiers
	if parts[0] == "learning" and parts[1] == "modifiers":
		category = "learning_modifiers"
		subcategory = parts[2] if parts.size() > 2 else ""
		item_name = "_".join(parts.slice(3)) if parts.size() > 3 else ""
		
	if parts[0] == "reward" and parts[1] == "modifiers":
		category = "reward_modifiers"
		subcategory = parts[2] if parts.size() > 2 else ""
		item_name = "_".join(parts.slice(3)) if parts.size() > 3 else ""
	
	# Try to load from local JSON file
	var json_path = "res://data/%s.json" % category
	
	if not FileAccess.file_exists(json_path):
		print("Item data file not found: ", json_path)
		return {}
	
	var file = FileAccess.open(json_path, FileAccess.READ)
	if file == null:
		print("Failed to open item data file: ", json_path)
		return {}
	
	var json_string = file.get_as_text()
	file.close()
	
	var json = JSON.new()
	var parse_result = json.parse(json_string)
	
	if parse_result != OK:
		print("Failed to parse JSON: ", json_path)
		return {}
	
	var data = json.data
	
	# Navigate to the specific item
	if data.has(subcategory) and data[subcategory].has(item_name):
		var item_stats_data = data[subcategory][item_name]
		
		# Add generated properties
		item_stats_data["item_id"] = item_id
		item_stats_data["category"] = category
		item_stats_data["subcategory"] = subcategory
		
		# Add name if not present
		if not item_stats_data.has("name"):
			item_stats_data["name"] = item_name.replace("_", " ").capitalize()
		
		# Cache the result
		items_cache[item_id] = item_stats_data
		return item_stats_data
	
	print("Item not found in data: ", item_id)
	return {}

func load_item_texture(item_id: String) -> Texture2D:
	"""Load texture for item based on ID"""
	if item_id.is_empty():
		return null
	
	# Parse item ID for texture path
	var parts = item_id.split("_")
	if parts.size() >= 3:
		var category = parts[0]
		var subcategory = parts[1]
		var item_name = "_".join(parts.slice(2))
		
		# Handle special cases
		if parts[0] == "learning" and parts[1] == "modifiers":
			category = "learning_modifiers"
			subcategory = parts[2] if parts.size() > 2 else ""
			item_name = "_".join(parts.slice(3)) if parts.size() > 3 else ""
			
		if parts[0] == "reward" and parts[1] == "modifiers":
			category = "reward_modifiers"
			subcategory = parts[2] if parts.size() > 2 else ""
			item_name = "_".join(parts.slice(3)) if parts.size() > 3 else ""
		
		# Try multiple texture paths
		var texture_paths = [
			"res://sprites/items/%s/%s/%s.png" % [category, subcategory, item_name],
			"res://sprites/items/%s/%s.png" % [category, item_name],
			"res://sprites/items/%s/%s.png" % [category, subcategory],
			"res://sprites/items/%s.png" % category
		]
		
		for path in texture_paths:
			if ResourceLoader.exists(path):
				return load(path)
		
		print("Item texture not found for: ", item_id)
		return load("res://sprites/placeholder.jpg")  # Fallback
	
	return null
