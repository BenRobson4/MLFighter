extends Node

signal connected_to_server()
signal disconnected_from_server()
signal message_received(message: Dictionary)
signal message_sent(message: Dictionary)

var websocket: WebSocketPeer
var client_id: String = ""
var is_connected: bool = false

func _ready():
	print("NetworkManager ready")
	websocket = WebSocketPeer.new()
	
	# Increase limits to handle large replays
	websocket.set_inbound_buffer_size(1024 * 1024 * 1)  # 1 MB
	websocket.set_outbound_buffer_size(1024 * 1024 * 1)  # 1 MB
	
	set_process(false)
	# Generate a client ID similar to tkinter client
	client_id = "godot_client_" + _generate_short_uuid()
	print("Generated client ID: ", client_id)

func _generate_short_uuid() -> String:
	# Generate a short UUID-like string (8 characters)
	var chars = "0123456789abcdef"
	var result = ""
	for i in range(8):
		result += chars[randi() % chars.length()]
	return result

func connect_to_server(url: String) -> int:
	print("Connecting to: ", url)
	var err = websocket.connect_to_url(url)
	if err == OK:
		set_process(true)
		print("WebSocket connection initiated")
	else:
		print("WebSocket connection failed: ", error_string(err))
	return err

func disconnect_from_server():
	print("Disconnecting WebSocket")
	# Send disconnect message before closing
	if is_connected:
		send_message({"type": "disconnect"})
		await get_tree().create_timer(0.1).timeout  # Give it time to send
	websocket.close()
	set_process(false)
	is_connected = false

func _process(_delta):
	websocket.poll()
	
	var state = websocket.get_ready_state()
	
	match state:
		WebSocketPeer.STATE_CONNECTING:
			pass  # Don't spam the console
		
		WebSocketPeer.STATE_OPEN:
			if not is_connected:
				is_connected = true
				print("WebSocket connected! Sending initial connect message...")
				
				# Send initial connect message like tkinter client
				var connect_msg = {
					"type": "connect",
					"client_id": client_id
				}
				send_message(connect_msg)
				
				# Don't emit connected signal yet - wait for server response
			
			while websocket.get_available_packet_count():
				var packet = websocket.get_packet()
				_handle_packet(packet)
		
		WebSocketPeer.STATE_CLOSING:
			print("WebSocket closing...")
		
		WebSocketPeer.STATE_CLOSED:
			if is_connected:
				is_connected = false
				var code = websocket.get_close_code()
				var reason = websocket.get_close_reason()
				print("WebSocket closed. Code: %d, Reason: %s" % [code, reason])
				set_process(false)
				emit_signal("disconnected_from_server")

func _handle_packet(packet: PackedByteArray):
	var json_string = packet.get_string_from_utf8()
	print("Raw packet received: ", json_string)
	
	var json = JSON.new()
	var parse_result = json.parse(json_string)
	
	if parse_result != OK:
		print("Error parsing JSON: ", json.get_error_message())
		return
	
	var message = json.data
	emit_signal("message_received", message)
	
	# Handle specific message types - using lowercase to match your server
	var msg_type = message.get("type", "")
	print("Message type: ", msg_type)
	
	match msg_type:
		# Connection messages
		"connected":  # This is the server's response to our connect message
			var server_client_id = message.get("client_id", "")
			if server_client_id != "":
				client_id = server_client_id  # Use server's ID if provided
			print("Client ID confirmed: ", client_id)
			emit_signal("connected_to_server")  # NOW emit the signal
		
		# Matchmaking messages
		"matchmaking_started":
			_change_scene("Matchmaking", message)
			
		"match_found":
			# Stay in matchmaking scene but update it with match info
			pass
			
		# Shop messages
		"initial_shop_ready":
			_change_scene("InitialShop", message)
		
		"shop_phase_start":
			_change_scene("ShopPhase", message)
			
		# Fight messages
		"fight_starting":
			_change_scene("Fighting", message)
			
		"batch_completed":
			# Stay in fighting scene, will transition to replay after
			pass
			
		# Replay messages
		"replay_data", "replay_next", "replay_previous":
			_change_scene("ReplayViewer", message)
			
		# Game over
		"game_over":
			_change_scene("GameOver", message)
			
		# Status messages (don't change scene)
		"options", "purchase_result", "refresh_result", "status", "error":
			pass
			
		"waiting_for_opponent", "opponent_ready", "opponent_disconnected":
			pass
		
		_:
			print("Unhandled message type: ", msg_type)

func _change_scene(scene_name: String, data: Dictionary):
	print("Requesting scene change to: ", scene_name)
	var game_state_manager = get_node_or_null("/root/Main/GameStateManager")
	if game_state_manager:
		game_state_manager.transition_to_scene(scene_name, data)
	else:
		push_error("GameStateManager not found!")

func send_message(message: Dictionary):
	if websocket.get_ready_state() == WebSocketPeer.STATE_OPEN:
		var json_string = JSON.stringify(message)
		print("Sending message: ", json_string)
		websocket.send_text(json_string)
		emit_signal("message_sent", message)
	else:
		push_error("Cannot send message - WebSocket not connected")

func get_client_id() -> String:
	return client_id
