extends Node

signal connected_to_server()
signal disconnected_from_server()
signal message_received(message: Dictionary)
signal message_sent(message: Dictionary)

var websocket: WebSocketPeer
var client_id: String = ""
var is_connected: bool = false

# References to active scenes
var active_shop_phase: ShopPhase
var active_player_inventory: PlayerInventory

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
	
	# Connect to GameStateManager scene_changed signal
	var game_state_manager = get_node_or_null("/root/Main/GameStateManager")
	if game_state_manager:
		game_state_manager.scene_changed.connect(_on_scene_changed)

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
			
		"options":
			_change_scene("ShopPhase", message)
			
		# Shop messages
		"initial_shop_ready":
			_change_scene("InitialShop", message)
		
		"shop_phase_start":
			_change_scene("ShopPhase", message)
		
		# Purchase/Sell results
		"purchase_result":
			_handle_purchase_result(message)
		
		"sell_result":
			_handle_sell_result(message)
		
		# Shop refresh result
		"refresh_result":
			_handle_refresh_result(message)
			
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
		"status", "error":
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

# ===== NEW METHODS FOR SHOP AND INVENTORY INTEGRATION =====

func _on_scene_changed(scene_name: String):
	"""Handle scene changes to connect signals from new scenes"""
	print("Scene changed to: ", scene_name)
	
	# Wait for scene to be fully loaded
	await get_tree().process_frame
	
	# Connect to ShopPhase signals
	if scene_name == "ShopPhase":
		_connect_shop_signals()
	
	# Find and connect to PlayerInventory if it exists in any scene
	_connect_inventory_signals()

func _connect_shop_signals():
	"""Connect to ShopPhase signals"""
	# Find the active ShopPhase instance
	active_shop_phase = get_tree().get_first_node_in_group("shop_phase")
	if active_shop_phase:
		print("Found ShopPhase, connecting signals")
		
		# Disconnect existing connections if any
		if active_shop_phase.is_connected("buy_item_requested", _on_buy_item_requested):
			active_shop_phase.buy_item_requested.disconnect(_on_buy_item_requested)
		if active_shop_phase.is_connected("refresh_shop_requested", _on_refresh_shop_requested):
			active_shop_phase.refresh_shop_requested.disconnect(_on_refresh_shop_requested)
		if active_shop_phase.is_connected("finish_shop_requested", _on_finish_shop_requested):
			active_shop_phase.finish_shop_requested.disconnect(_on_finish_shop_requested)
		
		# Connect signals
		active_shop_phase.buy_item_requested.connect(_on_buy_item_requested)
		active_shop_phase.refresh_shop_requested.connect(_on_refresh_shop_requested)
		active_shop_phase.finish_shop_requested.connect(_on_finish_shop_requested)
	else:
		print("ShopPhase not found")

func _connect_inventory_signals():
	"""Connect to PlayerInventory signals"""
	# Find the active PlayerInventory instance
	active_player_inventory = get_tree().get_first_node_in_group("player_inventory")
	if active_player_inventory:
		print("Found PlayerInventory, connecting signals")
		
		# Disconnect existing connections if any
		if active_player_inventory.is_connected("sell_item_requested", _on_sell_item_requested):
			active_player_inventory.sell_item_requested.disconnect(_on_sell_item_requested)
		
		# Connect signals
		active_player_inventory.sell_item_requested.connect(_on_sell_item_requested)
	else:
		print("PlayerInventory not found")

# ===== SIGNAL HANDLERS =====

func _on_buy_item_requested(fighter_id: String, item_id: String, auto_equip: bool):
	"""Handle buy item request from ShopPhase"""
	print("Buy item requested: ", item_id, " for fighter: ", fighter_id, " auto-equip: ", auto_equip)
	
	# Construct purchase message
	var message = {
		"type": "purchase_option",
		"option_id": item_id,
		"auto_equip": auto_equip
	}
	
	# Send to server
	send_message(message)

func _on_sell_item_requested(fighter_id: String, item_id: String):
	"""Handle sell item request from PlayerInventory"""
	print("Sell item requested: ", item_id, " for fighter: ", fighter_id)
	
	# Construct sell message (similar structure to purchase)
	var message = {
		"type": "sell_item",
		"item_id": item_id,
		"fighter_id": fighter_id
	}
	
	# Send to server
	send_message(message)

func _on_refresh_shop_requested(fighter_id: String):
	"""Handle refresh shop request"""
	print("Refresh shop requested for fighter: ", fighter_id)
	
	var message = {
		"type": "refresh_shop"
	}
	
	# Send to server
	send_message(message)

func _on_finish_shop_requested(fighter_id: String):
	"""Handle finish shop request"""
	print("Finish shop requested for fighter: ", fighter_id)
	
	var message = {
		"type": "shop_phase_complete"
	}
	
	# Send to server
	send_message(message)

# ===== SERVER RESPONSE HANDLERS =====

func _handle_purchase_result(message: Dictionary):
	"""Handle purchase result from server"""
	var success = message.get("success", false)
	var item_id = message.get("item_id", "")
	var auto_equip = message.get("auto_equip", false)
	var cost = message.get("cost", 0)
	var reason = message.get("reason", "Unknown error")
	
	print("Purchase result: ", "Success" if success else "Failed", " for item: ", item_id)
	
	# Forward to ShopPhase if available
	if active_shop_phase and is_instance_valid(active_shop_phase):
		if success:
			active_shop_phase.on_buy_confirmed(item_id, auto_equip, cost)
		else:
			active_shop_phase.on_buy_failed(item_id, reason)
	else:
		print("ShopPhase not available to handle purchase result")

func _handle_sell_result(message: Dictionary):
	"""Handle sell result from server"""
	var success = message.get("success", false)
	var item_id = message.get("item_id", "")
	var gold_earned = message.get("gold_earned", 0)
	var reason = message.get("reason", "Unknown error")
	
	print("Sell result: ", "Success" if success else "Failed", " for item: ", item_id)
	
	# Forward to PlayerInventory if available
	if active_player_inventory and is_instance_valid(active_player_inventory):
		if success:
			active_player_inventory.on_sell_confirmed(item_id, gold_earned)
		else:
			active_player_inventory.on_sell_failed(item_id, reason)
	else:
		print("PlayerInventory not available to handle sell result")

func _handle_refresh_result(message: Dictionary):
	"""Handle refresh shop result from server"""
	var success = message.get("success", false)
	
	print("Refresh result: ", "Success" if success else "Failed")
	
	# Forward to ShopPhase if available
	if active_shop_phase and is_instance_valid(active_shop_phase):
		if success:
			active_shop_phase.on_shop_refreshed(message)
		else:
			active_shop_phase.on_buy_failed("refresh", message.get("message", "Refresh failed"))
	else:
		print("ShopPhase not available to handle refresh result")
