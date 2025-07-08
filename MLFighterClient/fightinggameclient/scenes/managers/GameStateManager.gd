extends Node

signal scene_changed(scene_name: String)

var current_scene_instance: Node
var game_content_container: Node

# Scene paths
const SCENE_PATHS = {
	"Matchmaking": "res://scenes/templates/MatchmakingTemplate.tscn",
	"InitialShop": "res://scenes/game_phases/shop/InitialShop.tscn",  # Updated path
	"Fighting": "res://scenes/templates/FightingTemplate.tscn",
	"ReplayViewer": "res://scenes/templates/ReplayViewerTemplate.tscn",
	"ShopPhase": "res://scenes/templates/ShopPhaseTemplate.tscn",
	"GameOver": "res://scenes/templates/GameOverTemplate.tscn"
}

func _ready():
	# Get reference to game content container
	game_content_container = get_node("/root/Main/VBoxContainer/HSplitContainer/GameContent")

func transition_to_scene(scene_name: String, data: Dictionary = {}):
	print("Transitioning to scene: ", scene_name)
	
	# Clean up current scene
	if current_scene_instance:
		current_scene_instance.queue_free()
		await current_scene_instance.tree_exited
	
	# Load new scene
	if scene_name in SCENE_PATHS:
		var scene_path = SCENE_PATHS[scene_name]
		var packed_scene = load(scene_path)
		if packed_scene:
			current_scene_instance = packed_scene.instantiate()
			
			# Pass data to the new scene if it has an initialize method
			if current_scene_instance.has_method("initialize"):
				current_scene_instance.initialize(data)
			
			game_content_container.add_child(current_scene_instance)
			emit_signal("scene_changed", scene_name)
		else:
			push_error("Failed to load scene: " + scene_path)
