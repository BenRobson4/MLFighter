extends BaseTemplate

var replay_viewer_scene: PackedScene
var replay_viewer_instance: Node
var pending_replay_data: Dictionary = {}

func _ready():
	super._ready()
	
	# Load the ReplayViewer scene
	replay_viewer_scene = preload("res://scenes/replay/ReplayViewer.tscn")
	
	# Create and add instance
	replay_viewer_instance = replay_viewer_scene.instantiate()
	add_child(replay_viewer_instance)
	
	# Make it fill the container
	if replay_viewer_instance is Control:
		replay_viewer_instance.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	# Wait for scene to be ready
	await get_tree().process_frame
	
	# Process pending data if any
	if not pending_replay_data.is_empty():
		_load_replay_data(pending_replay_data)
		pending_replay_data.clear()

func _on_data_received(data: Dictionary):
	"""Handle data from server"""
	if not replay_viewer_instance:
		pending_replay_data = data
		return
	
	_load_replay_data(data)

func _load_replay_data(data: Dictionary):
	"""Load replay data into the viewer"""
	if not replay_viewer_instance:
		push_error("Replay viewer instance not ready")
		return
	
	if not data.has("replay_data"):
		push_error("No replay_data in server response")
		return
	
	# Convert replay data to JSON string
	var json_string = JSON.stringify(data.replay_data)
	
	# Get GameWorld from the viewer
	var game_world = replay_viewer_instance.get_node_or_null(
		"VBoxContainer/ArenaSection/ArenaBackground/GameViewportContainer/GameViewport/GameWorld"
	)
	
	if not game_world:
		push_error("GameWorld not found in ReplayViewer")
		return
	
	# Store replay data for reload functionality
	if game_world.has_method("set_replay_data"):
		game_world.set_replay_data(json_string)
	
	# Get ReplayManager and load the replay
	var replay_manager = game_world.get_node_or_null("ReplayManager")
	if not replay_manager:
		push_error("ReplayManager not found")
		return
	
	# Load and start replay
	if replay_manager.load_replay_data(json_string):
		await get_tree().process_frame  # Wait for initialization
		replay_manager.start_replay()
	else:
		push_error("Failed to load replay data")
	
	# Handle batch summary for UI updates
	if data.has("batch_summary"):
		_update_batch_info(data.batch_summary)

func _update_batch_info(summary: Dictionary):
	"""Update UI with batch information"""
	var info_text = "Batch: Wins %d, Losses %d (%.1f%%)" % [
		summary.get("wins", 0),
		summary.get("losses", 0),
		summary.get("win_rate", 0) * 100
	]
	print(info_text)  # Could update a UI label here if needed
