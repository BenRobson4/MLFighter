extends Node
class_name ReplayManager

signal replay_finished
signal replay_started

@export var replay_speed: float = 1.0
@export var auto_play: bool = true

var current_frame: int = 0
var is_playing: bool = false
var is_paused: bool = false
var total_frames: int = 0

# References
var player1: Player
var player2: Player
var camera: ArenaCamera
var game_world  # Parent GameWorld reference

# Core components
var decoder: ReplayDecoder
var playback_timer: Timer

func _ready():
	game_world = get_parent()
	
	# Create decoder
	decoder = ReplayDecoder.new()
	add_child(decoder)
	
	# Create playback timer
	playback_timer = Timer.new()
	playback_timer.timeout.connect(_on_frame_timer_timeout)
	add_child(playback_timer)

func load_replay_data(json_string: String) -> bool:
	"""Load replay from JSON string"""
	if not decoder.decode_replay(json_string):
		return false
	
	total_frames = decoder.get_total_frames()
	current_frame = 0
	
	var metadata = decoder.get_metadata()
	
	# Setup camera if arena dimensions available
	if camera and metadata.has("arena_width") and metadata.has("arena_height"):
		camera.setup_camera_for_arena(metadata.arena_width, metadata.arena_height)
	
	# Notify GameWorld to update UI
	if game_world:
		if game_world.has_method("setup_replay_info"):
			game_world.setup_replay_info(metadata)
		
		# Initialize health bars with first frame
		if total_frames > 0 and game_world.has_method("initialise_health_bars"):
			var first_frame = decoder.get_frame_data(0)
			game_world.initialise_health_bars(first_frame)
	
	return true

func load_replay_from_file(file_path: String) -> bool:
	"""Load replay from file - kept for compatibility"""
	if not FileAccess.file_exists(file_path):
		push_error("Replay file not found: " + file_path)
		return false
	
	var file = FileAccess.open(file_path, FileAccess.READ)
	if not file:
		push_error("Failed to open replay file: " + file_path)
		return false
	
	var json_string = file.get_as_text()
	file.close()
	
	return load_replay_data(json_string)

func start_replay():
	"""Start or restart replay playback"""
	if total_frames == 0:
		push_warning("No replay data loaded")
		return
	
	is_playing = true
	is_paused = false
	current_frame = 0
	
	replay_started.emit()
	
	if auto_play:
		_start_playback()

func stop_replay():
	"""Stop replay playback"""
	is_playing = false
	is_paused = false
	playback_timer.stop()
	replay_finished.emit()

func pause_replay():
	is_paused = true
	playback_timer.stop()

func resume_replay():
	if is_playing and is_paused:
		is_paused = false
		_start_playback()

func seek_to_frame(frame: int):
	"""Jump to specific frame"""
	current_frame = clamp(frame, 0, total_frames - 1)
	update_frame()

func set_replay_speed(speed: float):
	"""Change playback speed"""
	replay_speed = clamp(speed, 0.1, 5.0)
	if playback_timer.timeout.is_connected(_on_frame_timer_timeout):
		playback_timer.wait_time = (1.0 / 60.0) / replay_speed

func update_frame():
	"""Update current frame display"""
	if current_frame >= total_frames:
		return
	
	var frame_data = decoder.get_frame_data(current_frame)
	
	# Update players
	if player1 and frame_data.players.has("1"):
		player1.update_player_data(frame_data.players["1"])
		if game_world and game_world.has_method("update_player_health"):
			game_world.update_player_health(1, frame_data.players["1"].health)
	
	if player2 and frame_data.players.has("2"):
		player2.update_player_data(frame_data.players["2"])
		if game_world and game_world.has_method("update_player_health"):
			game_world.update_player_health(2, frame_data.players["2"].health)
	
	# Update frame counter
	if game_world and game_world.has_method("update_frame_info"):
		game_world.update_frame_info(current_frame, total_frames)

func _start_playback():
	"""Start the playback timer"""
	playback_timer.wait_time = (1.0 / 60.0) / replay_speed
	playback_timer.start()

func _on_frame_timer_timeout():
	"""Handle frame advancement"""
	if not is_playing or is_paused:
		return
	
	update_frame()
	current_frame += 1
	
	if current_frame >= total_frames:
		stop_replay()
