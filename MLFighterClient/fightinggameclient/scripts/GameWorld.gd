extends Node2D

@onready var player1 = $Player1
@onready var player2 = $Player2
@onready var replay_manager = $ReplayManager
@onready var camera = $Camera2D

# References to UI elements
var top_bar: TopBar
var bottom_bar: BottomBar
var main_scene
var arena_background: ColorRect

func _ready():
	# Create arena background
	_create_arena_background()
	
	# Connect players to replay manager
	replay_manager.player1 = player1
	replay_manager.player2 = player2
	replay_manager.camera = camera

func _create_arena_background():
	arena_background = ColorRect.new()
	arena_background.color = Color(1.0, 1.0, 1.0, 1.0)  # Dark green arena
	arena_background.size = Vector2(2000, 2000)  # Large enough to cover any arena
	arena_background.position = Vector2(-1000, -1000)  # Center it
	arena_background.z_index = -100  # Put it behind everything
	add_child(arena_background)
	print("Created arena background")

func on_replay_loaded(metadata: Dictionary):
	"""Called when replay data is loaded"""
	if metadata.has("arena_width") and metadata.has("arena_height"):
		var width = metadata.arena_width
		var height = metadata.arena_height
		
		# Update arena background size to match arena dimensions
		if arena_background:
			arena_background.size = Vector2(width, height)
			arena_background.position = Vector2(0, -height)  # Position based on your coordinate system
		
# Called by Main scene to connect UI references
func connect_ui(top_bar_ref: TopBar, bottom_bar_ref: BottomBar):
	top_bar = top_bar_ref
	bottom_bar = bottom_bar_ref
	
	# Connect bottom bar signals
	if bottom_bar:
		bottom_bar.play_pressed.connect(_on_play_pressed)
		bottom_bar.pause_pressed.connect(_on_pause_pressed)
		bottom_bar.stop_pressed.connect(_on_stop_pressed)
		bottom_bar.load_pressed.connect(_on_load_pressed)
		bottom_bar.speed_changed.connect(_on_speed_changed)
		bottom_bar.frame_seek.connect(_on_frame_seek)

# Called by Main scene to get arena dimension updates
func connect_main_scene(main_ref):
	main_scene = main_ref
	
# UI Interface functions (called by ReplayManager)
func initialize_health_bars(replay_data: Dictionary):
	if replay_data.has("frames") and replay_data.frames.size() > 0:
		var first_frame = replay_data.frames[0]
		var p1_health = first_frame.players.get("1", {}).get("health", 100.0)
		var p2_health = first_frame.players.get("2", {}).get("health", 100.0)
		
		if top_bar:
			top_bar.initialize_health_bars(p1_health, p2_health)

func setup_replay_info(metadata: Dictionary):
	if bottom_bar:
		bottom_bar.setup_replay_info(metadata)
	
	# Also handle arena dimensions
	on_replay_loaded(metadata)

func update_frame_info(current_frame: int, total_frames: int):
	if bottom_bar:
		bottom_bar.update_frame_info(current_frame, total_frames)
		
func update_player_health(player_num: int, health: float):
	if top_bar:
		top_bar.update_player_health(player_num, health)

# Signal handlers for UI controls
func _on_play_pressed():
	replay_manager.start_replay()

func _on_pause_pressed():
	if replay_manager.is_paused:
		replay_manager.resume_replay()
	else:
		replay_manager.pause_replay()

func _on_stop_pressed():
	replay_manager.stop_replay()

func _on_load_pressed():
	replay_manager.load_replay_from_file("res://replay.json")

func _on_speed_changed(value: float):
	replay_manager.set_replay_speed(value)

func _on_frame_seek(value: float):
	replay_manager.seek_to_frame(int(value))

# Function to load replay from server (called from Main if needed)
func load_replay_from_server(json_data: String):
	replay_manager.load_replay_data(json_data)

func _on_replay_received(json_data: String):
	load_replay_from_server(json_data)
	replay_manager.start_replay()
