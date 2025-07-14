extends Control

@onready var vbox_container = $VBoxContainer
@onready var top_bar = $VBoxContainer/TopBar
@onready var arena_section = $VBoxContainer/ArenaSection
@onready var arena_background = $VBoxContainer/ArenaSection/ArenaBackground
@onready var game_viewport_container = $VBoxContainer/ArenaSection/ArenaBackground/GameViewportContainer
@onready var game_viewport = $VBoxContainer/ArenaSection/ArenaBackground/GameViewportContainer/GameViewport
@onready var bottom_bar = $VBoxContainer/BottomBar

# UI settings
@export var top_bar_height: int = 100
@export var bottom_bar_height: int = 120
@export var border_width: int = 10
@export var border_color: Color = Color(0.4, 0.4, 0.4, 1.0)
@export var background_color: Color = Color(0.1, 0.1, 0.1, 0.9)

# Arena dimensions (from replay data)
var arena_width: float = 800
var arena_height: float = 400

func _ready():
	# Set up initial layout
	_setup_initial_layout()
	
	# Connect to viewport size changes
	get_viewport().size_changed.connect(_on_viewport_size_changed)
	
	# Connect UI to GameWorld
	await get_tree().process_frame
	var game_world = game_viewport.get_node_or_null("GameWorld")
	if game_world:
		if game_world.has_method("connect_ui"):
			game_world.connect_ui(top_bar, bottom_bar)
		if game_world.has_method("connect_main_scene"):
			game_world.connect_main_scene(self)

func _setup_initial_layout():
	# Set up VBoxContainer to fill the screen
	vbox_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	# Set fixed heights for top and bottom bars
	if top_bar:
		top_bar.custom_minimum_size.y = top_bar_height
		top_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	
	if bottom_bar:
		bottom_bar.custom_minimum_size.y = bottom_bar_height
		bottom_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	
	# Set up arena section to expand and fill
	if arena_section:
		arena_section.size_flags_vertical = Control.SIZE_EXPAND_FILL
		arena_section.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		
		# Set margins for the border effect
		arena_section.add_theme_constant_override("margin_left", border_width)
		arena_section.add_theme_constant_override("margin_right", border_width)
		arena_section.add_theme_constant_override("margin_top", 0)
		arena_section.add_theme_constant_override("margin_bottom", 0)
	
	# Set up arena background color
	if arena_background:
		if arena_background is Panel:
			var style = StyleBoxFlat.new()
			style.bg_color = border_color
			arena_background.add_theme_stylebox_override("panel", style)
		elif arena_background is ColorRect:
			arena_background.color = border_color
	
	# Set up viewport container
	if game_viewport_container:
		game_viewport_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		game_viewport_container.stretch = true
		game_viewport_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		game_viewport_container.size_flags_vertical = Control.SIZE_EXPAND_FILL
	
	# Initial viewport setup
	_update_viewport_size()

func set_arena_dimensions(width: float, height: float):
	"""Called by GameWorld when replay is loaded"""
	arena_width = width
	arena_height = height
	print("Arena dimensions set: ", width, "x", height)
	_update_viewport_size()
	
	# Update camera in GameWorld
	if game_viewport:
		var game_world = game_viewport.get_node_or_null("GameWorld")
		if game_world and game_world.has_node("Camera2D"):
			var camera = game_world.get_node("Camera2D")
			if camera.has_method("setup_camera_for_arena"):
				camera.setup_camera_for_arena(width, height)

func _on_viewport_size_changed():
	_update_viewport_size()

func _update_viewport_size():
	# Wait for layout to update
	await get_tree().process_frame
	
	if not game_viewport_container or not game_viewport:
		return
	
	# Get the actual size of the viewport container
	var container_size = game_viewport_container.size
	
	# Update SubViewport to match container
	game_viewport.size = container_size
	
