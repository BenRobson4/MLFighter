extends Node2D

@onready var player1 = $Player1
@onready var player2 = $Player2
@onready var replay_manager = $ReplayManager
@onready var ui = $UI

var ground_level = 500

func _ready():
	# Connect signals
	replay_manager.connect("replay_started", Callable(self, "_on_replay_started"))
	replay_manager.connect("frame_ready", Callable(self, "_on_frame_ready"))
	replay_manager.connect("replay_finished", Callable(self, "_on_replay_finished"))
	
	# For testing, load a replay file
	var test_file = "res://replays/test_replay.json"
	if replay_manager.load_replay_from_file(test_file):
		replay_manager.start_replay()

func _on_replay_started(metadata):
	# Get ground level from metadata
	ground_level = metadata.ground_level
	
	# Configure players based on metadata
	player1.setup_from_config(metadata.player_configs["1"])
	player2.setup_from_config(metadata.player_configs["2"])
	
	# Configure arena
	var arena_width = metadata.arena_width
	# Set arena boundaries, etc.
	
	# Update UI
	ui.set_max_frames(metadata.max_frames)

func _on_frame_ready(frame_data):
	# Update player states
	player1.update_from_frame_data(frame_data.p1)
	player2.update_from_frame_data(frame_data.p2)
	
	# Update UI
	ui.update_frame_counter(frame_data.f)

func _on_replay_finished():
	print("Replay finished")
	# Show end screen, display winner, etc.
