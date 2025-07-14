extends Control
class_name ShopPhase

# Network signals - consistent with inventory signals
signal buy_item_requested(fighter_id: String, item_id: String, auto_equip: bool)
signal refresh_shop_requested(fighter_id: String)
signal finish_shop_requested(fighter_id: String)

# Node references
@onready var item_container = $VBoxContainer/ItemSection/ItemContainer
@onready var gold_label = $VBoxContainer/HeaderPanel/GoldContainer/GoldLabel
@onready var phase_label = $VBoxContainer/HeaderPanel/PhaseLabel
@onready var refresh_button = $VBoxContainer/FooterPanel/RefreshButton
@onready var finish_shop_button = $VBoxContainer/FooterPanel/FinishShopButton

# Shop state
var current_fighter_id: String = ""
var shop_phase: String = ""
var available_items: Array = []
var item_slots: Array[ItemSlot] = []

func _ready():
	print("ShopPhase _ready() called")
	
	# Connect to FighterDataStore signals
	FighterDataStore.data_updated.connect(_on_fighter_data_updated)
	
	# Get current active fighter
	current_fighter_id = FighterDataStore.active_fighter_id
	print("Current fighter ID: ", current_fighter_id)
	
	# Collect all ItemSlot nodes
	_collect_item_slots()
	
	# Connect buttons
	refresh_button.pressed.connect(_on_refresh_pressed)
	finish_shop_button.pressed.connect(_on_finish_shop_pressed)
	
	# Connect to each item slot
	for slot in item_slots:
		slot.slot_mode = ItemSlot.SlotMode.SHOP
		slot.item_clicked.connect(_on_item_clicked)
		slot.item_right_clicked.connect(_on_item_right_clicked)
	
	# Add to group for easy access
	add_to_group("shop_phase")
	print("ShopPhase added to 'shop_phase' group")

func _collect_item_slots():
	"""Find all ItemSlot nodes in the scene"""
	item_slots.clear()
	
	# Get slots from item container
	if item_container:
		for child in item_container.get_children():
			if child is ItemSlot:
				item_slots.append(child)
	
	print("Found %d item slots" % item_slots.size())


func _test_with_mock_data():
	"""Initialize shop with mock data for testing"""
	print("=== TESTING MODE: Using mock data ===")
	
	var mock_message = {
		"type": "options",
		"phase": "initial_items",
		"client_gold": 1000.0,
		"message": "Choose your starting items",
		"data": [
			{
				"id": "weapons_sword_iron_sword",
				"name": "Iron Sword",
				"description": "A basic iron sword",
				"cost": 100.0,
				"category": "weapons",
				"subcategory": "sword",
				"stock": 10.0,
				"properties": {
					"name": "Iron Sword",
					"description": "A basic iron sword",
					"gravity_modifier": 1.0,
					"jump_force_modifier": 0.0,
					"move_speed_modifier": -5.0,
					"x_attack_range_modifier": 15.0,
					"y_attack_range_modifier": 10.0,
					"attack_damage_modifier": 10.0,
					"attack_cooldown_modifier": 0.0,
					"rarity": "common",
					"cost": 100.0,
					"stock": 10.0
				},
				"already_purchased": false,
				"can_afford": true,
				"stock_remaining": 10.0
			},
			{
				"id": "weapons_sword_steel_sword",
				"name": "Steel Sword",
				"description": "A sharp steel sword",
				"cost": 250.0,
				"category": "weapons",
				"subcategory": "sword",
				"stock": 5.0,
				"properties": {
					"name": "Steel Sword",
					"description": "A sharp steel sword",
					"gravity_modifier": 1.0,
					"jump_force_modifier": 0.0,
					"move_speed_modifier": -8.0,
					"x_attack_range_modifier": 20.0,
					"y_attack_range_modifier": 12.0,
					"attack_damage_modifier": 20.0,
					"attack_cooldown_modifier": 0.1,
					"rarity": "uncommon",
					"cost": 250.0,
					"stock": 5.0
				},
				"already_purchased": false,
				"can_afford": true,
				"stock_remaining": 5.0
			},
			# ... more mock items ...
		]
	}
	
	# Initialize with mock data
	initialize(mock_message)

