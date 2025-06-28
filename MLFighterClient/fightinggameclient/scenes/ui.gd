extends CanvasLayer

@onready var frame_counter_label = $Info/FrameCounter
@onready var player1_health_label = $Info/Player1Health
@onready var player2_health_label = $Info/Player2Health
@onready var p1_state_label = $Info/P1StateLabel
@onready var p2_state_label = $Info/P2StateLabel

func update_state_display(p1_states, p2_states):
	p1_state_label.text = "P1 - A:%s B:%s J:%s" % [
		get_state_letter(p1_states.attack),
		get_state_letter(p1_states.block),
		get_state_letter(p1_states.jump)
	]
	p2_state_label.text = "P2 - A:%s B:%s J:%s" % [
		get_state_letter(p2_states.attack),
		get_state_letter(p2_states.block),
		get_state_letter(p2_states.jump)
	]

func get_state_letter(state):
	match state:
		0: return "-"  # NONE
		1: return "S"  # STARTUP
		2: return "A"  # ACTIVE
		3: return "R"  # RECOVERY
		4: return "W"  # WAIT
		
var max_frames = 0

func set_max_frames(frames):
	max_frames = frames

func update_frame_counter(frame):
	frame_counter_label.text = "Frame: %d / %d" % [frame, max_frames]

func update_health_display(p1_health, p2_health):
	player1_health_label.text = "P1: %.1f" % p1_health
	player2_health_label.text = "P2: %.1f" % p2_health
