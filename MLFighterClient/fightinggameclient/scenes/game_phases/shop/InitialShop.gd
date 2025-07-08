extends Control

# UI References
@onready var fighter_buttons = $MarginContainer/VBoxContainer/FighterButtons
@onready var fighter_name = $MarginContainer/VBoxContainer/FighterInfoPanel/MarginContainer/FighterInfo/FighterName
@onready var fighter_style = $MarginContainer/VBoxContainer/FighterInfoPanel/MarginContainer/FighterInfo/FighterStyle
@onready var fighter_description = $MarginContainer/VBoxContainer/FighterInfoPanel/MarginContainer/FighterInfo/FighterDescription
@onready var fighter_stats = $MarginContainer/VBoxContainer/FighterInfoPanel/MarginContainer/FighterInfo/FighterStats
@onready var select_button = $MarginContainer/VBoxContainer/SelectButton

# Network reference
var network_manager: Node

# Fighter data
var fighter_options: Array = []
var selected_fighter_index: int = 0
var selected_fighter_data: Dictionary = {}
var pending_data: Dictionary = {}
var fighters_json_data: Dictionary = {}  # Store fighters.json data

func _ready():
	# Load fighters.json
	_load_fighters_data()
	
	# Get network manager reference
	network_manager = get_node("/root/Main/NetworkManager")
	
	# Defer UI setup to ensure all nodes are ready
	call_deferred("_setup_ui")
	
	# If we have pending data, process it after setup
	if pending_data.size() > 0:
		call_deferred("_process_initialization_data", pending_data)

func _load_fighters_data():
	"""Load the fighters.json file"""
	var file = FileAccess.open("res://data/fighters.json", FileAccess.READ)
	if file:
		var json_string = file.get_as_text()
		file.close()
		
		var json = JSON.new()
		var parse_result = json.parse(json_string)
		if parse_result == OK:
			fighters_json_data = json.data.get("fighters", {})
			print("Loaded fighters data: ", fighters_json_data.keys())
		else:
			push_error("Failed to parse fighters.json")
	else:
		push_error("Failed to load fighters.json")

func initialize(data: Dictionary):
	"""Called by GameStateManager when scene loads"""
	print("InitialShop initialized with data: ", data)
	
	# Store data for when nodes are ready
	pending_data = data
	
	# If we're already in the tree, process next frame
	if is_inside_tree():
		call_deferred("_process_initialization_data", data)

func _process_initialization_data(data: Dictionary):
	"""Process the initialization data once nodes are ready"""
	# Extract fighter options
	if data.has("fighter_options"):
		fighter_options = data.fighter_options
		_setup_fighter_buttons()
		_select_fighter(0)  # Select first fighter by default

