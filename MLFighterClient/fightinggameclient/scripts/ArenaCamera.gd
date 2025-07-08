extends Camera2D
class_name ArenaCamera

var arena_width: float = 800
var arena_height: float = 400
var target_zoom: Vector2 = Vector2.ONE

func _ready():
	make_current()
	
	# Connect to viewport size changes
	var viewport = get_viewport()
	if viewport:
		# For SubViewport, we need to monitor size changes differently
		set_process(true)  # Enable _process to check for size changes
	
	await get_tree().process_frame
	setup_camera()

var last_viewport_size: Vector2 = Vector2.ZERO

func _process(_delta):
	# Check if viewport size has changed
	var viewport = get_viewport()
	if viewport:
		var current_size = viewport.get_visible_rect().size
		if current_size != last_viewport_size and current_size.x > 0 and current_size.y > 0:
			last_viewport_size = current_size
			setup_camera()

func setup_camera_for_arena(width: float, height: float):
	arena_width = width
	arena_height = height
	print("Camera: Setting up for arena ", width, "x", height)
	setup_camera()

func setup_camera():
	# Position camera to show the full arena
	var camera_x = arena_width / 2.0
	var camera_y = -arena_height / 2.0 
	
	global_position = Vector2(camera_x, camera_y)
	
	var viewport = get_viewport()
	if not viewport:
		print("No viewport found!")
		return
	
	var viewport_size = viewport.get_visible_rect().size
	if viewport_size.x <= 0 or viewport_size.y <= 0:
		print("Invalid viewport size: ", viewport_size)
		return
	
	print("=== CAMERA SETUP ===")
	print("Viewport size: ", viewport_size)
	print("Arena size: ", arena_width, "x", arena_height)
	
	# Calculate zoom to fit arena in viewport with small margin
	var margin = 1.05  # 5% margin
	var zoom_x = viewport_size.x / (arena_width * margin)
	var zoom_y = viewport_size.y / (arena_height * margin)
	var required_zoom = min(zoom_x, zoom_y)
	
	target_zoom = Vector2(required_zoom, required_zoom)
	zoom = target_zoom
	
	print("Camera position: ", global_position)
	print("Camera zoom: ", zoom)
	
	# Debug: show visible area
	var visible_area = viewport_size / zoom
	var visible_min = global_position - visible_area / 2
	var visible_max = global_position + visible_area / 2
	print("Visible area: ", visible_min, " to ", visible_max)
	print("Arena bounds: (0,0) to (", arena_width, ", ", -arena_height, ")")
	print("==================")

# Optional: Smooth zoom transitions
func _physics_process(delta):
	if zoom != target_zoom:
		zoom = zoom.lerp(target_zoom, delta * 5.0)  # Smooth zoom transition
