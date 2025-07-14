extends Node

signal data_updated(fighter_id: String)
signal inventory_changed(fighter_id: String)
signal stats_changed(fighter_id: String)

# Storage for all fighter data
var fighters_data: Dictionary = {}

# Current active fighter
var active_fighter_id: String = ""

# Data structure for each fighter:
# {
#   "fighter_id": "aggressive",
#   "base_stats": {...},
#   "inventory": {
#     "weapons": [...],
#     "armour": [...],
#     "features": [...],
#     "modifiers": [...]
#   },
#   "learning_parameters": {
#     "epsilon": 0.5,
#     "decay": 0.005,
#     "learning_rate": 0.002
#   },
#   "calculated_stats": {...},
#   "metadata": {
#     "last_updated": timestamp,
#     "wins": 0,
#     "losses": 0,
#     "gold": 1000
#   }
# }

func _ready():
	print("FighterDataStore initialized")

## Core Functions

func set_fighter_data(fighter_id: String, data: Dictionary) -> void:
	"""Set complete fighter data"""
	fighters_data[fighter_id] = data
	fighters_data[fighter_id]["fighter_id"] = fighter_id
	fighters_data[fighter_id]["metadata"]["last_updated"] = Time.get_ticks_msec()
	
	emit_signal("data_updated", fighter_id)
	
	# Update StatManager if this is the active fighter
	if fighter_id == active_fighter_id:
		_sync_with_stat_manager()

func get_fighter_data(fighter_id: String) -> Dictionary:
	"""Get complete fighter data"""
	if fighters_data.has(fighter_id):
		return fighters_data[fighter_id].duplicate(true)
	return {}

func set_active_fighter(fighter_id: String) -> void:
	"""Set the currently active fighter"""
	active_fighter_id = fighter_id
	_sync_with_stat_manager()

func get_active_fighter_data() -> Dictionary:
	"""Get data for the currently active fighter"""
	return get_fighter_data(active_fighter_id)

## Inventory Management

func update_inventory(fighter_id: String, inventory: Dictionary) -> void:
	"""Update fighter's inventory"""
	if not fighters_data.has(fighter_id):
		fighters_data[fighter_id] = _create_empty_fighter_data(fighter_id)
	
	fighters_data[fighter_id]["inventory"] = inventory
	fighters_data[fighter_id]["metadata"]["last_updated"] = Time.get_ticks_msec()
	
	emit_signal("inventory_changed", fighter_id)
	
	if fighter_id == active_fighter_id:
		_sync_with_stat_manager()

func add_item_to_inventory(fighter_id: String, item_data: Dictionary, equip: bool = false) -> void:
	"""Add a single item to inventory"""
	if not fighters_data.has(fighter_id):
		fighters_data[fighter_id] = _create_empty_fighter_data(fighter_id)
	
	var inventory = fighters_data[fighter_id]["inventory"]
	var category = item_data.get("category", "")
	
	# Determine inventory category
	var inv_category = ""
	match category:
		"weapons":
			inv_category = "weapons"
		"armour":
			inv_category = "armour"
		"features":
			inv_category = "features"
		"learning_modifiers", "reward_modifiers":
			inv_category = "modifiers"
	
	if inv_category.is_empty():
		push_error("Unknown item category: " + category)
		return
	
	# Ensure category exists
	if not inventory.has(inv_category):
		inventory[inv_category] = []
	
	# Create inventory item
	var inv_item = {
		"item_id": item_data.get("item_id", ""),
		"equipped": equip,
		"purchase_time": Time.get_ticks_msec(),
		"metadata": item_data
	}
	
	# If equipping weapon/armour, unequip others
	if equip and inv_category in ["weapons", "armour"]:
		for item in inventory[inv_category]:
			item["equipped"] = false
	
	inventory[inv_category].append(inv_item)
	
	emit_signal("inventory_changed", fighter_id)
	
	if fighter_id == active_fighter_id:
		_sync_with_stat_manager()

func remove_item_from_inventory(fighter_id: String, item_id: String) -> bool:
	"""Remove item from inventory. Returns true if successful"""
	if not fighters_data.has(fighter_id):
		return false
	
	var inventory = fighters_data[fighter_id]["inventory"]
	
	for category in inventory:
		for i in range(inventory[category].size() - 1, -1, -1):
			if inventory[category][i]["item_id"] == item_id:
				inventory[category].remove_at(i)
				emit_signal("inventory_changed", fighter_id)
				
				if fighter_id == active_fighter_id:
					_sync_with_stat_manager()
				return true
	
	return false

func equip_item(fighter_id: String, item_id: String) -> void:
	"""Equip an item (unequips others of same type)"""
	if not fighters_data.has(fighter_id):
		return
	
	var inventory = fighters_data[fighter_id]["inventory"]
	var item_found = false
	var item_category = ""
	
	# Find the item and its category
	for category in inventory:
		for item in inventory[category]:
			if item["item_id"] == item_id:
				item_found = true
				item_category = category
				break
		if item_found:
			break
	
	if not item_found:
		return
	
	# Unequip all items in category if weapon/armour
	if item_category in ["weapons", "armour"]:
		for item in inventory[item_category]:
			item["equipped"] = false
	
	# Equip the specific item
	for item in inventory[item_category]:
		if item["item_id"] == item_id:
			item["equipped"] = true
			break
	
	emit_signal("inventory_changed", fighter_id)
	
	if fighter_id == active_fighter_id:
		_sync_with_stat_manager()

## Stats Management

