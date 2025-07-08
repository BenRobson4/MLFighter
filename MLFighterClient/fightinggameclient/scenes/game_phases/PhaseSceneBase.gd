extends Control  # or Node2D depending on your needs

class_name PhaseSceneBase

var network_manager: Node
var game_state_manager: Node
var phase_data: Dictionary = {}

func _ready():
	# Get references to managers
	network_manager = get_node("/root/Main/NetworkManager")
	game_state_manager = get_node("/root/Main/GameStateManager")
	
	# Connect to relevant signals
	network_manager.message_received.connect(_on_message_received)
	
	# Call phase-specific initialization
	_on_phase_entered()

func initialize(data: Dictionary):
	"""Called by GameStateManager when scene is loaded"""
	phase_data = data
	
func _on_phase_entered():
	"""Override in child classes for phase-specific setup"""
	pass

func _on_message_received(message: Dictionary):
	"""Override in child classes to handle phase-specific messages"""
	pass

func send_to_server(message: Dictionary):
	"""Helper to send messages to server"""
	network_manager.send_message(message)