func _setup_ui():
	"""Set up UI styling - called deferred to ensure nodes exist"""
	# Verify nodes exist
	if not is_inside_tree():
		return
		
	# Style the background
	var background = get_node_or_null("Background")
	if background:
		var style = StyleBoxFlat.new()
		style.bg_color = Color(0.12, 0.12, 0.16)
		style.border_color = Color(0.3, 0.3, 0.4)
		style.border_width_left = 2
		style.border_width_right = 2
		style.border_width_top = 2
		style.border_width_bottom = 2
		style.corner_radius_top_left = 8
		style.corner_radius_top_right = 8
		style.corner_radius_bottom_left = 8
		style.corner_radius_bottom_right = 8
		background.add_theme_stylebox_override("panel", style)
	
	# Style the title
	var title = get_node_or_null("MarginContainer/VBoxContainer/Title")
	if title:
		title.add_theme_font_size_override("font_size", 32)
		title.add_theme_color_override("font_color", Color(1, 0.95, 0.8))
		title.add_theme_constant_override("shadow_offset_x", 2)
		title.add_theme_constant_override("shadow_offset_y", 2)
		title.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.5))
	
	# Style fighter info panel
	var info_panel = get_node_or_null("MarginContainer/VBoxContainer/FighterInfoPanel")
	if info_panel:
		var info_style = StyleBoxFlat.new()
		info_style.bg_color = Color(0.08, 0.08, 0.11)
		info_style.border_color = Color(0.25, 0.25, 0.35)
		info_style.border_width_left = 1
		info_style.border_width_right = 1
		info_style.border_width_top = 1
		info_style.border_width_bottom = 1
		info_style.corner_radius_top_left = 5
		info_style.corner_radius_top_right = 5
		info_style.corner_radius_bottom_left = 5
		info_style.corner_radius_bottom_right = 5
		info_panel.add_theme_stylebox_override("panel", info_style)
	
	# Style labels
	if fighter_name:
		fighter_name.add_theme_font_size_override("font_size", 26)
		fighter_name.add_theme_color_override("font_color", Color(1, 0.85, 0.4))
		fighter_name.add_theme_constant_override("shadow_offset_x", 1)
		fighter_name.add_theme_constant_override("shadow_offset_y", 1)
	
	if fighter_style:
		fighter_style.add_theme_font_size_override("font_size", 18)
		fighter_style.add_theme_color_override("font_color", Color(0.7, 0.9, 1))
	
	# Style description text
	if fighter_description:
		fighter_description.add_theme_color_override("default_color", Color(0.9, 0.9, 0.9))
		fighter_description.add_theme_font_size_override("normal_font_size", 14)
		fighter_description.bbcode_enabled = true
	
	# Style stats text
	if fighter_stats:
		fighter_stats.add_theme_font_size_override("font_size", 13)
		fighter_stats.add_theme_color_override("font_color", Color(0.85, 0.85, 0.85))
		fighter_stats.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	
	# Style select button
	if select_button:
		select_button.custom_minimum_size = Vector2(250, 55)
		select_button.add_theme_font_size_override("font_size", 22)
		
		# Connect button signal
		if not select_button.pressed.is_connected(_on_select_button_pressed):
			select_button.pressed.connect(_on_select_button_pressed)
		
		# Create custom button style
		var button_style_normal = StyleBoxFlat.new()
		button_style_normal.bg_color = Color(0.15, 0.35, 0.55)
		button_style_normal.border_color = Color(0.25, 0.45, 0.65)
		button_style_normal.border_width_left = 2
		button_style_normal.border_width_right = 2
		button_style_normal.border_width_top = 2
		button_style_normal.border_width_bottom = 2
		button_style_normal.corner_radius_top_left = 6
		button_style_normal.corner_radius_top_right = 6
		button_style_normal.corner_radius_bottom_left = 6
		button_style_normal.corner_radius_bottom_right = 6
		
		var button_style_hover = StyleBoxFlat.new()
		button_style_hover.bg_color = Color(0.2, 0.45, 0.65)
		button_style_hover.border_color = Color(0.3, 0.55, 0.75)
		button_style_hover.border_width_left = 2
		button_style_hover.border_width_right = 2
		button_style_hover.border_width_top = 2
		button_style_hover.border_width_bottom = 2
		button_style_hover.corner_radius_top_left = 6
		button_style_hover.corner_radius_top_right = 6
		button_style_hover.corner_radius_bottom_left = 6
		button_style_hover.corner_radius_bottom_right = 6
		
		select_button.add_theme_stylebox_override("normal", button_style_normal)
		select_button.add_theme_stylebox_override("hover", button_style_hover)
	
	# Add entrance animation after everything is set up
	call_deferred("_animate_entrance")

func _setup_fighter_buttons():
	"""Create buttons for each fighter option"""
	if not fighter_buttons:
		return
		
	# Clear existing buttons
	for child in fighter_buttons.get_children():
		child.queue_free()
	
	# Wait for cleanup
	await get_tree().process_frame
	
	# Create button for each fighter
	for i in range(fighter_options.size()):
		var fighter = fighter_options[i]
		var button = Button.new()
		
		# Capitalize fighter name
		var name = fighter.get("fighter_name", "Fighter %d" % (i + 1))
		button.text = name.capitalize()
		button.custom_minimum_size = Vector2(180, 65)
		button.add_theme_font_size_override("font_size", 20)
		
		# Style fighter buttons
		var fb_style_normal = StyleBoxFlat.new()
		fb_style_normal.bg_color = Color(0.2, 0.2, 0.25)
		fb_style_normal.border_color = Color(0.35, 0.35, 0.4)
		fb_style_normal.border_width_left = 2
		fb_style_normal.border_width_right = 2
		fb_style_normal.border_width_top = 2
		fb_style_normal.border_width_bottom = 2
		fb_style_normal.corner_radius_top_left = 5
		fb_style_normal.corner_radius_top_right = 5
		fb_style_normal.corner_radius_bottom_left = 5
		fb_style_normal.corner_radius_bottom_right = 5
		
		var fb_style_hover = StyleBoxFlat.new()
		fb_style_hover.bg_color = Color(0.28, 0.28, 0.33)
		fb_style_hover.border_color = Color(0.45, 0.45, 0.5)
		fb_style_hover.border_width_left = 2
		fb_style_hover.border_width_right = 2
		fb_style_hover.border_width_top = 2
		fb_style_hover.border_width_bottom = 2
		fb_style_hover.corner_radius_top_left = 5
		fb_style_hover.corner_radius_top_right = 5
		fb_style_hover.corner_radius_bottom_left = 5
		fb_style_hover.corner_radius_bottom_right = 5
		
		var fb_style_pressed = StyleBoxFlat.new()
		fb_style_pressed.bg_color = Color(0.35, 0.45, 0.55)
		fb_style_pressed.border_color = Color(0.5, 0.6, 0.7)
		fb_style_pressed.border_width_left = 3
		fb_style_pressed.border_width_right = 3
		fb_style_pressed.border_width_top = 3
		fb_style_pressed.border_width_bottom = 3
		fb_style_pressed.corner_radius_top_left = 5
		fb_style_pressed.corner_radius_top_right = 5
		fb_style_pressed.corner_radius_bottom_left = 5
		fb_style_pressed.corner_radius_bottom_right = 5
		
		button.add_theme_stylebox_override("normal", fb_style_normal)
		button.add_theme_stylebox_override("hover", fb_style_hover)
		button.add_theme_stylebox_override("pressed", fb_style_pressed)
		
		# Style button
		if i == 0:
			button.button_pressed = true  # Select first by default
		
		# Connect button signal with index
		button.pressed.connect(_on_fighter_button_pressed.bind(i))
		
		# Add hover effect
		button.mouse_entered.connect(_on_fighter_button_hover.bind(i))
		
		fighter_buttons.add_child(button)
		
