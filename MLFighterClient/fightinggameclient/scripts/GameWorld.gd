extends Node2D

@onready var player1 = $Player1
@onready var player2 = $Player2
@onready var replay_manager = $ReplayManager
@onready var ui = $UI

func _ready():
	# Connect replay manager signals
	replay_manager.replay_loaded.connect(_on_replay_loaded)
	replay_manager.frame_changed.connect(_on_frame_changed)
	replay_manager.replay_finished.connect(_on_replay_finished)

func _process(delta):
	replay_manager.process_replay(delta)

func _on_replay_loaded():
	print("Replay loaded successfully")
	# Initialize players to first frame
	_on_frame_changed(0)

func _on_frame_changed(frame_number: int):
	var frame_data = replay_manager.get_current_frame_data()
	
	if frame_data.is_empty():
		return
	
	# Update player states
	if frame_data.has("players"):
		var players_data = frame_data["players"]
		
		if players_data.has("player1"):
			player1.update_from_state(players_data["player1"])
		
		if players_data.has("player2"):
			player2.update_from_state(players_data["player2"])
	
	# Play actions
	if frame_data.has("actions"):
		var actions = frame_data["actions"]
		
		if actions.has("player1"):
			player1.play_action(actions["player1"])
		
		if actions.has("player2"):
			player2.play_action(actions["player2"])
	
	# Update UI
	update_ui(frame_data)

func update_ui(frame_data: Dictionary):
	# Update frame counter
	if ui.has_node("FrameLabel"):
		ui.get_node("FrameLabel").text = "Frame: " + str(frame_data.get("frame_number", 0))
	
	# Update game over state
	if frame_data.get("game_over", false):
		var winner = frame_data.get("winner", "")
		if ui.has_node("WinnerLabel"):
			ui.get_node("WinnerLabel").text = "Winner: " + winner
			ui.get_node("WinnerLabel").visible = true

func _on_replay_finished():
	print("Replay finished")