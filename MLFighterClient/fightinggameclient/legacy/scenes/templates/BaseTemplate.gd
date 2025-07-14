extends Control 

class_name BaseTemplate

var scene_data: Dictionary = {}

func _ready():
	# Set anchor to fill parent
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
func _on_data_received(data):
	pass

func initialize(data: Dictionary):
	scene_data = data
	if has_method("_on_data_received"):
		_on_data_received(data)
