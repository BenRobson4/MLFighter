extends Node
class_name GameController

# ==================== SIGNALS ====================
signal phase_changed(new_phase: String)
signal connection_status_changed(connected: bool)

# ==================== REFERENCES ====================
@onready var network_manager: NetworkManager = $NetworkManager
@onready var phase_container: Node = $"../PhaseContainer"
@onready var notification_system = $"../UI/NotificationSystem"

# ==================== CONSTANTS ====================
const PHASE_SCENES = {
	"CONNECTION": preload("res://scenes/phases/ConnectionPhase.tscn"),
	"MATCHMAKING": preload("res://scenes/phases/MatchmakingPhase.tscn"),
	"FIGHTER_SELECTION": preload("res://scenes/phases/FighterSelectionPhase.tscn"),
	"SHOP_PHASE": preload("res://scenes/phases/ShopPhase.tscn"),
	"FIGHTING": preload("res://scenes/phases/FightingPhase.tscn"),
	"VIEWING_REPLAY": preload("res://scenes/phases/ReplayViewingPhase.tscn"),
}

# ==================== STATE VARIABLES ====================
var current_phase: String = ""
var current_phase_instance: Node = null

# ==================== INITIALIZATION ====================
func _ready() -> void:
	# Connect to GameDataStore signals
	GameDataStore.gold_changed.connect(_on_gold_changed)
	GameDataStore.fighter_selected.connect(_on_fighter_selected)
	GameDataStore.inventory_updated.connect(_on_inventory_updated)
	GameDataStore.stats_updated.connect(_on_stats_updated)
	
	# Connect to StaticDataManager signals
	StaticDataManager.data_loaded.connect(_on_static_data_loaded)
	StaticDataManager.all_data_loaded.connect(_on_all_static_data_loaded)
	StaticDataManager.data_load_failed.connect(_on_static_data_load_failed)
	
	# Connect to NetworkManager signals
	network_manager.connected_to_server.connect(_on_connected_to_server)
	network_manager.disconnected_from_server.connect(_on_disconnected_from_server)
	network_manager.connection_error.connect(_on_connection_error)
	network_manager.message_received.connect(_on_message_received)

# ==================== PHASE MANAGEMENT ====================
func transition_to_phase(phase_name: String) -> void:
	pass

func _cleanup_current_phase() -> void:
	pass

func _load_phase_scene(phase_name: String) -> Node:
	pass

# ==================== MESSAGE ROUTING ====================
func _on_message_received(message: Dictionary) -> void:
	pass

func _route_message_to_phase(message: Dictionary) -> void:
	pass

# ==================== SERVER MESSAGE HANDLERS ====================
func _handle_connected_message(data: Dictionary) -> void:
	pass

func _handle_matchmaking_started(data: Dictionary) -> void:
	pass

func _handle_match_found(data: Dictionary) -> void:
	pass

func _handle_fighter_selection_ready(data: Dictionary) -> void:
	pass

func _handle_shop_phase_start(data: Dictionary) -> void:
	pass

func _handle_fight_starting(data: Dictionary) -> void:
	pass

func _handle_batch_completed(data: Dictionary) -> void:
	pass

func _handle_replay_data(data: Dictionary) -> void:
	pass

func _handle_waiting_for_opponent(data: Dictionary) -> void:
	pass

func _handle_opponent_ready(data: Dictionary) -> void:
	pass

func _handle_error(data: Dictionary) -> void:
	pass

# ==================== NETWORK EVENT HANDLERS ====================
func _on_connected_to_server() -> void:
	pass

func _on_disconnected_from_server() -> void:
	pass

func _on_connection_error(error: String) -> void:
	pass

# ==================== DATA STORE EVENT HANDLERS ====================
func _on_gold_changed(new_amount: int) -> void:
	pass

func _on_fighter_selected(fighter_data: Dictionary) -> void:
	pass

func _on_inventory_updated(inventory: Dictionary) -> void:
	pass

func _on_stats_updated(wins: int, losses: int, rounds: int) -> void:
	pass

# ==================== STATIC DATA EVENT HANDLERS ====================
func _on_static_data_loaded(data_type: String) -> void:
	pass

func _on_all_static_data_loaded() -> void:
	pass

func _on_static_data_load_failed(data_type: String, error: String) -> void:
	pass

# ==================== OUTGOING MESSAGES ====================
func send_message_to_server(message: Dictionary) -> void:
	pass

func request_fighter_selection(fighter_id: String) -> void:
	pass

func request_item_purchase(item_id: String) -> void:
	pass

func request_shop_refresh() -> void:
	pass

func complete_shop_phase() -> void:
	pass

func notify_replay_viewed() -> void:
	pass

# ==================== UTILITY FUNCTIONS ====================
func get_current_phase_name() -> String:
	pass

func is_in_phase(phase_name: String) -> bool:
	pass

func show_notification(message: String, duration: float = 3.0) -> void:
	pass
