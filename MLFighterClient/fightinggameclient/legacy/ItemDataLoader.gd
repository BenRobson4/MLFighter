extends Node

static var data_cache: Dictionary = {}
static var category_mappings: Dictionary = {}

static func initialize_mappings():
	"""Build mappings of all available categories and subcategories"""
	if not category_mappings.is_empty():
		return
	
	var data_files = {
		"weapons": "res://data/weapons.json",
		"armour": "res://data/armour.json", 
		"learning_modifiers": "res://data/learning_modifiers.json",
		"reward_modifiers": "res://data/reward_modifiers.json",
		"features": "res://data/features.json"
	}
	
	for category in data_files:
		var file_path = data_files[category]
		if FileAccess.file_exists(file_path):
			var file = FileAccess.open(file_path, FileAccess.READ)
			var json_text = file.get_as_text()
			file.close()
			
			var json = JSON.new()
			if json.parse(json_text) == OK:
				var data = json.data
				category_mappings[category] = data.keys()
				data_cache[category] = data

static func parse_item_id(item_id: String) -> Dictionary:
	"""Parse item ID by progressively matching against known categories"""
	initialize_mappings()
	
	var parts = item_id.split("_")
	if parts.is_empty():
		return {}
	
	# Try to find matching category by progressively combining parts
	var category = ""
	var subcategory = ""
	var item_name = ""
	var category_parts = []
	
	# Step 1: Find the category by trying combinations
	for i in range(1, min(parts.size(), 4)):  # Max 3 parts for category
		var test_category = "_".join(parts.slice(0, i))
		if category_mappings.has(test_category):
			category = test_category
			category_parts = parts.slice(0, i)
			break
	
	if category.is_empty():
		print("No matching category found for: ", item_id)
		return {}
	
	# Step 2: Find subcategory from remaining parts
	var remaining_parts = parts.slice(category_parts.size())
	if remaining_parts.is_empty():
		return {"category": category}
	
	var subcategories = category_mappings.get(category, [])
	
	# Try to match subcategory
	for i in range(1, min(remaining_parts.size() + 1, 4)):
		var test_subcategory = "_".join(remaining_parts.slice(0, i))
		if test_subcategory in subcategories:
			subcategory = test_subcategory
			item_name = "_".join(remaining_parts.slice(i))
			break
	
	# If no subcategory match, assume first part is subcategory
	if subcategory.is_empty() and remaining_parts.size() > 0:
		subcategory = remaining_parts[0]
		item_name = "_".join(remaining_parts.slice(1))
	
	return {
		"category": category,
		"subcategory": subcategory,
		"item_name": item_name,
		"full_id": item_id
	}

static func get_item_data(item_id: String) -> Dictionary:
	"""Get item data using smart parsing"""
	var parsed = parse_item_id(item_id)
	if parsed.is_empty():
		return {}
	
	var category_data = data_cache.get(parsed.category, {})
	var subcategory_data = category_data.get(parsed.subcategory, {})
	
	if parsed.item_name.is_empty():
		return subcategory_data
	
	var item_data = subcategory_data.get(parsed.item_name, {})
	
	# Add metadata
	if not item_data.is_empty():
		item_data["item_id"] = item_id
		item_data["category"] = parsed.category
		item_data["subcategory"] = parsed.subcategory
		if not item_data.has("name"):
			item_data["name"] = parsed.item_name.replace("_", " ").capitalize()
	
	return item_data
