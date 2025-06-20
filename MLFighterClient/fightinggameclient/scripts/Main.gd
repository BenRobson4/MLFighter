extends Node2D

@onready var player1 = $Player1
@onready var player2 = $Player2
@onready var replay_manager = $ReplayManager
@onready var network_manager = $NetworkManager
@onready var ui = $UI

var current_frame_data: Dictionary = {}

func _ready():
	# Connect signals
	replay_manager.frame_changed.connect(_on_frame_changed)
	replay_manager.replay_loaded.connect(_on_replay_loaded)
	replay_manager.replay_finished.connect(_on_replay_finished)
	
	network_manager.replay_received.connect(_on_replay_received)
	network_manager.connected_to_server.connect(_on_connected)
	
	# Initialize UI
	if ui:
		ui.play_button.pressed.connect(_on_play_pressed)
		ui.pause_button.pressed.connect(_on_pause_pressed)
		ui.slider.value_changed.connect(_on_seek)
	
	# Connect to server (adjust host/port as needed)
	network_manager.connect_to_server("localhost", 8080)

func _on_connected():
	print("Connected to server!")
	# Request a replay
	network_manager.request_replay()

func _on_replay_received(replay_json: String):
	print("Received replay from server")
	if replay_manager.load_replay_from_json(replay_json):
		# Start playing automatically
		replay_manager.play()

func _on_replay_loaded(replay_data: Dictionary):
	print("Replay loaded successfully")
	# Update UI with replay info
	if ui:
		ui.set_max_frames(replay_manager.frames.size())

func _on_frame_changed(frame_number: int):
	"""Handle frame change during replay"""
	current_frame_data = replay_manager.get_current_frame()
	
	if current_frame_data.size() == 0:
		return
	
	# Update player states
	if current_frame_data.has("players"):
		var players_data = current_frame_data["players"]
		
		if players_data.has("player1") and player1:
			player1.update_state(players_data["player1"])
		
		if players_data.has("player2") and player2:
			player2.update_state(players_data["player2"])
	
	# Trigger action animations
	if current_frame_data.has("actions"):
		var actions = current_frame_data["actions"]
		
		if actions.has("player1") and player1:
			player1.perform_action(actions["player1"])
		
		if actions.has("player2") and player2:
			player2.perform_action(actions["player2"])
	
	# Update UI
	if ui:
		ui.update_frame_counter(frame_number)
		ui.slider.set_value_no_signal(frame_number)
	
	# Check for game over
	if current_frame_data.get("game_over", false):
		var winner = current_frame_data.get("winner", "")
		_show_game_over(winner)

func _on_replay_finished():
	print("Replay finished")
	if ui:
		ui.show_replay_finished()

func _show_game_over(winner: String):
	"""Display game over screen"""
	if ui:
		ui.show_winner(winner)

func _on_play_pressed():
	replay_manager.play()

func _on_pause_pressed():
	replay_manager.pause()

func _on_seek(value: float):
	replay_manager.seek(int(value))