func initialize(data: Dictionary):
	"""Initialize shop with data from server message"""
	print("ShopPhase initialize() called with data")
	print("Data type: ", data.get("type", "MISSING TYPE"))
	print("Data phase: ", data.get("phase", "MISSING PHASE"))
	print("Data message: ", data.get("message", "MISSING MESSAGE"))
	print("Data items count: ", data.get("data", []).size())
	
	# Clear any previous state
	available_items.clear()
	
	# The data parameter is the full message from server
	shop_phase = data.get("phase", "")
	available_items = data.get("data", [])
	var message = data.get("message", "Choose your items")
	
	# Use client_gold from server data if available
	var server_gold = data.get("client_gold", -1)
	var current_gold = server_gold if server_gold >= 0 else FighterDataStore.get_gold(current_fighter_id)
	
	print("Shop phase: ", shop_phase)
	print("Available items: ", available_items.size())
	print("Current gold: ", current_gold)
	
	# Update UI
	_update_gold_display(current_gold)
	_update_phase_display(message)
	
	# Populate item slots
	_populate_item_slots()
	
	print("ShopPhase initialization complete")
	
func _populate_item_slots():
	"""Fill item slots with available items"""
	print("Populating item slots")
	print("Available items: ", available_items.size())
	print("Item slots: ", item_slots.size())
	
	# Debug: Print all available items
	for i in range(available_items.size()):
		var item = available_items[i]
		print("Item %d: id=%s, name=%s" % [i, item.get("id", "NO_ID"), item.get("name", "NO_NAME")])
	
	# Clear all slots first
	for slot in item_slots:
		slot.clear_slot()
	
	# Get current gold for affordability check
	var current_gold = FighterDataStore.get_gold(current_fighter_id)
	
	# Populate with available items
	var slot_index = 0
	for item_data in available_items:
		if slot_index >= item_slots.size():
			print("Warning: More items (%d) than slots (%d)" % [available_items.size(), item_slots.size()])
			break
			
		var slot = item_slots[slot_index]
		
		# The server sends the item with an "id" field that contains the full item ID
		var item_id = item_data.get("id", "")
		print("Setting slot %d to item: %s" % [slot_index, item_id])
		
		var cost = item_data.get("cost", 0)
		
		# Prepare item data for slot
		var slot_data = {
			"item_id": item_id,
			"name": item_data.get("name", "Unknown"),
			"description": item_data.get("description", ""),
			"cost": cost,
			"category": item_data.get("category", ""),
			"subcategory": item_data.get("subcategory", ""),
			"stock": item_data.get("stock_remaining", 0),
			"server_data": item_data  # Keep original server data
		}
		
		# Merge properties from server into slot_data
		if item_data.has("properties"):
			for key in item_data["properties"]:
				if not slot_data.has(key):
					slot_data[key] = item_data["properties"][key]
		
		# Set the item - ItemSlot will load additional data from JSON
		slot.set_item(slot_data)
		
		# Calculate affordability and availability
		var can_afford = cost <= current_gold
		var already_purchased = item_data.get("already_purchased", false)
		var stock_remaining = item_data.get("stock_remaining", 0)
		
		# Visual feedback for affordability/availability
		if not can_afford:
			slot.modulate = Color(0.7, 0.7, 0.7)  # Darken if can't afford
			slot.item_button.disabled = true
			_add_status_indicator(slot, "Can't Afford", Color(1, 0.3, 0.3))
		elif already_purchased:
			slot.modulate = Color(0.5, 0.5, 0.5)  # Darken if already purchased
			slot.item_button.disabled = true
			_add_status_indicator(slot, "Owned", Color(0.3, 1, 0.3))
		elif stock_remaining <= 0:
			slot.modulate = Color(0.5, 0.5, 0.5)  # Darken if out of stock
			slot.item_button.disabled = true
			_add_status_indicator(slot, "Out of Stock", Color(0.5, 0.5, 0.5))
		
		slot_index += 1

func _add_status_indicator(slot: ItemSlot, text: String, color: Color):
	"""Add visual indicator for item status"""
	var label = Label.new()
	label.text = text
	label.add_theme_color_override("font_color", color)
	label.add_theme_font_size_override("font_size", 12)
	label.position = Vector2(5, 5)
	label.name = "StatusIndicator"  # Name for easy reference
	
	# Remove existing indicator if present
	var existing = slot.get_node_or_null("StatusIndicator")
	if existing:
		existing.queue_free()
	
	slot.add_child(label)

