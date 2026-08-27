extends CharacterBody3D

@export var walk_speed := 5.5
@export var sprint_speed := 8.5
@export var acceleration := 18.0
@export var air_acceleration := 5.0
@export var jump_velocity := 5.2
@export var mouse_sensitivity := 0.0022
@export var mobile_look_sensitivity := 0.0040
@export var gamepad_look_speed := 2.4
@export var gamepad_deadzone := 0.18
@export var weapon_damage := 34.0
@export var fire_interval := 0.16

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D
@onready var ray: RayCast3D = $Head/Camera3D/RayCast3D

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var pitch := 0.0
var mobile_move := Vector2.ZERO
var mobile_fire := false
var mobile_sprint := false
var mobile_jump_requested := false
var fire_timer := 0.0

func _ready() -> void:
	add_to_group("player")
	if not DisplayServer.is_touchscreen_available():
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_apply_look(event.relative * mouse_sensitivity)
	if event.is_action_pressed("ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if Input.mouse_mode != Input.MOUSE_MODE_CAPTURED and not DisplayServer.is_touchscreen_available():
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		else:
			_try_fire()

func _physics_process(delta: float) -> void:
	fire_timer = max(fire_timer - delta, 0.0)
	_handle_gamepad_look(delta)

	if not is_on_floor():
		velocity.y -= gravity * delta
	elif Input.is_action_just_pressed("jump") or mobile_jump_requested or _gamepad_jump_pressed():
		velocity.y = jump_velocity
	mobile_jump_requested = false

	var keyboard_move := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var pad_move := _gamepad_move()
	var input_vec := keyboard_move
	if mobile_move.length_squared() > input_vec.length_squared():
		input_vec = mobile_move
	if pad_move.length_squared() > input_vec.length_squared():
		input_vec = pad_move

	var direction := (transform.basis * Vector3(input_vec.x, 0.0, input_vec.y)).normalized()
	var sprinting := Input.is_action_pressed("sprint") or mobile_sprint or _gamepad_sprint_pressed()
	var target_speed := sprint_speed if sprinting else walk_speed
	var target := direction * target_speed
	var accel := acceleration if is_on_floor() else air_acceleration
	velocity.x = move_toward(velocity.x, target.x, accel * delta)
	velocity.z = move_toward(velocity.z, target.z, accel * delta)
	move_and_slide()

	if mobile_fire or _gamepad_fire_pressed():
		_try_fire()

func set_mobile_move(value: Vector2) -> void:
	mobile_move = value.limit_length(1.0)

func add_mobile_look(delta: Vector2) -> void:
	_apply_look(delta * mobile_look_sensitivity)

func set_mobile_fire(active: bool) -> void:
	mobile_fire = active
	if active:
		_try_fire()

func request_mobile_jump() -> void:
	mobile_jump_requested = true

func set_mobile_sprint(active: bool) -> void:
	mobile_sprint = active

func _apply_look(amount: Vector2) -> void:
	rotate_y(-amount.x)
	pitch = clamp(pitch - amount.y, deg_to_rad(-88.0), deg_to_rad(88.0))
	head.rotation.x = pitch

func _handle_gamepad_look(delta: float) -> void:
	if Input.get_connected_joypads().is_empty():
		return
	var device := Input.get_connected_joypads()[0]
	var look := Vector2(
		Input.get_joy_axis(device, JOY_AXIS_RIGHT_X),
		Input.get_joy_axis(device, JOY_AXIS_RIGHT_Y)
	)
	if look.length() < gamepad_deadzone:
		return
	look = look.limit_length(1.0)
	_apply_look(look * gamepad_look_speed * delta)

func _gamepad_move() -> Vector2:
	if Input.get_connected_joypads().is_empty():
		return Vector2.ZERO
	var device := Input.get_connected_joypads()[0]
	var value := Vector2(
		Input.get_joy_axis(device, JOY_AXIS_LEFT_X),
		Input.get_joy_axis(device, JOY_AXIS_LEFT_Y)
	)
	if value.length() < gamepad_deadzone:
		return Vector2.ZERO
	return value.limit_length(1.0)

func _gamepad_fire_pressed() -> bool:
	if Input.get_connected_joypads().is_empty():
		return false
	var device := Input.get_connected_joypads()[0]
	return Input.get_joy_axis(device, JOY_AXIS_TRIGGER_RIGHT) > 0.45 or Input.is_joy_button_pressed(device, JOY_BUTTON_RIGHT_SHOULDER)

func _gamepad_jump_pressed() -> bool:
	if Input.get_connected_joypads().is_empty():
		return false
	var device := Input.get_connected_joypads()[0]
	return Input.is_joy_button_pressed(device, JOY_BUTTON_A)

func _gamepad_sprint_pressed() -> bool:
	if Input.get_connected_joypads().is_empty():
		return false
	var device := Input.get_connected_joypads()[0]
	return Input.is_joy_button_pressed(device, JOY_BUTTON_LEFT_STICK)

func _try_fire() -> void:
	if fire_timer > 0.0:
		return
	fire_timer = fire_interval
	_fire()

func _fire() -> void:
	ray.force_raycast_update()
	if not ray.is_colliding():
		return
	var collider := ray.get_collider()
	var hit_point := ray.get_collision_point()
	var shot_direction := -camera.global_transform.basis.z
	if collider and collider.has_method("apply_hit"):
		collider.apply_hit(hit_point, shot_direction, weapon_damage)
	else:
		print("ARCONT impact: ", collider)
