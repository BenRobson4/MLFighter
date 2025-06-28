extends CharacterBody2D

# Movement variables
var speed := 200
var jump_velocity := -400
var gravity := 1000

# Called when the node is added to the scene
func _ready():
	$AnimationPlayer.play("idle")  # Play idle at start

func _physics_process(delta):
	var input_vector = Vector2.ZERO

	# Get input direction
	input_vector.x = Input.get_action_strength("ui_right") - Input.get_action_strength("ui_left")
	input_vector = input_vector.normalized()

	# Move left/right
	velocity.x = input_vector.x * speed

	# Apply gravity
	if not is_on_floor():
		velocity.y += gravity * delta
	else:
		if Input.is_action_just_pressed("ui_accept"):
			velocity.y = jump_velocity

	move_and_slide()

	# Animation logic
	update_animation(input_vector)

func update_animation(input_vector: Vector2):
	var anim = $AnimationPlayer
	
	if not is_on_floor():
		anim.play("jump")
	elif input_vector.x != 0:
		anim.play("run")
	else:
		anim.play("idle")
			# Flip sprite based on direction
	if input_vector.x != 0:
		$Sprite2D.flip_h = input_vector.x < 0
