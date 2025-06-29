extends Node
class_name ReplayManager

signal replay_finished
signal replay_started
signal arena_dimensions_loaded(width: float, height: float)

@export var replay_speed: float = 1.0
@export var auto_play: bool = true

var replay_data: Dictionary = {}
var current_frame: int = 0
var is_playing: bool = false
var is_paused: bool = false
var total_frames: int = 0

# References to players
var player1: Player
var player2: Player

# Reference to camera
var camera: ArenaCamera

# Reference to the GameWorld (which coordinates UI updates)
var game_world

func _ready():
	# Get reference to parent GameWorld
	game_world = get_parent()

func load_replay_data(json_string: String) -> bool:
	var json = JSON.new()
	var parse_result = json.parse(json_string)
	
	if parse_result != OK:
		print("Error parsing JSON: ", json.error_string)
		return false
	
	replay_data = json.data
	total_frames = replay_data.frames.size()
	current_frame = 0
	
	# Setup camera based on arena dimensions
	if camera and replay_data.has("metadata"):
		var metadata = replay_data.metadata
		if metadata.has("arena_width") and metadata.has("arena_height"):
			camera.setup_camera_for_arena(metadata.arena_width, metadata.arena_height)
	
	print("Loaded replay with ", total_frames, " frames")
	print("Arena size: ", replay_data.metadata.arena_width, "x", replay_data.metadata.arena_height)
	
	# Notify GameWorld to update UI
	if game_world and game_world.has_method("setup_replay_info"):
		game_world.setup_replay_info(replay_data.metadata)
		game_world.initialize_health_bars(replay_data)
	
	return true

func load_replay_from_file(file_path: String) -> bool:
	if not FileAccess.file_exists(file_path):
		print("Replay file not found: ", file_path)
		return false
	
	var file = FileAccess.open(file_path, FileAccess.READ)
	if file == null:
		print("Failed to open replay file: ", file_path)
		return false
	
	var json_string = file.get_as_text()
	file.close()
	
	return load_replay_data(json_string)

func start_replay():
	if replay_data.is_empty():
		print("No replay data loaded")
		return
	
	is_playing = true
	is_paused = false
	current_frame = 0
	replay_started.emit()
	
	if auto_play:
		_start_playback()

func _start_playback():
	# Calculate frame duration based on replay speed
	var frame_duration = (1.0 / 60.0) / replay_speed  # Assuming 60 FPS
	
	var timer = Timer.new()
	add_child(timer)
	timer.wait_time = frame_duration
	timer.timeout.connect(_on_frame_timer_timeout)
	timer.start()

func _on_frame_timer_timeout():
	if not is_playing or is_paused:
		return
	
	update_frame()
	current_frame += 1
	
	if current_frame >= total_frames:
		stop_replay()

func update_frame():
	if current_frame >= total_frames:
		return
	
	var frame_data = replay_data.frames[current_frame]
	
	# Update players
	if player1 and frame_data.players.has("1"):
		player1.update_player_data(frame_data.players["1"])
		# Update health bar through GameWorld
		if game_world and game_world.has_method("update_player_health"):
			game_world.update_player_health(1, frame_data.players["1"].health)
	
	if player2 and frame_data.players.has("2"):
		player2.update_player_data(frame_data.players["2"])
		# Update health bar through GameWorld
		if game_world and game_world.has_method("update_player_health"):
			game_world.update_player_health(2, frame_data.players["2"].health)
	
	# Update frame info through GameWorld
	if game_world and game_world.has_method("update_frame_info"):
		game_world.update_frame_info(current_frame, total_frames)

func stop_replay():
	is_playing = false
	is_paused = false
	replay_finished.emit()
	
	# Clean up timer
	for child in get_children():
		if child is Timer:
			child.queue_free()

func pause_replay():
	is_paused = true

func resume_replay():
	is_paused = false

func seek_to_frame(frame: int):
	if frame < 0 or frame >= total_frames:
		return
	
	current_frame = frame
	update_frame()

func set_replay_speed(speed: float):
	replay_speed = clamp(speed, 0.1, 5.0)
	
	# Update timer if playing
	for child in get_children():
		if child is Timer:
			child.wait_time = (1.0 / 60.0) / replay_speed
