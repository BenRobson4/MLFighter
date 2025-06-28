extends Node

signal frame_ready(frame_data)
signal replay_finished
signal replay_started(metadata)

var replay_data = null
var current_frame_index = 0
var is_playing = false
var playback_speed = 0.2
var frame_timer = 0.0
var frame_duration = 1.0 / 60.0  # Assuming 60 FPS

func load_replay_from_file(filepath):
	var file = FileAccess.open(filepath, FileAccess.READ)
	if file:
		var content = file.get_as_text()
		file.close()
		
		# Handle gzip decompression
		if filepath.ends_with(".gz"):
			content = decompress_gzip(content)
		
		var json = JSON.new()
		var parse_result = json.parse(content)
		if parse_result == OK:
			replay_data = json.get_data()
			print("Replay loaded successfully. Total frames: ", replay_data.metadata.total_frames)
			return true
	
	print("Failed to load replay from file: ", filepath)
	return false

func decompress_gzip(compressed_content):
	# Note: Godot doesn't have built-in gzip decompression in GDScript
	# For testing purposes, we'll use uncompressed JSON files
	# In production, you might need to use a plugin or native code for this
	return compressed_content

func start_replay():
	if replay_data == null:
		print("No replay data loaded")
		return
	
	current_frame_index = 0
	is_playing = true
	emit_signal("replay_started", replay_data.metadata)
	print("Replay started")

func pause_replay():
	is_playing = false

func resume_replay():
	is_playing = true

func stop_replay():
	is_playing = false
	current_frame_index = 0

func seek_to_frame(frame_number):
	if replay_data == null or frame_number >= len(replay_data.frames):
		return
	
	current_frame_index = frame_number
	process_current_frame()

func _process(delta):
	if not is_playing or replay_data == null:
		return
	
	frame_timer += delta * playback_speed
	
	while frame_timer >= frame_duration and current_frame_index < len(replay_data.frames):
		process_current_frame()
		current_frame_index += 1
		frame_timer -= frame_duration
		
		if current_frame_index >= len(replay_data.frames):
			is_playing = false
			emit_signal("replay_finished")
			break

func process_current_frame():
	var frame_data = replay_data.frames[current_frame_index]
	emit_signal("frame_ready", frame_data)

func get_metadata():
	return replay_data.metadata if replay_data else null