func update_base_stats(fighter_id: String, base_stats: Dictionary) -> void:
	"""Update fighter's base stats"""
	if not fighters_data.has(fighter_id):
		fighters_data[fighter_id] = _create_empty_fighter_data(fighter_id)
	
	fighters_data[fighter_id]["base_stats"] = base_stats
	emit_signal("stats_changed", fighter_id)
	
	if fighter_id == active_fighter_id:
		_sync_with_stat_manager()

func update_learning_parameters(fighter_id: String, params: Dictionary) -> void:
	"""Update learning parameters"""
	if not fighters_data.has(fighter_id):
		fighters_data[fighter_id] = _create_empty_fighter_data(fighter_id)
	
	fighters_data[fighter_id]["learning_parameters"] = params
	emit_signal("stats_changed", fighter_id)
	
	if fighter_id == active_fighter_id:
		_sync_with_stat_manager()

func update_calculated_stats(fighter_id: String, stats: Dictionary) -> void:
	"""Store calculated stats (from StatManager)"""
	if not fighters_data.has(fighter_id):
		return
	
	fighters_data[fighter_id]["calculated_stats"] = stats
	fighters_data[fighter_id]["metadata"]["last_updated"] = Time.get_ticks_msec()

## Metadata Management

func update_metadata(fighter_id: String, key: String, value) -> void:
	"""Update metadata value"""
	if not fighters_data.has(fighter_id):
		fighters_data[fighter_id] = _create_empty_fighter_data(fighter_id)
	
	fighters_data[fighter_id]["metadata"][key] = value

func get_metadata(fighter_id: String, key: String, default_value = null):
	"""Get metadata value"""
	if fighters_data.has(fighter_id) and fighters_data[fighter_id]["metadata"].has(key):
		return fighters_data[fighter_id]["metadata"][key]
	return default_value

func update_gold(fighter_id: String, gold: int) -> void:
	"""Update fighter's gold"""
	update_metadata(fighter_id, "gold", gold)

func get_gold(fighter_id: String) -> int:
	"""Get fighter's gold"""
	return get_metadata(fighter_id, "gold", 0)

## Utility Functions

func clear_all_data() -> void:
	"""Clear all stored fighter data"""
	fighters_data.clear()
	active_fighter_id = ""
	print("All fighter data cleared")

func clear_fighter_data(fighter_id: String) -> void:
	"""Clear data for specific fighter"""
	if fighters_data.has(fighter_id):
		fighters_data.erase(fighter_id)
		if active_fighter_id == fighter_id:
			active_fighter_id = ""

func has_fighter_data(fighter_id: String) -> bool:
	"""Check if fighter data exists"""
	return fighters_data.has(fighter_id)

func get_all_fighter_ids() -> Array:
	"""Get list of all stored fighter IDs"""
	return fighters_data.keys()

func _create_empty_fighter_data(fighter_id: String) -> Dictionary:
	"""Create empty fighter data structure"""
	return {
		"fighter_id": fighter_id,
		"base_stats": {},
		"inventory": {
			"weapons": [],
			"armour": [],
			"features": [],
			"modifiers": []
		},
		"learning_parameters": {
			"epsilon": 0.5,
			"decay": 0.005,
			"learning_rate": 0.002
		},
		"calculated_stats": {},
		"metadata": {
			"last_updated": Time.get_ticks_msec(),
			"wins": 0,
			"losses": 0,
			"gold": 1000
		}
	}

func _sync_with_stat_manager() -> void:
	"""Sync active fighter data with StatManager"""
	if active_fighter_id.is_empty() or not fighters_data.has(active_fighter_id):
		return
	
	var data = fighters_data[active_fighter_id]
	
	# Convert inventory format for StatManager
	var stat_manager_inventory = {
		"weapons": [],
		"armour": []
	}
	
	if data["inventory"].has("weapons"):
		for weapon in data["inventory"]["weapons"]:
			stat_manager_inventory["weapons"].append({
				"item_id": weapon["item_id"],
				"equipped": weapon.get("equipped", false)
			})
	
	if data["inventory"].has("armour"):
		for armour in data["inventory"]["armour"]:
			stat_manager_inventory["armour"].append({
				"item_id": armour["item_id"],
				"equipped": armour.get("equipped", false)
			})
	
	# Update StatManager
	StatManager.update_player_data(
		active_fighter_id,
		stat_manager_inventory,
		data.get("learning_parameters", {})
	)
	
	# Store calculated stats back
	update_calculated_stats(active_fighter_id, StatManager.get_current_stats())

## Debug Functions

func print_fighter_data(fighter_id: String) -> void:
	"""Print fighter data for debugging"""
	if fighters_data.has(fighter_id):
		print("Fighter Data for: ", fighter_id)
		print(JSON.stringify(fighters_data[fighter_id], "\t"))
	else:
		print("No data found for fighter: ", fighter_id)

func get_inventory_summary(fighter_id: String) -> Dictionary:
	"""Get summary of fighter's inventory"""
	if not fighters_data.has(fighter_id):
		return {}
	
	var inventory = fighters_data[fighter_id]["inventory"]
	var summary = {
		"total_items": 0,
		"equipped_weapon": "",
		"equipped_armour": "",
		"modifier_count": 0,
		"feature_count": 0
	}
	
	for category in inventory:
		summary["total_items"] += inventory[category].size()
		
		if category == "weapons":
			for weapon in inventory[category]:
				if weapon.get("equipped", false):
					summary["equipped_weapon"] = weapon["item_id"]
		elif category == "armour":
			for armour in inventory[category]:
				if armour.get("equipped", false):
					summary["equipped_armour"] = armour["item_id"]
		elif category == "modifiers":
			summary["modifier_count"] = inventory[category].size()
		elif category == "features":
			summary["feature_count"] = inventory[category].size()
	
	return summary
