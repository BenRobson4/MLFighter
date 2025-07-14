extends Control
class_name PlayerInventory

# Node references
@onready var inventory_grid = $MainContainer/ColorRect/InventorySection/InventoryGrid
@onready var fighter_display = $MainContainer/FighterSection/FighterDisplay 

# Inventory management
var item_slots: Array[ItemSlot] = []
var current_fighter_id: String = ""

# Network signals (to be connected to your network manager)
signal sell_item_requested(fighter_id: String, item_id: String)

func _ready():
	# Connect to FighterDataStore signals
	FighterDataStore.inventory_changed.connect(_on_inventory_changed)
	FighterDataStore.data_updated.connect(_on_fighter_data_updated)
	
	# Get the current active fighter
	current_fighter_id = FighterDataStore.active_fighter_id
	
	# Initialize item slots
	_setup_item_slots()
	
	# Load initial inventory
	_refresh_inventory_display()
	
	# Add to groups for easy access
	add_to_group("player_inventory")

func _setup_item_slots():
	"""Setup the 8 item slots and connect their signals"""
	item_slots.clear()
	
	# Get all ItemSlot nodes from the grid
	for child in inventory_grid.get_children():
		if child is ItemSlot:
			item_slots.append(child)
			
			# Set slot mode to inventory
			child.slot_mode = ItemSlot.SlotMode.INVENTORY
			
			# Connect signals
			if not child.is_connected("item_clicked", _on_item_clicked):
				child.item_clicked.connect(_on_item_clicked)
			if not child.is_connected("item_right_clicked", _on_item_right_clicked):
				child.item_right_clicked.connect(_on_item_right_clicked)
	
	# Ensure we have exactly 8 slots
	while item_slots.size() < 8:
		var new_slot = _create_item_slot()
		inventory_grid.add_child(new_slot)
		item_slots.append(new_slot)
	
	print("Initialized %d inventory slots" % item_slots.size())

func _create_item_slot() -> ItemSlot:
	"""Create a new ItemSlot instance"""
	var slot_scene = preload("res://scenes/ui/ItemSlot.tscn")  # Adjust path
	var slot = slot_scene.instantiate() as ItemSlot
	
	slot.slot_mode = ItemSlot.SlotMode.INVENTORY
	slot.item_clicked.connect(_on_item_clicked)
	slot.item_right_clicked.connect(_on_item_right_clicked)
	
	return slot

func _refresh_inventory_display():
	"""Refresh the inventory display from FighterDataStore"""
	if current_fighter_id.is_empty():
		print("No active fighter to display inventory for")
		return
	
	# Clear all slots first
	for slot in item_slots:
		slot.clear_slot()
	
	# Get fighter data
	var fighter_data = FighterDataStore.get_fighter_data(current_fighter_id)
	if fighter_data.is_empty():
		print("No data found for fighter: ", current_fighter_id)
		return
	
	var inventory = fighter_data.get("inventory", {})
	var slot_index = 0
	
	# Display weapons
	if inventory.has("weapons"):
		for weapon_data in inventory["weapons"]:
			if slot_index >= item_slots.size():
				break
			
			var item_data = _prepare_item_data(weapon_data, "weapons")
			item_slots[slot_index].set_item(item_data)
			
			# Show equipped state
			if weapon_data.get("equipped", false):
				item_slots[slot_index].is_selected = true
			
			slot_index += 1
	
	# Display armour
	if inventory.has("armour"):
		for armour_data in inventory["armour"]:
			if slot_index >= item_slots.size():
				break
			
			var item_data = _prepare_item_data(armour_data, "armour")
			item_slots[slot_index].set_item(item_data)
			
			# Show equipped state
			if armour_data.get("equipped", false):
				item_slots[slot_index].is_selected = true
			
			slot_index += 1
	
	# Note: Features, modifiers, etc. are not displayed in inventory slots
	# They affect stats but aren't visible items

func _prepare_item_data(inventory_item: Dictionary, category: String) -> Dictionary:
	"""Prepare item data for display in slot"""
	var item_data = {}
	
	# Get the item ID
	var item_id = inventory_item.get("item_id", "")
	
	# Load item data from ItemSlot's cache/loader
	if not item_id.is_empty():
		# Use the ItemSlot's static method to load item data
		var loaded_data = ItemSlot.new().load_item_data(item_id)
		item_data = loaded_data.duplicate()
	
	# Merge with inventory metadata
	if inventory_item.has("metadata"):
		for key in inventory_item["metadata"]:
			if not item_data.has(key):
				item_data[key] = inventory_item["metadata"][key]
	
	# Ensure essential fields
	item_data["item_id"] = item_id
	item_data["category"] = category
	item_data["equipped"] = inventory_item.get("equipped", false)
	
	return item_data

func _on_item_clicked(item_data: Dictionary):
	"""Handle left click - equip/unequip item"""
	if item_data.is_empty():
		return
	
	var item_id = item_data.get("item_id", "")
	if item_id.is_empty():
		return
	
	# Check current equipped state
	var is_equipped = _is_item_equipped(item_id)
	
	if is_equipped:
		# Unequip the item
		_unequip_item(item_id)
		print("Unequipped: ", item_id)
	else:
		# Equip the item (will auto-unequip others of same type)
		FighterDataStore.equip_item(current_fighter_id, item_id)
		print("Equipped: ", item_id)
	
	# The display will refresh automatically via the inventory_changed signal