func _update_fighter_display():
	"""Update the UI with selected fighter information"""
	if not fighter_name or not fighter_style or not fighter_description or not fighter_stats:
		return
		
	var fighter_type = selected_fighter_data.get("fighter_name", "unknown")
	var base_data = fighters_json_data.get(fighter_type, {})
	
	# Update name (capitalize)
	fighter_name.text = fighter_type.capitalize() + " Fighter"
	
	# Update style description from base data
	var style_desc = base_data.get("description", "No description available")
	fighter_style.text = style_desc
	
	# Build formatted description with BBCode for RichTextLabel
	fighter_description.clear()
	fighter_description.bbcode_enabled = true  # Ensure BBCode is enabled
	
	# Learning parameters section
	fighter_description.push_color(Color(0.9, 0.9, 0.5))
	fighter_description.push_bold()
	fighter_description.append_text("AI Learning Parameters:")
	fighter_description.pop()  # pop bold
	fighter_description.pop()  # pop color
	fighter_description.append_text("\n")
	
	var learning_params = selected_fighter_data.get("learning_parameters", {})
	if learning_params.size() > 0:
		fighter_description.push_indent(20)
		
		fighter_description.push_color(Color(0.85, 0.85, 0.85))
		fighter_description.append_text("• Exploration Rate: ")
		fighter_description.push_color(Color(0.7, 1.0, 0.7))
		fighter_description.append_text("%.3f" % learning_params.get("epsilon", 0))
		fighter_description.pop()
		fighter_description.append_text("\n")
		
		fighter_description.append_text("• Exploration Decay: ")
		fighter_description.push_color(Color(0.7, 1.0, 0.7))
		fighter_description.append_text("%.5f" % learning_params.get("epsilon_decay", 0))
		fighter_description.pop()
		fighter_description.append_text("\n")
		
		fighter_description.append_text("• Learning Rate: ")
		fighter_description.push_color(Color(0.7, 1.0, 0.7))
		fighter_description.append_text("%.5f" % learning_params.get("learning_rate", 0))
		fighter_description.pop()
		fighter_description.append_text("\n")
		
		fighter_description.pop()  # pop color
		fighter_description.pop()  # pop indent
	
	fighter_description.append_text("\n")
	
	# Active features section
	fighter_description.push_color(Color(0.5, 0.9, 0.9))
	fighter_description.push_bold()
	fighter_description.append_text("Active AI Features:")
	fighter_description.pop()  # pop bold
	fighter_description.pop()  # pop color
	fighter_description.append_text("\n")
	
	fighter_description.push_indent(20)
	fighter_description.push_color(Color(0.85, 0.85, 0.85))
	
	var feature_desc = selected_fighter_data.get("description", "")
	var features = feature_desc.split(", ")
	for feature in features:
		if "includes feature" in feature:
			var feat_name = feature.split("includes feature ")[1]
			fighter_description.append_text("• ")
			fighter_description.push_color(Color(0.8, 0.9, 1.0))
			fighter_description.append_text(feat_name)
			fighter_description.pop()
			fighter_description.append_text("\n")
	
	fighter_description.pop()  # pop color
	fighter_description.pop()  # pop indent
	
	# Build stats display for the RichTextLabel
	var stats_text = ""
	
	# Base stats section
	var base_stats = base_data.get("base_stats", {})
	print("----------------------------------------------------------------------------------------------------------")
	print("base stats:", base_stats)
	if base_stats.size() > 0:
		fighter_stats.clear()
		
		# Combat Stats header
		fighter_stats.push_color(Color(1.0, 0.88, 0.5))
		fighter_stats.push_bold()
		fighter_stats.append_text("Combat Stats:")
		fighter_stats.pop() # pop bold
		fighter_stats.pop() # pop color
		fighter_stats.newline()
		
		# Stats content
		fighter_stats.push_color(Color(0.85, 0.85, 0.85))
		fighter_stats.append_text("Health: ")
		fighter_stats.push_color(Color(0.5, 1.0, 0.5))
		fighter_stats.append_text("%d HP" % base_stats.get("health", 100))
		fighter_stats.pop()
		fighter_stats.newline()
		
		fighter_stats.append_text("Move Speed: ")
		fighter_stats.push_color(Color(0.5, 1.0, 0.5))
		fighter_stats.append_text(str(base_stats.get("move_speed", 5)))
		fighter_stats.pop()
		fighter_stats.newline()
		
		# Continue for other stats...
		fighter_stats.pop() # pop base color
	else:
		fighter_stats.clear()
		fighter_stats.push_color(Color(1.0, 0.5, 0.5))
		fighter_stats.append_text("No combat data available")
	
	return
	
	fighter_stats.text = stats_text
	
	# Update select button
	if select_button:
		select_button.text = "Select " + fighter_type.capitalize()

