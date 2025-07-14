extends Node

# Cached data
var fighters_data: Dictionary = {}
var weapons_data: Dictionary = {}
var armour_data: Dictionary = {}
var features_data: Dictionary = {}
var learning_modifiers_data: Dictionary = {}
var reward_modifiers_data: Dictionary = {}

# Current player state
var current_fighter_id: String = ""
var current_inventory: Dictionary = {}
var current_learning_parameters: Dictionary = {}
var calculated_stats: Dictionary = {}

func _ready():
	load_all_data()

func load_all_data():
	"""Load all JSON data files"""
	fighters_data = load_json_file("res://data/fighters.json")
	weapons_data = load_json_file("res://data/weapons.json")
	armour_data = load_json_file("res://data/armour.json")
	features_data = load_json_file("res://data/features.json")
	learning_modifiers_data = load_json_file("res://data/learning_modifiers.json")
	reward_modifiers_data = load_json_file("res://data/reward_modifiers.json")

func load_json_file(file_path: String) -> Dictionary:
	"""Load and parse a JSON file"""
	if not FileAccess.file_exists(file_path):
		print("Warning: File not found: ", file_path)
		return {}
	
	var file = FileAccess.open(file_path, FileAccess.READ)
	var json_text = file.get_as_text()
	file.close()
	
	var json = JSON.new()
	var parse_result = json.parse(json_text)
	
	if parse_result != OK:
		print("Error parsing JSON: ", file_path)
		return {}
	
	return json.data

func update_player_data(fighter_id: String, inventory: Dictionary, learning_parameters: Dictionary = {}):
	"""Update current player data and recalculate stats"""
	current_fighter_id = fighter_id
	current_inventory = inventory
	current_learning_parameters = learning_parameters
	
	# Recalculate stats
	calculated_stats = calculate_final_stats()

func calculate_final_stats() -> Dictionary:
	"""Calculate final stats from base fighter + equipped items"""
	if current_fighter_id.is_empty():
		return {}
	
	# Get base fighter stats
	var base_stats = get_fighter_base_stats(current_fighter_id)
	if base_stats.is_empty():
		return {}
	
	# Start with base stats
	var final_stats = base_stats.duplicate(true)
	
	# Apply equipped weapon modifiers
	var equipped_weapon = get_equipped_weapon()
	if equipped_weapon:
		apply_weapon_modifiers(final_stats, equipped_weapon)
	
	# Apply equipped armour modifiers
	var equipped_armour = get_equipped_armour()
	if equipped_armour:
		apply_armour_modifiers(final_stats, equipped_armour)
	
	# Store learning parameters
	final_stats["learning_parameters"] = current_learning_parameters.duplicate(true)
	
	return final_stats

func get_fighter_base_stats(fighter_id: String) -> Dictionary:
	"""Get base stats for a fighter"""
	if fighters_data.has("fighters") and fighters_data.fighters.has(fighter_id):
		return fighters_data.fighters[fighter_id].base_stats.duplicate(true)
	return {}

func get_equipped_weapon() -> Dictionary:
	"""Get currently equipped weapon data"""
	if not current_inventory.has("weapons"):
		return {}
	
	for weapon in current_inventory.weapons:
		if weapon.get("equipped", false):
			# Handle both 'id' and 'item_id' for compatibility
			var weapon_id = weapon.get("item_id")
			return get_weapon_data(weapon_id)
	return {}

func get_equipped_armour() -> Dictionary:
	"""Get currently equipped armour data"""
	if not current_inventory.has("armour"):
		return {}
	
	for armour in current_inventory.armour:
		if armour.get("equipped", false):
			# Handle both 'id' and 'item_id' for compatibility
			var armour_id = armour.get("item_id", armour.get("id", ""))
			return get_armour_data(armour_id)
	return {}

