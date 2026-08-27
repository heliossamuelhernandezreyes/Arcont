extends CharacterBody3D

signal health_changed(current: float, maximum: float)
signal died
signal injury_changed(zone: String, severity: float)

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
@export var cover_speed := 3.0
@export var cover_probe_distance := 1.0
@export var armor_rating := 0.28

@onready var camera_rig: Node3D = $CameraRig
@onready var camera: Camera3D = $CameraRig/Camera3D
@onready var weapon: Node = $CameraRig/Camera3D/Weapon
@onready var cover_probe: RayCast3D = $CoverProbe
@onready var body_visual: Node3D = $BodyVisual

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var pitch := -0.12
var mobile_move := Vector2.ZERO
var mobile_fire := false
var mobile_sprint := false
var mobile_jump_requested := false
var health := 100.0
var dead := false
var in_cover := false
var cover_normal := Vector3.ZERO
var shoulder_side := 1.0
var injuries := {"head": 0.0, "torso": 0.0, "left_arm": 0.0, "right_arm": 0.0, "left_leg": 0.0, "right_leg": 0.0}

func _ready() -> void:
	add_to_group("player")
	health = max_health
	camera_rig.rotation.x = pitch
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
	if event is InputEventKey and event.pressed and event.keycode == KEY_C:
		_toggle_cover()
	if event is InputEventKey and event.pressed and event.keycode == KEY_Q:
		_switch_shoulder()
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if Input.mouse_mode != Input.MOUSE_MODE_CAPTURED and not DisplayServer.is_touchscreen_available():
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		else:
			_try_fire()

func _physics_process(delta: float) -> void:
	if dead:
		return
	_handle_gamepad_look(delta)
	_update_cover_state()
	if not is_on_floor():
		velocity.y -= gravity * delta
	elif (Input.is_action_just_pressed("jump") or mobile_jump_requested or _gamepad_jump_pressed()) and not in_cover:
		velocity.y = jump_velocity
	mobile_jump_requested = false

	var keyboard_move := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var pad_move := _gamepad_move()
	var input_vec := keyboard_move
	if mobile_move.length_squared() > input_vec.length_squared(): input_vec = mobile_move
	if pad_move.length_squared() > input_vec.length_squared(): input_vec = pad_move

	var cam_forward := -camera_rig.global_transform.basis.z
	var cam_right := camera_rig.global_transform.basis.x
	cam_forward.y = 0.0
	cam_right.y = 0.0
	var direction := (cam_right.normalized() * input_vec.x + cam_forward.normalized() * -input_vec.y).normalized()
	var sprinting := Input.is_action_pressed("sprint") or mobile_sprint or _gamepad_sprint_pressed()
	var leg_penalty: float = clamp(1.0 - (float(injuries["left_leg"]) + float(injuries["right_leg"])) * 0.22, 0.45, 1.0)
	var target_speed := (sprint_speed if sprinting else walk_speed) * leg_penalty
	if in_cover:
		target_speed = cover_speed * leg_penalty
		var tangent := Vector3.UP.cross(cover_normal).normalized()
		direction = tangent * input_vec.x
	var target := direction * target_speed
	var accel := acceleration if is_on_floor() else air_acceleration
	velocity.x = move_toward(velocity.x, target.x, accel * delta)
	velocity.z = move_toward(velocity.z, target.z, accel * delta)
	if direction.length_squared() > 0.02 and not in_cover:
		body_visual.look_at(body_visual.global_position + direction, Vector3.UP)
	move_and_slide()
	if mobile_fire or _gamepad_fire_pressed(): _try_fire()
	if _gamepad_reload_pressed(): request_reload()

func _toggle_cover() -> void:
	if in_cover:
		in_cover = false
		return
	cover_probe.force_raycast_update()
	if cover_probe.is_colliding():
		in_cover = true
		cover_normal = cover_probe.get_collision_normal()

func _update_cover_state() -> void:
	if not in_cover: return
	cover_probe.force_raycast_update()
	if not cover_probe.is_colliding():
		in_cover = false
		return
	cover_normal = cover_probe.get_collision_normal()
	var face := -cover_normal
	body_visual.look_at(body_visual.global_position + face, Vector3.UP)

func _switch_shoulder() -> void:
	shoulder_side *= -1.0
	camera.position.x = 0.72 * shoulder_side

