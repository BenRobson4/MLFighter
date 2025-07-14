extends Control
class_name TopBar

@onready var background = $Background
@onready var player1_health_bar = $Background/HealthContainer/HealthBars/Player1Health/Player1HealthBar
@onready var player2_health_bar = $Background/HealthContainer/HealthBars/Player2Health/Player2HealthBar
@onready var player1_health_label = $Background/HealthContainer/HealthBars/Player1Health/Player1HealthLabel
@onready var player2_health_label = $Background/HealthContainer/HealthBars/Player2Health/Player2HealthLabel

var player1_max_health: float = 100.0
var player2_max_health: float = 100.0

# Health bar colors
var health_color_high = Color(0.2, 0.8, 0.2)  # Green
var health_color_medium = Color(0.8, 0.8, 0.2)  # Yellow
var health_color_low = Color(0.8, 0.2, 0.2)  # Red

func _ready():
	# Style background
	if background:
		background.color = Color(0.1, 0.1, 0.1, 0.9)

func initialise_health_bars(player1_health: float, player2_health: float):
	player1_max_health = player1_health
	player2_max_health = player2_health
	
	if player1_health_bar:
		player1_health_bar.max_value = player1_max_health
		player1_health_bar.value = player1_max_health
	
	if player2_health_bar:
		player2_health_bar.max_value = player2_max_health
		player2_health_bar.value = player2_max_health
	
	update_player_health(1, player1_health)
	update_player_health(2, player2_health)

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
	
	# Update health label
	if health_label:
		var percentage = int((health / max_health) * 100)
		health_label.text = "%.0f/%.0f (%d%%)" % [health, max_health, percentage]
