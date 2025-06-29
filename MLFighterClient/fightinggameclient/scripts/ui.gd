extends CanvasLayer
class_name UIManager

@onready var play_button = $BottomBar/HBoxContainer/Controls/PlayButton
@onready var pause_button = $BottomBar/HBoxContainer/Controls/PauseButton
@onready var stop_button = $BottomBar/HBoxContainer/Controls/StopButton
@onready var speed_slider = $BottomBar/HBoxContainer/Controls/Sliders/SpeedSlider
@onready var frame_slider = $BottomBar/HBoxContainer/Controls/Sliders/FrameSlider
@onready var frame_label = $BottomBar/HBoxContainer/Info/FrameLabel
@onready var winner_label = $BottomBar/HBoxContainer/Info/FrameLabel
@onready var load_button = $BottomBar/HBoxContainer/Controls/LoadButton

# Health bars
@onready var player1_health_bar = $TopBar/HealthBars/Player1Health/Player1HealthBar
@onready var player2_health_bar = $TopBar/HealthBars/Player2Health/Player2HealthBar
@onready var player1_health_label = $TopBar/HealthBars/Player1Health/Player1HealthLabel
@onready var player2_health_label = $TopBar/HealthBars/Player2Health/Player2HealthLabel

var replay_manager: ReplayManager
var player1_max_health: float = 100.0
var player2_max_health: float = 100.0

# Health bar colors
var health_color_high = Color(0.2, 0.8, 0.2)  # Green
var health_color_medium = Color(0.8, 0.8, 0.2)  # Yellow
var health_color_low = Color(0.8, 0.2, 0.2)  # Red

func _ready():
	# Connect UI signals
	if play_button:
		play_button.pressed.connect(_on_play_pressed)
	if pause_button:
		pause_button.pressed.connect(_on_pause_pressed)
	if stop_button:
		stop_button.pressed.connect(_on_stop_pressed)
	if speed_slider:
		speed_slider.value_changed.connect(_on_speed_changed)
	if frame_slider:
		frame_slider.value_changed.connect(_on_frame_seek)
	if load_button:
		load_button.pressed.connect(_on_load_pressed)
	
	# Get replay manager reference
	replay_manager = get_node("../ReplayManager")
	
	if replay_manager:
		replay_manager.replay_started.connect(_on_replay_started)
		replay_manager.replay_finished.connect(_on_replay_finished)
	
		# Style health bar backgrounds
	var bg_style = StyleBoxFlat.new()
	bg_style.bg_color = Color(0.2, 0.2, 0.2, 0.8)  # Dark gray background
	bg_style.corner_radius_top_left = 4
	bg_style.corner_radius_top_right = 4
	bg_style.corner_radius_bottom_left = 4
	bg_style.corner_radius_bottom_right = 4
	
	if player1_health_bar:
		player1_health_bar.add_theme_stylebox_override("background", bg_style)
	
	if player2_health_bar:
		player2_health_bar.add_theme_stylebox_override("background", bg_style)

func initialize_health_bars(replay_data: Dictionary):
	# Extract initial health from first frame
	if replay_data.has("frames") and replay_data.frames.size() > 0:
		var first_frame = replay_data.frames[0]
		
		if first_frame.players.has("1"):
			player1_max_health = first_frame.players["1"].health
			if player1_health_bar:
				player1_health_bar.max_value = player1_max_health
				player1_health_bar.value = player1_max_health
			update_player_health(1, player1_max_health)
		
		if first_frame.players.has("2"):
			player2_max_health = first_frame.players["2"].health
			if player2_health_bar:
				player2_health_bar.max_value = player2_max_health
				player2_health_bar.value = player2_max_health
			update_player_health(2, player2_max_health)

func setup_replay_info(metadata: Dictionary):
	if winner_label:
		winner_label.text = "Winner: Player " + str(metadata.winner)
	
	if frame_slider:
		frame_slider.max_value = metadata.total_frames - 1
		frame_slider.value = 0

func update_frame_info(current_frame: int, total_frames: int):
	if frame_label:
		frame_label.text = "Frame: " + str(current_frame + 1) + " / " + str(total_frames)
	
	if frame_slider:
		frame_slider.value = current_frame

func update_player_health(player_num: int, health: float):
	var health_bar: ProgressBar
	var health_label: Label
	var max_health: float
	
	if player_num == 1:
		health_bar = player1_health_bar
		health_label = player1_health_label
		max_health = player1_max_health
	else:
		health_bar = player2_health_bar
		health_label = player2_health_label
		max_health = player2_max_health
	
	if health_bar:
		health_bar.value = health
		
		# Update color based on health percentage
		var health_percent = health / max_health
		var health_color: Color
		
		if health_percent > 0.5:
			health_color = health_color_high
		elif health_percent > 0.25:
			health_color = health_color_medium
		else:
			health_color = health_color_low
		
		# Apply color to health bar
		var style = StyleBoxFlat.new()
		style.bg_color = health_color
		style.corner_radius_top_left = 4
		style.corner_radius_top_right = 4
		style.corner_radius_bottom_left = 4
		style.corner_radius_bottom_right = 4
		health_bar.add_theme_stylebox_override("fill", style)
	
	# Update health label with actual values and percentage
	if health_label:
		var percentage = int((health / max_health) * 100)
		health_label.text = "Player %d: %.0f/%.0f (%d%%)" % [player_num, health, max_health, percentage]

# ... rest of the functions remain the same ...

func _on_play_pressed():
	if replay_manager:
		replay_manager.start_replay()

func _on_pause_pressed():
	if replay_manager:
		if replay_manager.is_paused:
			replay_manager.resume_replay()
		else:
			replay_manager.pause_replay()

func _on_stop_pressed():
	if replay_manager:
		replay_manager.stop_replay()

func _on_speed_changed(value: float):
	if replay_manager:
		replay_manager.set_replay_speed(value)

func _on_frame_seek(value: float):
	if replay_manager:
		replay_manager.seek_to_frame(int(value))

func _on_load_pressed():
	if replay_manager:
		replay_manager.load_replay_from_file("res://replay.json")

func _on_replay_started():
	if play_button:
		play_button.disabled = true
	if pause_button:
		pause_button.disabled = false

func _on_replay_finished():
	if play_button:
		play_button.disabled = false
	if pause_button:
		pause_button.disabled = true