func apply_damage(amount: float, source_direction := Vector3.ZERO, zone := "torso", penetration := 1.0) -> void:
	if dead or amount <= 0.0: return
	var normalized_zone := zone if injuries.has(zone) else "torso"
	var armor_effect := armor_rating if normalized_zone == "torso" else armor_rating * 0.35
	var final_damage: float = amount * maxf(0.2, penetration) * (1.0 - armor_effect)
	if normalized_zone == "head": final_damage *= 1.75
	health = maxf(health - final_damage, 0.0)
	injuries[normalized_zone] = clamp(float(injuries[normalized_zone]) + final_damage / 70.0, 0.0, 1.0)
	injury_changed.emit(normalized_zone, float(injuries[normalized_zone]))
	health_changed.emit(health, max_health)
	if source_direction.length_squared() > 0.0: velocity += source_direction.normalized() * 0.35
	if health <= 0.0: _die()

func heal(amount: float) -> void:
	if dead or amount <= 0.0: return
	health = minf(health + amount, max_health)
	health_changed.emit(health, max_health)

func _die() -> void:
	if dead: return
	dead = true
	mobile_fire = false
	velocity = Vector3.ZERO
	died.emit()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func respawn(at_position: Vector3) -> void:
	global_position = at_position
	health = max_health
	dead = false
	in_cover = false
	for key in injuries.keys(): injuries[key] = 0.0
	health_changed.emit(health, max_health)

func set_mobile_move(value: Vector2) -> void: mobile_move = value.limit_length(1.0)
func add_mobile_look(delta: Vector2) -> void:
	if not dead: _apply_look(delta * mobile_look_sensitivity)
func set_mobile_fire(active: bool) -> void:
	mobile_fire = active and not dead
	if mobile_fire: _try_fire()
func request_mobile_jump() -> void: mobile_jump_requested = true
func set_mobile_sprint(active: bool) -> void: mobile_sprint = active
func request_reload() -> void:
	if not dead and weapon.has_method("request_reload"): weapon.request_reload()
func _try_fire() -> void:
	if not dead and weapon.has_method("try_fire"): weapon.try_fire()
func _on_weapon_recoil(recoil_pitch: float, recoil_yaw: float) -> void:
	rotate_y(recoil_yaw)
	pitch = clamp(pitch + recoil_pitch, deg_to_rad(-65.0), deg_to_rad(55.0))
	camera_rig.rotation.x = pitch
func _apply_look(amount: Vector2) -> void:
	rotate_y(-amount.x)
	pitch = clamp(pitch - amount.y, deg_to_rad(-65.0), deg_to_rad(55.0))
	camera_rig.rotation.x = pitch
func _handle_gamepad_look(delta: float) -> void:
	if Input.get_connected_joypads().is_empty(): return
	var device := Input.get_connected_joypads()[0]
	var look := Vector2(Input.get_joy_axis(device, JOY_AXIS_RIGHT_X), Input.get_joy_axis(device, JOY_AXIS_RIGHT_Y))
	if look.length() >= gamepad_deadzone: _apply_look(look.limit_length(1.0) * gamepad_look_speed * delta)
func _gamepad_move() -> Vector2:
	if Input.get_connected_joypads().is_empty(): return Vector2.ZERO
	var device := Input.get_connected_joypads()[0]
	var value := Vector2(Input.get_joy_axis(device, JOY_AXIS_LEFT_X), Input.get_joy_axis(device, JOY_AXIS_LEFT_Y))
	return Vector2.ZERO if value.length() < gamepad_deadzone else value.limit_length(1.0)
func _gamepad_fire_pressed() -> bool:
	if Input.get_connected_joypads().is_empty(): return false
	var device := Input.get_connected_joypads()[0]
	return Input.get_joy_axis(device, JOY_AXIS_TRIGGER_RIGHT) > 0.45 or Input.is_joy_button_pressed(device, JOY_BUTTON_RIGHT_SHOULDER)
func _gamepad_jump_pressed() -> bool:
	return not Input.get_connected_joypads().is_empty() and Input.is_joy_button_pressed(Input.get_connected_joypads()[0], JOY_BUTTON_A)
func _gamepad_sprint_pressed() -> bool:
	return not Input.get_connected_joypads().is_empty() and Input.is_joy_button_pressed(Input.get_connected_joypads()[0], JOY_BUTTON_LEFT_STICK)
func _gamepad_reload_pressed() -> bool:
	return not Input.get_connected_joypads().is_empty() and Input.is_joy_button_pressed(Input.get_connected_joypads()[0], JOY_BUTTON_X)