func _on_item_right_clicked(item_data: Dictionary):
	"""Handle right click - sell item immediately"""
	if item_data.is_empty():
		return
	
	var item_id = item_data.get("item_id", "")
	if item_id.is_empty():
		return
	
	# Calculate sell price (typically half of purchase price)
	var base_cost = item_data.get("cost", 0)
	var sell_price = int(base_cost * 0.5)
	
	print("Selling %s for %d gold" % [item_id, sell_price])
	
	# Send sell request to server
	emit_signal("sell_item_requested", current_fighter_id, item_id)
	
	# The actual removal will happen when server confirms
	# For now, we could show a pending state
	_show_item_pending(item_id)

func _is_item_equipped(item_id: String) -> bool:
	"""Check if an item is currently equipped"""
	var fighter_data = FighterDataStore.get_fighter_data(current_fighter_id)
	var inventory = fighter_data.get("inventory", {})
	
	for category in inventory:
		for item in inventory[category]:
			if item.get("item_id") == item_id:
				return item.get("equipped", false)
	
	return false

func _unequip_item(item_id: String):
	"""Unequip an item"""
	var fighter_data = FighterDataStore.get_fighter_data(current_fighter_id)
	var inventory = fighter_data.get("inventory", {})
	
	# Find and unequip the item
	for category in inventory:
		for item in inventory[category]:
			if item.get("item_id") == item_id:
				item["equipped"] = false
				break
	
	# Update the inventory in FighterDataStore
	FighterDataStore.update_inventory(current_fighter_id, inventory)

func _show_item_pending(item_id: String):
	"""Show visual feedback that item is pending sale"""
	for slot in item_slots:
		if not slot.is_empty and slot.item_data.get("item_id") == item_id:
			# Add visual feedback - dim the item
			slot.modulate = Color(0.5, 0.5, 0.5, 0.5)
			slot.item_button.disabled = true
			break

func _clear_item_pending(item_id: String):
	"""Clear pending state for an item"""
	for slot in item_slots:
		if not slot.is_empty and slot.item_data.get("item_id") == item_id:
			# Restore normal appearance
			slot.modulate = Color.WHITE
			slot.item_button.disabled = false
			break

# Signal handlers

func _on_inventory_changed(fighter_id: String):
	"""Handle inventory changes from FighterDataStore"""
	if fighter_id == current_fighter_id:
		_refresh_inventory_display()

func _on_fighter_data_updated(fighter_id: String):
	"""Handle fighter data updates"""
	if fighter_id == current_fighter_id:
		_refresh_inventory_display()

# Public methods for external systems

func set_fighter(fighter_id: String):
	"""Set the current fighter to display"""
	current_fighter_id = fighter_id
	FighterDataStore.set_active_fighter(fighter_id)
	_refresh_inventory_display()

func on_sell_confirmed(item_id: String, gold_earned: int):
	"""Called when server confirms a sale"""
	print("Sale confirmed: %s sold for %d gold" % [item_id, gold_earned])
	
	# Clear pending state
	_clear_item_pending(item_id)
	
	# Remove item from inventory
	FighterDataStore.remove_item_from_inventory(current_fighter_id, item_id)
	
	# Update gold
	var current_gold = FighterDataStore.get_gold(current_fighter_id)
	FighterDataStore.update_gold(current_fighter_id, current_gold + gold_earned)
	
	# Show feedback
	_show_sale_feedback(item_id, gold_earned)

func on_sell_failed(item_id: String, reason: String):
	"""Called when server rejects a sale"""
	print("Sale failed for %s: %s" % [item_id, reason])
	
	# Clear pending state
	_clear_item_pending(item_id)
	
	# Show error message
	_show_error_message("Failed to sell item: " + reason)

func _show_sale_feedback(item_id: String, gold_earned: int):
	"""Show visual feedback for successful sale"""
	# Create a floating text showing gold earned
	var float_text = Label.new()
	float_text.text = "+%d gold" % gold_earned
	float_text.add_theme_color_override("font_color", Color.GOLD)
	float_text.add_theme_font_size_override("font_size", 24)
	
	# Position above the inventory
	add_child(float_text)
	float_text.position = inventory_grid.global_position + Vector2(inventory_grid.size.x / 2, -20)
	
	# Animate floating up and fading
	var tween = create_tween()
	tween.set_parallel(true)
	tween.tween_property(float_text, "position:y", float_text.position.y - 50, 1.0)
	tween.tween_property(float_text, "modulate:a", 0.0, 1.0)
	tween.chain().tween_callback(float_text.queue_free)

func _show_error_message(message: String):
	"""Show error message to player"""
	# You can implement a proper notification system here
	print("ERROR: ", message)
	
	# Simple error display
	var error_label = Label.new()
	error_label.text = message
	error_label.add_theme_color_override("font_color", Color.RED)
	error_label.add_theme_font_size_override("font_size", 18)
	
	add_child(error_label)
	error_label.position = inventory_grid.global_position + Vector2(0, inventory_grid.size.y + 10)
	
	# Auto-remove after 3 seconds
	await get_tree().create_timer(3.0).timeout
	if is_instance_valid(error_label):
		error_label.queue_free()

# Debug functions

func print_inventory_state():
	"""Print current inventory state for debugging"""
	print("=== Inventory State for %s ===" % current_fighter_id)
	var fighter_data = FighterDataStore.get_fighter_data(current_fighter_id)
	var inventory = fighter_data.get("inventory", {})
	
	for category in inventory:
		print("%s:" % category.capitalize())
		for item in inventory[category]:
			var equipped_str = " [EQUIPPED]" if item.get("equipped", false) else ""
			print("  - %s%s" % [item.get("item_id", "unknown"), equipped_str])
