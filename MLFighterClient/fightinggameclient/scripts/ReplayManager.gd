extends Node

signal replay_loaded(replay_data)
signal frame_changed(frame_number)
signal replay_finished()

var replay_data: Dictionary = {}
var frames: Array = []
var current_frame: int = 0
var is_playing: bool = false
var playback_speed: float = 1.0
var frame_timer: float = 0.0
var frame_duration: float = 0.016  # 60 FPS

func load_replay_from_json(json_string: String) -> bool:
	"""Load replay data from JSON string"""
	var json = JSON.new()
	var parse_result = json.parse(json_string)
	
	if parse_result != OK:
		print("Failed to parse replay JSON")
		return false
	
	replay_data = json.data
	frames = replay_data.get("frames", [])
	
	if frames.size() == 0:
		print("No frames in replay data")
		return false
	
	print("Loaded replay with ", frames.size(), " frames")
	emit_signal("replay_loaded", replay_data)
	return true

func play():
	"""Start playing the replay"""
	is_playing = true
	current_frame = 0
	frame_timer = 0.0

func pause():
	"""Pause replay playback"""
	is_playing = false

func stop():
	"""Stop replay and reset to beginning"""
	is_playing = false
	current_frame = 0
	frame_timer = 0.0

func seek(frame_number: int):
	"""Jump to specific frame"""
	current_frame = clamp(frame_number, 0, frames.size() - 1)
	emit_signal("frame_changed", current_frame)

func get_current_frame() -> Dictionary:
	"""Get current frame data"""
	if current_frame < frames.size():
		return frames[current_frame]
	return {}

func get_frame(frame_number: int) -> Dictionary:
	"""Get specific frame data"""
	if frame_number >= 0 and frame_number < frames.size():
		return frames[frame_number]
	return {}

func _process(delta):
	"""Process replay playback"""
	if not is_playing or frames.size() == 0:
		return
	
	frame_timer += delta * playback_speed
	
	while frame_timer >= frame_duration:
		frame_timer -= frame_duration
		
		if current_frame < frames.size() - 1:
			current_frame += 1
			emit_signal("frame_changed", current_frame)
		else:
			is_playing = false
			emit_signal("replay_finished")
			break