func _on_item_clicked(item_data: Dictionary):
	"""Handle left click - buy item"""
	if item_data.is_empty():
		return
	
	var item_id = item_data.get("item_id", "")
	var cost = item_data.get("cost", 0)
	var stock = item_data.get("stock", 0)
	var category = item_data.get("category", "")
	
	# Check if item is in stock
	if stock <= 0:
		_show_error_message("Item is out of stock!")
		return
	
	# Check if player has enough gold
	var player_gold = FighterDataStore.get_gold(current_fighter_id)
	if player_gold < cost:
		_show_error_message("Not enough gold! Need %d, have %d" % [cost, player_gold])
		return
	
	# Send purchase request (without auto-equip)
	emit_signal("buy_item_requested", current_fighter_id, item_id, false)
	
	# Show pending state
	_show_item_pending(item_id)

func _on_item_right_clicked(item_data: Dictionary):
	"""Handle right click - buy and equip item"""
	if item_data.is_empty():
		return
	
	var item_id = item_data.get("item_id", "")
	var cost = item_data.get("cost", 0)
	var stock = item_data.get("stock", 0)
	var category = item_data.get("category", "")
	
	# Check if item can be equipped
	if not category in ["weapons", "armour"]:
		_show_error_message("This item cannot be equipped!")
		return
	
	# Check if item is in stock
	if stock <= 0:
		_show_error_message("Item is out of stock!")
		return
	
	# Check if player has enough gold
	var player_gold = FighterDataStore.get_gold(current_fighter_id)
	if player_gold < cost:
		_show_error_message("Not enough gold! Need %d, have %d" % [cost, player_gold])
		return
	
	# Send purchase request with auto-equip flag
	emit_signal("buy_item_requested", current_fighter_id, item_id, true)
	
	# Show pending state
	_show_item_pending(item_id)

func _on_refresh_pressed():
	"""Handle refresh button press"""
	emit_signal("refresh_shop_requested", current_fighter_id)
	
	# Disable button while waiting for response
	refresh_button.disabled = true
	
	# Show loading state
	_show_info_message("Refreshing shop...")

func _on_finish_shop_pressed():
	"""Handle finish shop button press"""
	emit_signal("finish_shop_requested", current_fighter_id)
	
	# Disable button while waiting for response
	finish_shop_button.disabled = true
	
	# Show loading state
	_show_info_message("Finishing shopping...")

func _show_item_pending(item_id: String):
	"""Show visual feedback that item purchase is pending"""
	for slot in item_slots:
		if not slot.is_empty and slot.item_data.get("item_id") == item_id:
			# Add visual feedback - dim the item
			slot.modulate = Color(0.5, 0.5, 0.5, 0.5)
			slot.item_button.disabled = true
			_add_status_indicator(slot, "Pending", Color(1, 0.8, 0.2))
			break

func _clear_item_pending(item_id: String):
	"""Clear pending state for an item"""
	for slot in item_slots:
		if not slot.is_empty and slot.item_data.get("item_id") == item_id:
			# Restore normal appearance
			slot.modulate = Color.WHITE
			slot.item_button.disabled = false
			
			# Remove status indicator
			var indicator = slot.get_node_or_null("StatusIndicator")
			if indicator:
				indicator.queue_free()
			break

func _update_gold_display(gold: int):
	"""Update gold label"""
	if gold_label:
		gold_label.text = "Gold: %d" % gold

func _update_phase_display(message: String):
	"""Update phase label"""
	if phase_label:
		phase_label.text = message

func _show_error_message(message: String):
	"""Show error message to player"""
	print("ERROR: ", message)
	
	# Simple error display
	var error_label = Label.new()
	error_label.text = message
	error_label.add_theme_color_override("font_color", Color.RED)
	error_label.add_theme_font_size_override("font_size", 18)
	
	add_child(error_label)
	error_label.position = Vector2(20, get_viewport_rect().size.y - 100)
	
	# Auto-remove after 3 seconds
	await get_tree().create_timer(3.0).timeout
	if is_instance_valid(error_label):
		error_label.queue_free()

func _show_info_message(message: String):
	"""Show info message to player"""
	print("INFO: ", message)
	
	# Simple info display
	var info_label = Label.new()
	info_label.text = message
	info_label.add_theme_color_override("font_color", Color.WHITE)
	info_label.add_theme_font_size_override("font_size", 18)
	
	add_child(info_label)
	info_label.position = Vector2(20, get_viewport_rect().size.y - 70)
	
	# Auto-remove after 2 seconds
	await get_tree().create_timer(2.0).timeout
	if is_instance_valid(info_label):
		info_label.queue_free()

# Response handlers

