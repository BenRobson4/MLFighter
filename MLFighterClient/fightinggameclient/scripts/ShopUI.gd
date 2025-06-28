extends Control

const SERVER_URL = "ws://localhost:8765"

var websocket: WebSocketPeer
var client_id: String
var current_options: Array = []
var purchased_items: Array = []
var client_gold: int = 0

@onready var title_label = $VBoxContainer/TitleLabel
@onready var gold_label = $VBoxContainer/GoldLabel
@onready var options_container = $VBoxContainer/ScrollContainer/OptionsContainer
@onready var status_label = $VBoxContainer/HBoxContainer/StatusLabel
@onready var refresh_button = $VBoxContainer/HBoxContainer/RefreshButton
@onready var purchases_button = $VBoxContainer/HBoxContainer/PurchasesButton

func _ready():
	# Generate unique client ID
	client_id = "client_" + str(Time.get_unix_time_from_system())
	
	# Setup UI
	title_label.text = "Shop - Connecting..."
	gold_label.text = "Gold: ---"
	refresh_button.text = "Refresh Shop"
	refresh_button.pressed.connect(_on_refresh_pressed)
	
	# Add purchases button if not in scene
	if not purchases_button:
		purchases_button = Button.new()
		purchases_button.text = "View Purchases"
		$VBoxContainer/HBoxContainer.add_child(purchases_button)
	purchases_button.pressed.connect(_on_purchases_pressed)
	
	# Initialize WebSocket
	websocket = WebSocketPeer.new()
	connect_to_server()

func connect_to_server():
	var err = websocket.connect_to_url(SERVER_URL)
	if err != OK:
		status_label.text = "Failed to connect"
		print("WebSocket connection error: ", err)
	else:
		status_label.text = "Connecting..."

func _process(_delta):
	if websocket.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		websocket.poll()
		
		var state = websocket.get_ready_state()
		
		if state == WebSocketPeer.STATE_OPEN:
			if title_label.text == "Shop - Connecting...":
				send_connect_message()
				title_label.text = "Shop - Connected"
				status_label.text = "Connected"
			
			while websocket.get_available_packet_count():
				var packet = websocket.get_packet()
				var message = packet.get_string_from_utf8()
				handle_server_message(message)
				
		elif state == WebSocketPeer.STATE_CLOSING:
			status_label.text = "Disconnecting..."
			
		elif state == WebSocketPeer.STATE_CLOSED:
			var code = websocket.get_close_code()
			var reason = websocket.get_close_reason()
			status_label.text = "Disconnected: %d - %s" % [code, reason]
			title_label.text = "Shop - Disconnected"

func send_connect_message():
	var message = {
		"type": "connect",
		"client_id": client_id
	}
	send_message(message)

func send_message(data: Dictionary):
	if websocket.get_ready_state() == WebSocketPeer.STATE_OPEN:
		var json_string = JSON.stringify(data)
		websocket.send_text(json_string)

func handle_server_message(message: String):
	var json = JSON.new()
	var parse_result = json.parse(message)
	
	if parse_result != OK:
		print("Failed to parse message: ", message)
		return
		
	var data = json.data
	
	match data.get("type"):
		"connected":
			print("Connected with ID: ", data.get("client_id"))
			client_gold = data.get("starting_gold", 0)
			update_gold_display()
			
		"options":
			var options_data = data.get("data", [])
			var refresh_cost = data.get("refresh_cost", 10)
			refresh_button.text = "Refresh Shop (%d gold)" % refresh_cost
			refresh_button.disabled = client_gold < refresh_cost
			client_gold = data.get("client_gold", client_gold)
			update_gold_display()
			display_options(options_data)
			
		"purchase_result":
			handle_purchase_result(data)
			
		"purchases_list":
			display_purchases_info(data)
			
		"refresh_result":
			var success = data.get("success", false)
			var msg = data.get("message", "")
			client_gold = data.get("remaining_gold", client_gold)
			update_gold_display()

			if success:
				status_label.text = msg
			else:
				status_label.text = "Refresh failed: " + msg
				
			refresh_button.disabled = false
			
		"status":
			client_gold = data.get("gold", 0)
			purchased_items = data.get("items_owned", [])
			update_gold_display()
			status_label.text = "Owned items: %d" % purchased_items.size()

