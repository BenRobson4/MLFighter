extends Control

@onready var network_manager = $NetworkManager
@onready var game_state_manager = $GameStateManager
@onready var log_text = $VBoxContainer/HSplitContainer/LogPanel/MarginContainer/VBoxContainer/ScrollContainer/LogText
@onready var game_content = $VBoxContainer/HSplitContainer/GameContent

# Debug buttons
@onready var connect_button = $VBoxContainer/TopPanel/MarginContainer/VBoxContainer/GridContainer/ConnectButton
@onready var disconnect_button = $VBoxContainer/TopPanel/MarginContainer/VBoxContainer/GridContainer/DisconnectButton
@onready var purchase_button = $VBoxContainer/TopPanel/MarginContainer/VBoxContainer/GridContainer/PurchaseButton
@onready var refresh_shop_button = $VBoxContainer/TopPanel/MarginContainer/VBoxContainer/GridContainer/RefreshShopButton
@onready var request_options_button = $VBoxContainer/TopPanel/MarginContainer/VBoxContainer/GridContainer/RequestOptionsButton
@onready var initial_shop_complete_button = $VBoxContainer/TopPanel/MarginContainer/VBoxContainer/GridContainer/InitialShopCompleteButton
@onready var replay_viewed_button = $VBoxContainer/TopPanel/MarginContainer/VBoxContainer/GridContainer/ReplayViewedButton
@onready var shop_phase_complete_button = $VBoxContainer/TopPanel/MarginContainer/VBoxContainer/GridContainer/ShopPhaseCompleteButton
@onready var get_status_button = $VBoxContainer/TopPanel/MarginContainer/VBoxContainer/GridContainer/GetStatusButton

const SERVER_URL = "ws://localhost:8765/ws"

func _ready():
	print("Main scene ready")
	
	# Seed random number generator for client ID
	randomize()
	
	# Set up log formatting
	log_text.bbcode_enabled = true
	log_text.scroll_following = true  # Auto-scroll
	
	# Show client ID
	var client_id = network_manager.get_client_id()
	log_message("[color=green]Debug client started[/color] | Client ID: %s" % client_id, "SYSTEM")
	
	# Connect network manager signals
	network_manager.connected_to_server.connect(_on_connected)
	network_manager.disconnected_from_server.connect(_on_disconnected)
	network_manager.message_received.connect(_on_message_received)
	network_manager.message_sent.connect(_on_message_sent)
	
	# Connect game state manager signals
	game_state_manager.scene_changed.connect(_on_scene_changed)
	
	# Connect button signals
	connect_button.pressed.connect(_on_connect_pressed)
	disconnect_button.pressed.connect(_on_disconnect_pressed)
	purchase_button.pressed.connect(_on_purchase_pressed)
	refresh_shop_button.pressed.connect(_on_refresh_shop_pressed)
	request_options_button.pressed.connect(_on_request_options_pressed)
	initial_shop_complete_button.pressed.connect(_on_initial_shop_complete_pressed)
	replay_viewed_button.pressed.connect(_on_replay_viewed_pressed)
	shop_phase_complete_button.pressed.connect(_on_shop_phase_complete_pressed)
	get_status_button.pressed.connect(_on_get_status_pressed)
	
	# Initial button states
	disconnect_button.disabled = true
	_set_message_buttons_enabled(false)
	
	print("Signal connections complete")

func _on_connected():
	print("Connected callback triggered")
	var client_id = network_manager.get_client_id()
	log_message("[color=green]Connected to server![/color] | Client ID: %s" % client_id, "SYSTEM")
	connect_button.disabled = true
	disconnect_button.disabled = false
	_set_message_buttons_enabled(true)

func _on_disconnected():
	print("Disconnected callback triggered")
	log_message("[color=red]Disconnected from server![/color]", "SYSTEM")
	connect_button.disabled = false
	disconnect_button.disabled = true
	_set_message_buttons_enabled(false)

func _on_message_received(message: Dictionary):
	print("Message received: ", message)
	var pretty_json = JSON.stringify(message, "\t")
	log_message("[color=cyan]RECEIVED:[/color]\n" + pretty_json, "SERVER")

func _on_message_sent(message: Dictionary):
	print("Message sent: ", message)
	var pretty_json = JSON.stringify(message, "\t")
	log_message("[color=yellow]SENT:[/color]\n" + pretty_json, "CLIENT")

func _on_scene_changed(scene_name: String):
	log_message("[color=magenta]Scene changed to: %s[/color]" % scene_name, "SYSTEM")

func log_message(text: String, source: String = ""):
	var timestamp = Time.get_time_string_from_system()
	var formatted = "[color=gray][%s][/color] %s\n" % [timestamp, text]
	log_text.append_text(formatted)
	
	# Force scroll to bottom
	await get_tree().process_frame
	log_text.scroll_to_line(log_text.get_line_count() - 1)

func _set_message_buttons_enabled(enabled: bool):
	purchase_button.disabled = not enabled
	refresh_shop_button.disabled = not enabled
	request_options_button.disabled = not enabled
	initial_shop_complete_button.disabled = not enabled
	replay_viewed_button.disabled = not enabled
	shop_phase_complete_button.disabled = not enabled
	get_status_button.disabled = not enabled

# Button handlers
func _on_connect_pressed():
	log_message("Attempting to connect to %s" % SERVER_URL, "SYSTEM")
	var err = network_manager.connect_to_server(SERVER_URL)
	if err != OK:
		log_message("[color=red]Failed to initiate connection: %s[/color]" % error_string(err), "SYSTEM")

func _on_disconnect_pressed():
	log_message("Disconnecting from server", "SYSTEM")
	network_manager.disconnect_from_server()

func _on_purchase_pressed():
	network_manager.send_message({
		"type": "purchase_option",
		"option_id": "test_item_001"
	})

func _on_refresh_shop_pressed():
	network_manager.send_message({
		"type": "refresh_shop"
	})

func _on_request_options_pressed():
	network_manager.send_message({
		"type": "request_options"
	})

func _on_initial_shop_complete_pressed():
	network_manager.send_message({
		"type": "initial_shop_complete"
	})

func _on_replay_viewed_pressed():
	network_manager.send_message({
		"type": "replay_viewed"
	})

func _on_shop_phase_complete_pressed():
	network_manager.send_message({
		"type": "shop_phase_complete"
	})

func _on_get_status_pressed():
	network_manager.send_message({
		"type": "get_status"
	})
