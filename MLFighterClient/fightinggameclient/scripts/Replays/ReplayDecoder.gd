extends Node
class_name ReplayDecoder

# Decoded replay data
var metadata: Dictionary = {}
var reconstructed_frames: Array = []
var total_frames: int = 0

# Property name mappings
const METADATA_MAPPING = {
	"v": "version",
	"aw": "arena_width",
	"ah": "arena_height",
	"gl": "ground_level",
	"mf": "max_frames",
	"ts": "timestamp_start",
	"te": "timestamp_end",
	"tf": "total_frames",
	"d": "duration_seconds",
	"w": "winner",
	"p1": "player1_fighter",
	"p2": "player2_fighter"
}

const PLAYER_MAPPING = {
	"x": "x",
	"y": "y",
	"h": "health",
	"vx": "velocity_x",
	"vy": "velocity_y",
	"fr": "facing_right",
	"s": "current_state",
	"sf": "state_frame_counter",
	"g": "is_grounded",
	"ac": "attack_cooldown_remaining",
	"bc": "block_cooldown_remaining",
	"jc": "jump_cooldown_remaining",
	"st": "stun_frames_remaining"
}

func decode_replay(json_string: String) -> bool:
	"""Decode compressed replay data into a usable format"""
	var json = JSON.new()
	var parse_result = json.parse(json_string)
	
	if parse_result != OK:
		push_error("Failed to parse replay JSON: " + json.error_string)
		return false
	
	var compressed_data = json.data
	
	# Extract metadata - check both "metadata" and "meta" for compatibility
	var meta_data = compressed_data.get("metadata", compressed_data.get("meta", {}))
	if meta_data.is_empty():
		push_error("Replay data missing metadata")
		return false
	
	metadata = _expand_metadata(meta_data)
	
	# Reconstruct frames
	if not compressed_data.has("frames"):
		push_error("Replay data missing frames")
		return false
	
	_reconstruct_frames(compressed_data.frames)
	total_frames = reconstructed_frames.size()
	
	return true

func _expand_metadata(compressed_meta: Dictionary) -> Dictionary:
	"""Convert shortened metadata keys to full names"""
	var expanded = {}
	for short_key in compressed_meta:
		var full_key = METADATA_MAPPING.get(short_key, short_key)
		expanded[full_key] = compressed_meta[short_key]
	return expanded

func _reconstruct_frames(compressed_frames: Array) -> void:
	"""Reconstruct full frames from delta-compressed data"""
	reconstructed_frames.clear()
	var previous_frame = {}
	
	for compressed_frame in compressed_frames:
		var full_frame = {
			"frame": compressed_frame.get("f", 0),
			"players": {}
		}
		
		# Reconstruct each player's data
		for player_id in ["1", "2"]:
			var full_player_data = {}
			
			# Copy previous frame data if exists
			if previous_frame.has("players") and previous_frame.players.has(player_id):
				full_player_data = previous_frame.players[player_id].duplicate()
			
			# Apply delta changes
			if compressed_frame.has("p") and compressed_frame.p.has(player_id):
				var delta_data = compressed_frame.p[player_id]
				for short_key in delta_data:
					var full_key = PLAYER_MAPPING.get(short_key, short_key)
					full_player_data[full_key] = delta_data[short_key]
			
			full_frame.players[player_id] = full_player_data
		
		reconstructed_frames.append(full_frame)
		previous_frame = full_frame

func get_frame_data(frame_index: int) -> Dictionary:
	"""Get reconstructed frame data at specific index"""
	if frame_index >= 0 and frame_index < reconstructed_frames.size():
		return reconstructed_frames[frame_index]
	return {}

func get_metadata() -> Dictionary:
	return metadata

func get_total_frames() -> int:
	return total_frames
