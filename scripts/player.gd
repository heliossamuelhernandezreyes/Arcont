extends CharacterBody3D

signal health_changed(current: float, maximum: float)
signal died

@export var walk_speed := 5.5
@export var sprint_speed := 8.5
@export var acceleration := 18.0
@export var air_acceleration := 5.0
@export var jump_velocity := 5.2
@export var mouse_sensitivity := 0.0022
@export var mobile_look_sensitivity := 0.0040
@export var gamepad_look_speed := 2.4
@export var gamepad_deadzone := 0.18
@export var max_health := 100.0

@onready var head: Node3D = $Head
@onready var weapon: Node = $Head/Camera3D/Weapon

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var pitch := 0.0
var mobile_move := Vector2.ZERO
var mobile_fire := false
var mobile_sprint := false
var mobile_jump_requested := false
var health := 100.0
var dead := false

func _ready() -> void:
	add_to_group("player")
	health = max_health
	health_changed.emit(health, max_health)
	if weapon.has_signal("recoil_requested"):
		weapon.recoil_requested.connect(_on_weapon_recoil)
	if not DisplayServer.is_touchscreen_available():
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _unhandled_input(event: InputEvent) -> void:
	if dead:
		return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_apply_look(event.relative * mouse_sensitivity)
	if event.is_action_pressed("ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if event.is_action_pressed("reload"):
		request_reload()
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if Input.mouse_mode != Input.MOUSE_MODE_CAPTURED and not DisplayServer.is_touchscreen_available():
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		else:
			_try_fire()

func _physics_process(delta: float) -> void:
	if dead:
		return
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
	if _gamepad_reload_pressed():
		request_reload()

func apply_damage(amount: float, source_direction := Vector3.ZERO) -> void:
	if dead or amount <= 0.0:
		return
	health = max(health - amount, 0.0)
	health_changed.emit(health, max_health)
	if source_direction.length_squared() > 0.0:
		velocity += source_direction.normalized() * 0.35
	if health <= 0.0:
		_die()

func heal(amount: float) -> void:
	if dead or amount <= 0.0:
		return
	health = min(health + amount, max_health)
	health_changed.emit(health, max_health)

func _die() -> void:
	if dead:
		return
	dead = true
	mobile_fire = false
	velocity = Vector3.ZERO
	died.emit()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	print("ARCONT player down")

func respawn(at_position: Vector3) -> void:
	global_position = at_position
	health = max_health
	dead = false
	health_changed.emit(health, max_health)

func set_mobile_move(value: Vector2) -> void:
	mobile_move = value.limit_length(1.0)

func add_mobile_look(delta: Vector2) -> void:
	if not dead:
		_apply_look(delta * mobile_look_sensitivity)

func set_mobile_fire(active: bool) -> void:
	mobile_fire = active and not dead
	if mobile_fire:
		_try_fire()

func request_mobile_jump() -> void:
	mobile_jump_requested = true

func set_mobile_sprint(active: bool) -> void:
	mobile_sprint = active

func request_reload() -> void:
	if not dead and weapon.has_method("request_reload"):
		weapon.request_reload()

func _try_fire() -> void:
	if not dead and weapon.has_method("try_fire"):
		weapon.try_fire()

func _on_weapon_recoil(recoil_pitch: float, recoil_yaw: float) -> void:
	rotate_y(recoil_yaw)
	pitch = clamp(pitch + recoil_pitch, deg_to_rad(-88.0), deg_to_rad(88.0))
	head.rotation.x = pitch

func _apply_look(amount: Vector2) -> void:
	rotate_y(-amount.x)
	pitch = clamp(pitch - amount.y, deg_to_rad(-88.0), deg_to_rad(88.0))
	head.rotation.x = pitch

func _handle_gamepad_look(delta: float) -> void:
	if Input.get_connected_joypads().is_empty():
		return
	var device := Input.get_connected_joypads()[0]
	var look := Vector2(Input.get_joy_axis(device, JOY_AXIS_RIGHT_X), Input.get_joy_axis(device, JOY_AXIS_RIGHT_Y))
	if look.length() < gamepad_deadzone:
		return
	_apply_look(look.limit_length(1.0) * gamepad_look_speed * delta)

func _gamepad_move() -> Vector2:
	if Input.get_connected_joypads().is_empty():
		return Vector2.ZERO
	var device := Input.get_connected_joypads()[0]
	var value := Vector2(Input.get_joy_axis(device, JOY_AXIS_LEFT_X), Input.get_joy_axis(device, JOY_AXIS_LEFT_Y))
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
	return Input.is_joy_button_pressed(Input.get_connected_joypads()[0], JOY_BUTTON_A)

func _gamepad_sprint_pressed() -> bool:
	if Input.get_connected_joypads().is_empty():
		return false
	return Input.is_joy_button_pressed(Input.get_connected_joypads()[0], JOY_BUTTON_LEFT_STICK)

func _gamepad_reload_pressed() -> bool:
	if Input.get_connected_joypads().is_empty():
		return false
	return Input.is_joy_button_pressed(Input.get_connected_joypads()[0], JOY_BUTTON_X)