func update_gold_display():
	gold_label.text = "Gold: %d" % client_gold

func display_options(options: Array):
	# Clear existing options
	for child in options_container.get_children():
		child.queue_free()
	
	current_options = options
	
	# Create button for each option
	for option in options:
		var button = create_option_button(option)
		options_container.add_child(button)
	
	status_label.text = "Showing %d items" %options.size()

func create_option_button(option: Dictionary) -> Control:
	var container = VBoxContainer.new()
	container.add_theme_constant_override("separation", 5)
	
	var button = Button.new()
	
	# Set button text
	var item_name = option.get("name", "Unknown")
	var cost = option.get("cost", 0)
	var description = option.get("description", "")
	var already_purchased = option.get("already_purchased", false)
	
	# Create rich text for the button
	var text = "%s - %d gold\n%s" % [item_name, cost, description]
	button.text = text
	
	# Style the button
	button.custom_minimum_size = Vector2(600, 80)
	button.add_theme_font_size_override("font_size", 14)
	
	# Handle purchase state
	if already_purchased:
		button.disabled = true
		button.text = "[OWNED] " + text
		button.modulate = Color(0.7, 1.0, 0.7)  # Green tint
	elif cost > client_gold:
		button.disabled = true
		button.text += "\n[INSUFFICIENT GOLD]"
		button.modulate = Color(1.0, 0.7, 0.7)  # Red tint
	elif not option.get("available", true):
		button.disabled = true
		button.text += "\n[UNAVAILABLE]"
	
	# Connect signal for purchase
	if not button.disabled and not already_purchased:
		var option_id = option.get("id", "")
		button.pressed.connect(_on_purchase_pressed.bind(option_id, cost))
		button.tooltip_text = "Click to purchase"
	
	container.add_child(button)
	
	# Add status label
	if already_purchased:
		var status = Label.new()
		status.text = "You own this item"
		status.add_theme_color_override("font_color", Color(0.5, 1.0, 0.5))
		container.add_child(status)
	
	return container

func _on_purchase_pressed(option_id: String, cost: int):
	print("Attempting to purchase: ", option_id, " for ", cost, " gold")
	
	var message = {
		"type": "purchase_option",
		"option_id": option_id,
		"cost": cost
	}
	send_message(message)
	status_label.text = "Processing purchase..."

func handle_purchase_result(data: Dictionary):
	var success = data.get("success", false)
	var option_id = data.get("option_id", "")
	var remaining_gold = data.get("remaining_gold", 0)
	var reason = data.get("reason", "")
	
	client_gold = remaining_gold
	update_gold_display()
	
	if success:
		status_label.text = "Purchased %s! Gold: %d" % [option_id, remaining_gold]
		purchased_items.append(option_id)
		
		# Visual feedback
		for child in options_container.get_children():
			child.modulate = Color(1.0, 1.0, 1.0, 0.8)
		
		# Brief delay then refresh
		await get_tree().create_timer(0.5).timeout
		for child in options_container.get_children():
			child.modulate = Color.WHITE
	else:
		status_label.text = "Purchase failed: %s" % reason

func _on_refresh_pressed():
	var message = {
		"type": "refresh_shop"
	}
	send_message(message)
	status_label.text = "Refreshing shop..."
	refresh_button.disabled = true

func _on_purchases_pressed():
	var message = {
		"type": "get_purchases"
	}
	send_message(message)
	status_label.text = "Fetching purchase history..."

func display_purchases_info(data: Dictionary):
	var purchases = data.get("purchases", [])
	var total_spent = data.get("total_spent", 0)
	var items_owned = data.get("items_owned", [])
	
	print("\n=== PURCHASE HISTORY ===")
	print("Total items owned: ", items_owned.size())
	print("Total gold spent: ", total_spent)
	print("Items owned: ", items_owned)
	print("\nPurchase details:")
	for purchase in purchases:
		print("  - %s: %d gold at %s" % [
			purchase.get("option_id", ""),
			purchase.get("cost", 0),
			purchase.get("timestamp", "")
		])
	print("========================\n")
	
	status_label.text = "Owned: %d items, Spent: %d gold" % [items_owned.size(), total_spent]

func _exit_tree():
	if websocket:
		websocket.close()
