extends Node

signal connected_to_server()
signal disconnected_from_server()
signal replay_received(replay_json)

var client: StreamPeerTCP
var is_connected: bool = false
var receive_buffer: String = ""

func connect_to_server(host: String, port: int) -> bool:
	"""Connect to the game server"""
	client = StreamPeerTCP.new()
	var result = client.connect_to_host(host, port)
	
	if result == OK:
		is_connected = true
		emit_signal("connected_to_server")
		return true
	else:
		print("Failed to connect to server")
		return false

func request_replay(replay_id: String = ""):
	"""Request a replay from the server"""
	if not is_connected:
		print("Not connected to server")
		return
	
	var request = {
		"type": "replay_request",
		"replay_id": replay_id
	}
	
	var json_string = JSON.stringify(request)
	client.put_string(json_string + "\n")

func _process(_delta):
	"""Process incoming network data"""
	if not is_connected or not client:
		return
	
	if client.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		var available = client.get_available_bytes()
		if available > 0:
			var data = client.get_string(available)
			receive_buffer += data
			_process_buffer()
	else:
		is_connected = false
		emit_signal("disconnected_from_server")

func _process_buffer():
	"""Process received data buffer"""
	while "\n" in receive_buffer:
		var line_end = receive_buffer.find("\n")
		var line = receive_buffer.substr(0, line_end)
		receive_buffer = receive_buffer.substr(line_end + 1)
		
		if line.length() > 0:
			_handle_message(line)

func _handle_message(message: String):
	"""Handle received message from server"""
	var json = JSON.new()
	var parse_result = json.parse(message)
	
	if parse_result == OK:
		var data = json.data
		if data.has("type") and data["type"] == "replay_data":
			emit_signal("replay_received", JSON.stringify(data["replay"]))