func _on_fighter_button_pressed(index: int):
	"""Handle fighter button press"""
	_select_fighter(index)
	
	# Update button states
	for i in range(fighter_buttons.get_child_count()):
		var button = fighter_buttons.get_child(i)
		button.button_pressed = (i == index)

func _on_fighter_button_hover(index: int):
	"""Preview fighter on hover with visual feedback"""
	if index >= fighter_buttons.get_child_count():
		return
		
	var button = fighter_buttons.get_child(index)
	var tween = create_tween()
	tween.tween_property(button, "scale", Vector2(1.05, 1.05), 0.1)
	
	# Reset scale when mouse leaves
	if not button.mouse_exited.is_connected(_reset_button_scale):
		button.mouse_exited.connect(_reset_button_scale.bind(button), CONNECT_ONE_SHOT)

func _reset_button_scale(button: Button):
	"""Reset button scale on mouse exit"""
	var reset_tween = create_tween()
	reset_tween.tween_property(button, "scale", Vector2(1.0, 1.0), 0.1)

func _select_fighter(index: int):
	"""Select a fighter and update the display"""
	if index < 0 or index >= fighter_options.size():
		return
	
	selected_fighter_index = index
	selected_fighter_data = fighter_options[index]
	
	# Update display with animation
	_update_fighter_display()
	
	# Animate the info panel
	var info_panel = get_node_or_null("MarginContainer/VBoxContainer/FighterInfoPanel")
	if info_panel:
		info_panel.modulate.a = 0
		var tween = create_tween()
		tween.tween_property(info_panel, "modulate:a", 1.0, 0.2)

func _on_select_button_pressed():
	"""Handle fighter selection"""
	if selected_fighter_data.is_empty():
		push_error("No fighter selected!")
		return
	
	var option_id = selected_fighter_data.get("option_id", "")
	if option_id == "":
		push_error("Selected fighter has no option_id!")
		return
	
	# Send purchase message
	print("Selecting fighter with option_id: ", option_id)
	network_manager.send_message({
		"type": "purchase_option",
		"option_id": option_id
	})
	
	# Disable buttons to prevent double selection
	if select_button:
		select_button.disabled = true
		select_button.text = "Selection Sent..."
		
		# Add pulse animation to indicate sending
		var tween = create_tween()
		tween.set_loops(3)
		tween.tween_property(select_button, "modulate", Color(1.2, 1.2, 1.2), 0.2)
		tween.tween_property(select_button, "modulate", Color(1.0, 1.0, 1.0), 0.2)
	
	if fighter_buttons:
		for button in fighter_buttons.get_children():
			button.disabled = true

func _animate_entrance():
	"""Animate the UI entrance"""
	# Fade in effect
	modulate.a = 0
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 1.0, 0.3)
	
	# Slide in fighter buttons
	if fighter_buttons and fighter_buttons.get_child_count() > 0:
		for i in range(fighter_buttons.get_child_count()):
			var button = fighter_buttons.get_child(i)
			var original_pos = button.position
			button.position.y -= 30
			button.modulate.a = 0
			
			var button_tween = create_tween()
			button_tween.set_parallel(true)
			button_tween.tween_property(button, "position", original_pos, 0.3).set_delay(i * 0.1)
			button_tween.tween_property(button, "modulate:a", 1.0, 0.3).set_delay(i * 0.1)
