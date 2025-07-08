extends BaseTemplate

func _ready():
	super._ready()
	
	# Create a panel as background
	var panel = Panel.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	panel.modulate = Color(0.5, 0.2, 0.5)  # Purple
	add_child(panel)
	
	var container = VBoxContainer.new()
	container.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	add_child(container)
	
	var label = Label.new()
	label.text = "INITIAL SHOP SCENE"
	label.add_theme_font_size_override("font_size", 32)
	container.add_child(label)
	
	# Show phase info if available
	if scene_data.has("phase"):
		var phase_label = Label.new()
		phase_label.text = "Phase: " + scene_data.get("phase", "unknown")
		phase_label.add_theme_font_size_override("font_size", 16)
		container.add_child(phase_label)
	
	# Show fighter options count if available
	if scene_data.has("fighter_options"):
		var options_label = Label.new()
		options_label.text = "Fighter options available: " + str(scene_data.fighter_options.size())
		options_label.add_theme_font_size_override("font_size", 16)
		container.add_child(options_label)

func _on_data_received(data: Dictionary):
	print("Initial Shop data: ", data)
