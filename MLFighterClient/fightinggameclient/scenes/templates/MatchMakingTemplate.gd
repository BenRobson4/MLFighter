extends BaseTemplate

func _ready():
	super._ready()
	
	# Create a panel as background
	var panel = Panel.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	panel.modulate = Color(0.2, 0.3, 0.5)  # Blue
	add_child(panel)
	
	var label = Label.new()
	label.text = "MATCHMAKING SCENE"
	label.add_theme_font_size_override("font_size", 32)
	label.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	add_child(label)

func _on_data_received(data: Dictionary):
	print("Matchmaking data: ", data)
