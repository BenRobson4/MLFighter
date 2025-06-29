extends Control
class_name BottomBar

@onready var background = $Background
@onready var winner_label = $Background/ControlContainer/VBoxContainer/InfoRow/WinnerLabel
@onready var frame_label = $Background/ControlContainer/VBoxContainer/InfoRow/FrameLabel
@onready var load_button = $Background/ControlContainer/VBoxContainer/ControlsRow/LoadButton
@onready var play_button = $Background/ControlContainer/VBoxContainer/ControlsRow/PlayButton
@onready var pause_button = $Background/ControlContainer/VBoxContainer/ControlsRow/PauseButton
@onready var stop_button = $Background/ControlContainer/VBoxContainer/ControlsRow/StopButton
@onready var speed_slider = $Background/ControlContainer/VBoxContainer/ControlsRow/SpeedSlider
@onready var frame_slider = $Background/ControlContainer/VBoxContainer/ControlsRow/FrameSlider

signal play_pressed
signal pause_pressed
signal stop_pressed
signal load_pressed
signal speed_changed(value: float)
signal frame_seek(value: float)

func _ready():
	# Style background
	if background:
		background.color = Color(0.1, 0.1, 0.1, 0.9)
	
	# Connect signals
	if play_button:
		play_button.pressed.connect(func(): play_pressed.emit())
	if pause_button:
		pause_button.pressed.connect(func(): pause_pressed.emit())
	if stop_button:
		stop_button.pressed.connect(func(): stop_pressed.emit())
	if load_button:
		load_button.pressed.connect(func(): load_pressed.emit())
	if speed_slider:
		speed_slider.value_changed.connect(func(value): speed_changed.emit(value))
	if frame_slider:
		frame_slider.value_changed.connect(func(value): frame_seek.emit(value))
	
	# Setup sliders
	if speed_slider:
		speed_slider.min_value = 0.1
		speed_slider.max_value = 5.0
		speed_slider.value = 1.0
		speed_slider.step = 0.1

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