func on_buy_confirmed(item_id: String, auto_equip: bool, cost: int):
	"""Called when server confirms a purchase"""
	print("Purchase confirmed: %s for %d gold, auto-equip: %s" % [item_id, cost, str(auto_equip)])
	
	# Clear pending state
	_clear_item_pending(item_id)
	
	# Update gold in FighterDataStore
	var current_gold = FighterDataStore.get_gold(current_fighter_id)
	FighterDataStore.update_gold(current_fighter_id, current_gold - cost)
	
	# Find the full item data from available_items
	var item_data = {}
	for available_item in available_items:
		if available_item.get("id", "") == item_id:
			item_data = available_item.duplicate()
			break
	
	# If item not found in available_items, try to load it
	if item_data.is_empty():
		var item_slot = ItemSlot.new()
		item_data = item_slot.load_item_data(item_id)
		item_data["item_id"] = item_id
		item_slot.queue_free()  # Clean up temporary object
	
	# Ensure item_id is properly set
	item_data["item_id"] = item_id
	
	# Extract category from item_id if not present
	if not item_data.has("category") or item_data["category"].is_empty():
		var parts = item_id.split("_")
		if parts.size() >= 2:
			if parts[0] == "learning" and parts[1] == "modifiers":
				item_data["category"] = "learning_modifiers"
			elif parts[0] == "reward" and parts[1] == "modifiers":
				item_data["category"] = "reward_modifiers"
			else:
				item_data["category"] = parts[0]
	
	print("Adding item to inventory with category: ", item_data.get("category", "MISSING CATEGORY"))
	
	# Add item to inventory
	FighterDataStore.add_item_to_inventory(current_fighter_id, item_data, auto_equip)
	
	# Update gold display
	_update_gold_display(current_gold - cost)
	
	# Show feedback
	_show_purchase_feedback(item_id, cost)
	
	# Update item availability in shop
	_update_item_availability(item_id)

func on_buy_failed(item_id: String, reason: String):
	"""Called when server rejects a purchase"""
	print("Purchase failed for %s: %s" % [item_id, reason])
	
	# Clear pending state
	_clear_item_pending(item_id)
	
	# Show error message
	_show_error_message("Failed to buy item: " + reason)

func on_shop_refreshed(shop_data: Dictionary):
	"""Called when shop is refreshed"""
	print("Shop refreshed")
	
	# Re-enable refresh button
	refresh_button.disabled = false
	
	# Initialize with new data
	initialize(shop_data)
	
	# Show confirmation
	_show_info_message("Shop refreshed!")

func on_shop_finished():
	"""Called when shop is finished"""
	print("Shop finished")
	
	# Hide shop or transition to next scene
	# This depends on your game flow
	queue_free()

# FighterDataStore signal handlers

func _on_fighter_data_updated(fighter_id: String):
	"""Handle fighter data updates"""
	if fighter_id == current_fighter_id:
		# Update gold display
		var current_gold = FighterDataStore.get_gold(current_fighter_id)
		_update_gold_display(current_gold)

# Helper methods

func _update_item_availability(item_id: String):
	"""Update item availability in shop after purchase"""
	# Find the item in available_items
	for i in range(available_items.size()):
		if available_items[i].get("id") == item_id:
			# Reduce stock
			var stock = available_items[i].get("stock_remaining", 0)
			available_items[i]["stock_remaining"] = max(0, stock - 1)
			
			# Mark as already purchased if appropriate
			if available_items[i].get("unique", false):
				available_items[i]["already_purchased"] = true
			
			break
	
	# Refresh display
	_populate_item_slots()

func _show_purchase_feedback(item_id: String, cost: int):
	"""Show visual feedback for successful purchase"""
	# Create a floating text showing purchase
	var float_text = Label.new()
	float_text.text = "Purchased! -%d gold" % cost
	float_text.add_theme_color_override("font_color", Color.GOLD)
	float_text.add_theme_font_size_override("font_size", 24)
	
	# Position above the gold label
	add_child(float_text)
	float_text.position = gold_label.global_position + Vector2(0, -30)
	
	# Animate floating up and fading
	var tween = create_tween()
	tween.set_parallel(true)
	tween.tween_property(float_text, "position:y", float_text.position.y - 50, 1.0)
	tween.tween_property(float_text, "modulate:a", 0.0, 1.0)
	tween.chain().tween_callback(float_text.queue_free)

func set_fighter(fighter_id: String):
	"""Set the current fighter for the shop"""
	current_fighter_id = fighter_id
	
	# Update gold display
	var current_gold = FighterDataStore.get_gold(current_fighter_id)
	_update_gold_display(current_gold)
