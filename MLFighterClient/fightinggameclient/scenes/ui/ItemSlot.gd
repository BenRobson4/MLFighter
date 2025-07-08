extends Control
class_name ItemSlot

signal item_clicked(item_data: Dictionary)
signal item_right_clicked(item_data: Dictionary)

@onready var item_background = $ItemBackground
@onready var item_sprite = $ItemSprite
@onready var item_border = $ItemBorder
@onready var item_button = $ItemButton
@onready var tooltip_container = $TooltipContainer
@onready var item_name_label = $TooltipContainer/TooltipContent/ItemName
@onready var item_description_label = $TooltipContainer/TooltipContent/ItemDescription

# Border textures
@export var default_border: Texture2D
@export var hover_border: Texture2D  
@export var selected_border: Texture2D  

var item_data: Dictionary = {}
var is_empty: bool = true
var is_selected: bool = false
var is_hovered: bool = false

# Cache for loaded item data
static var items_cache: Dictionary = {}

func _ready():
	# Connect signals
	item_button.mouse_entered.connect(_on_mouse_entered)
	item_button.mouse_exited.connect(_on_mouse_exited)
	item_button.pressed.connect(_on_item_clicked)
	
	# Initialize empty state
	clear_slot()
	set_item({"item_id":"weapons_sword_steel_sword"})
	
func _process(delta):
	# Update border based on state
	if is_selected:
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
	
	# Load item info from files
	var item_id = data.get("item_id", "")
	if not item_id.is_empty():
		item_data = load_item_data(item_id)
	
	# Load and set item sprite
	var item_texture = load_item_texture(data.get("item_id", ""))
	if item_texture:
		item_sprite.texture = item_texture
		item_sprite.visible = true
	else:
		item_sprite.visible = false
	
	# Update tooltip content
	_update_tooltip_content()
	
	# Show background
	item_background.visible = true

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
	item_description_label.visible = not description.is_empty()
	
	# Position tooltip above the item slot
	_position_tooltip()

func _position_tooltip():
	"""Position tooltip above the item slot"""
	var tooltip_height = tooltip_container.size.y
	tooltip_container.position = Vector2(0, -tooltip_height - 10)  # 10px gap

func _on_item_clicked():
	is_selected = not is_selected

func _on_mouse_entered():
	is_hovered = true

func _on_mouse_exited():
	is_hovered = false
	
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
	
	# Parse item ID: weapons_sword_steel_sword -> weapons/sword/steel_sword.png
	var parts = item_id.split("_")
	if parts.size() >= 3:
		var category = parts[0]  # "weapons"
		var subcategory = parts[1]  # "sword" 
		var item_name = "_".join(parts.slice(2))  # "steel_sword"
		
		var texture_path = "res://sprites/items/%s/%s/%s.png" % [category, subcategory, item_name]
		
		if ResourceLoader.exists(texture_path):
			return load(texture_path)
		else:
			# Try fallback path
			texture_path = "res://sprites/items/%s/%s.png" % [category, item_name]
			if ResourceLoader.exists(texture_path):
				return load(texture_path)
			else:
				print("Item texture not found: ", texture_path)
				return load("res://sprites/placeholder.png")  # Fallback
	
	return null