func apply_weapon_modifiers(stats: Dictionary, weapon: Dictionary):
	"""Apply weapon modifiers to stats"""
	if weapon.has("gravity_modifier"):
		stats.gravity *= weapon.gravity_modifier
	if weapon.has("jump_force_modifier"):
		stats.jump_force += weapon.jump_force_modifier
	if weapon.has("move_speed_modifier"):
		stats.move_speed += weapon.move_speed_modifier
	if weapon.has("x_attack_range_modifier"):
		stats.x_attack_range += weapon.x_attack_range_modifier
	if weapon.has("y_attack_range_modifier"):
		stats.y_attack_range += weapon.y_attack_range_modifier
	if weapon.has("attack_damage_modifier"):
		stats.attack_damage += weapon.attack_damage_modifier
	if weapon.has("attack_cooldown_modifier"):
		stats.attack_cooldown += weapon.attack_cooldown_modifier

func apply_armour_modifiers(stats: Dictionary, armour: Dictionary):
	"""Apply armour modifiers to stats"""
	if armour.has("gravity_modifier"):
		stats.gravity *= armour.gravity_modifier
	if armour.has("jump_force_modifier"):
		stats.jump_force += armour.jump_force_modifier
	if armour.has("move_speed_modifier"):
		stats.move_speed += armour.move_speed_modifier
	if armour.has("health_modifier"):
		stats.health += armour.health_modifier
	if armour.has("damage_received_modifier"):
		# Add damage_reduction field if it doesn't exist
		if not stats.has("damage_reduction"):
			stats.damage_reduction = 0
		stats.damage_reduction += abs(armour.damage_received_modifier)

func get_current_stats() -> Dictionary:
	"""Get the current calculated stats"""
	return calculated_stats.duplicate(true)
	
func get_item_data(item_id: String) -> Dictionary:
	"""Universal item data getter"""
	return ItemDataLoader.get_item_data(item_id)

func preview_item_stats(item_id: String, item_type: String = "") -> Dictionary:
	"""Preview stats if an item were equipped"""
	var item_data = get_item_data(item_id)
	if item_data.is_empty():
		return calculated_stats.duplicate(true)
	
	var category = item_data.get("category", "")
	var preview_inventory = current_inventory.duplicate(true)
	var preview_learning = current_learning_parameters.duplicate(true)
	
	# Handle based on category
	if category == "weapons":
		# Unequip current weapon and equip new one
		if not preview_inventory.has("weapons"):
			preview_inventory.weapons = []
		for weapon in preview_inventory.weapons:
			weapon.equipped = false
		preview_inventory.weapons.append({
			"item_id": item_id,
			"equipped": true
		})
		
	elif category == "armour":
		# Unequip current armour and equip new one
		if not preview_inventory.has("armour"):
			preview_inventory.armour = []
		for armour in preview_inventory.armour:
			armour.equipped = false
		preview_inventory.armour.append({
			"item_id": item_id,
			"equipped": true
		})
		
	elif category == "learning_modifiers":
		# Apply learning modifier
		if item_data.has("delta"):
			var subcategory = item_data.get("subcategory", "")
			if "epsilon" in subcategory:
				preview_learning["epsilon"] = preview_learning.get("epsilon", 0.5) + item_data.delta
			elif "decay" in subcategory:
				preview_learning["decay"] = preview_learning.get("decay", 0.005) + item_data.delta
			elif "learning_rate" in subcategory:
				preview_learning["learning_rate"] = preview_learning.get("learning_rate", 0.002) + item_data.delta
				
	elif category == "reward_modifiers":
		# These don't affect displayed stats
		return calculated_stats.duplicate(true)
	
	# Calculate preview stats
	var old_inventory = current_inventory
	var old_learning = current_learning_parameters
	
	current_inventory = preview_inventory
	current_learning_parameters = preview_learning
	var preview_stats = calculate_final_stats()
	
	current_inventory = old_inventory
	current_learning_parameters = old_learning
	
	return preview_stats

# Simplify the weapon/armour getters:
func get_weapon_data(weapon_id: String) -> Dictionary:
	"""Get weapon data by ID"""
	return get_item_data(weapon_id)

func get_armour_data(armour_id: String) -> Dictionary:
	"""Get armour data by ID"""
	return get_item_data(armour_id)
