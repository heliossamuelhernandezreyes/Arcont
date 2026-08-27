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
@export var armor_rating := 0.28
@export var camera_collision_margin := 0.18
@export var cover_snap_distance := 1.15
@export var cover_transition_distance := 1.35
@export var peek_offset := 0.52
@export var low_cover_camera_lift := 0.55

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
var cover_height := 1.8
var cover_collider: Object
var cover_peek_side := 0.0
var shoulder_side := 1.0
var desired_camera_position := Vector3(0.72, 0.55, 3.35)
var base_camera_position := Vector3(0.72, 0.55, 3.35)
var injuries := {"head":0.0,"torso":0.0,"left_arm":0.0,"right_arm":0.0,"left_leg":0.0,"right_leg":0.0}

func _ready() -> void:
	add_to_group("player")
	health = max_health
	camera_rig.rotation.x = pitch
	base_camera_position = camera.position
	desired_camera_position = base_camera_position
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
	if mobile_move.length_squared() > input_vec.length_squared():
		input_vec = mobile_move
	if pad_move.length_squared() > input_vec.length_squared():
		input_vec = pad_move

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
		cover_peek_side = _cover_edge_peek(input_vec.x)
		if absf(cover_peek_side) > 0.01:
			shoulder_side = cover_peek_side
		_update_cover_camera()
		if absf(input_vec.x) > 0.7 and cover_peek_side != 0.0:
			_try_transition_to_adjacent_cover(tangent * signf(input_vec.x))
	else:
		cover_peek_side = 0.0
		_update_cover_camera()

	var target := direction * target_speed
	var accel := acceleration if is_on_floor() else air_acceleration
	velocity.x = move_toward(velocity.x, target.x, accel * delta)
	velocity.z = move_toward(velocity.z, target.z, accel * delta)
	if direction.length_squared() > 0.02 and not in_cover:
		body_visual.look_at(body_visual.global_position + direction, Vector3.UP)
	move_and_slide()
	_update_camera_collision()
	if mobile_fire or _gamepad_fire_pressed():
		_try_fire()
	if _gamepad_reload_pressed():
		request_reload()

func _toggle_cover() -> void:
	if in_cover:
		_leave_cover()
		return
	cover_probe.force_raycast_update()
	if cover_probe.is_colliding():
		_enter_cover(cover_probe.get_collider(), cover_probe.get_collision_normal())

func _enter_cover(collider: Object, normal: Vector3) -> void:
	in_cover = true
	cover_collider = collider
	cover_normal = normal.normalized()
	cover_height = 1.8
	if collider != null and collider.has_meta("cover_height"):
		cover_height = float(collider.get_meta("cover_height"))
	var world := get_world_3d()
	if world != null:
		var start := global_position + Vector3.UP * 0.55
		var query := PhysicsRayQueryParameters3D.create(start, start - cover_normal * cover_snap_distance)
		query.exclude = [get_rid()]
		var hit := world.direct_space_state.intersect_ray(query)
		if not hit.is_empty():
			var point: Vector3 = hit.get("position", global_position)
			global_position += (point + cover_normal * 0.48 - start)

func _leave_cover() -> void:
	in_cover = false
	cover_collider = null
	cover_peek_side = 0.0
	cover_height = 1.8

func _update_cover_state() -> void:
	if not in_cover:
		return
	cover_probe.force_raycast_update()
	if cover_probe.is_colliding():
		var collider := cover_probe.get_collider()
		if collider == cover_collider or cover_collider == null:
			cover_collider = collider
			cover_normal = cover_probe.get_collision_normal().normalized()
			if collider != null and collider.has_meta("cover_height"):
				cover_height = float(collider.get_meta("cover_height"))
			body_visual.look_at(body_visual.global_position - cover_normal, Vector3.UP)
			return
	if not _try_transition_to_adjacent_cover(Vector3.ZERO):
		_leave_cover()

func _cover_edge_peek(horizontal_input: float) -> float:
	if absf(horizontal_input) < 0.25:
		return 0.0
	var tangent := Vector3.UP.cross(cover_normal).normalized()
	var side := signf(horizontal_input)
	var world := get_world_3d()
	if world == null:
		return 0.0
	var origin := global_position + tangent * side * 0.55 + Vector3.UP * 0.8
	var query := PhysicsRayQueryParameters3D.create(origin, origin - cover_normal * cover_transition_distance)
	query.exclude = [get_rid()]
	var hit := world.direct_space_state.intersect_ray(query)
	if hit.is_empty():
		return side
	return 0.0

func _update_cover_camera() -> void:
	var target := base_camera_position
	target.x = 0.72 * shoulder_side
	if in_cover:
		if absf(cover_peek_side) > 0.01:
			target.x += peek_offset * cover_peek_side
		if cover_height <= 1.25 and (mobile_fire or _gamepad_fire_pressed() or Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT)):
			target.y += low_cover_camera_lift
	desired_camera_position = desired_camera_position.lerp(target, 0.24)

func _try_transition_to_adjacent_cover(preferred_direction: Vector3) -> bool:
	var world := get_world_3d()
	if world == null:
		return false
	var directions: Array[Vector3] = []
	if preferred_direction.length_squared() > 0.01:
		directions.append(preferred_direction.normalized())
	else:
		var tangent := Vector3.UP.cross(cover_normal).normalized()
		directions.append(tangent)
		directions.append(-tangent)
	for direction in directions:
		var start := global_position + direction * 0.75 + Vector3.UP * 0.65
		var end := start - cover_normal * cover_transition_distance
		var query := PhysicsRayQueryParameters3D.create(start, end)
		query.exclude = [get_rid()]
		var hit := world.direct_space_state.intersect_ray(query)
		if not hit.is_empty():
			var collider: Object = hit.get("collider")
			var normal: Vector3 = hit.get("normal", cover_normal)
			if collider != null:
				cover_collider = collider
				cover_normal = normal.normalized()
				if collider.has_meta("cover_height"):
					cover_height = float(collider.get_meta("cover_height"))
				return true
	return false

func _switch_shoulder() -> void:
	shoulder_side *= -1.0
	_update_cover_camera()

func _update_camera_collision() -> void:
	var world := get_world_3d()
	if world == null:
		return
	var origin := camera_rig.global_position
	var desired_global := camera_rig.to_global(desired_camera_position)
	var query := PhysicsRayQueryParameters3D.create(origin, desired_global)
	query.exclude = [get_rid()]
	query.collide_with_areas = false
	var hit := world.direct_space_state.intersect_ray(query)
	if hit.is_empty():
		camera.position = camera.position.lerp(desired_camera_position, 0.28)
		return
	var hit_position: Vector3 = hit.get("position", origin)
	var direction := (desired_global - origin).normalized()
	var safe_global := hit_position - direction * camera_collision_margin
	camera.position = camera_rig.to_local(safe_global)

func apply_damage(amount: float, source_direction := Vector3.ZERO, zone := "torso", penetration := 1.0) -> void:
	if dead or amount <= 0.0:
		return
	var normalized_zone := zone if injuries.has(zone) else "torso"
	var armor_effect := armor_rating if normalized_zone == "torso" else armor_rating * 0.35
	var final_damage: float = amount * maxf(0.2, penetration) * (1.0 - armor_effect)
	if normalized_zone == "head":
		final_damage *= 1.75
	health = maxf(health - final_damage, 0.0)
	injuries[normalized_zone] = clamp(float(injuries[normalized_zone]) + final_damage / 70.0, 0.0, 1.0)
	injury_changed.emit(normalized_zone, float(injuries[normalized_zone]))
	health_changed.emit(health, max_health)
	if source_direction.length_squared() > 0.0:
		velocity += source_direction.normalized() * 0.35
	if health <= 0.0:
		_die()

func heal(amount: float) -> void:
	if dead or amount <= 0.0:
		return
	health = minf(health + amount, max_health)
	health_changed.emit(health, max_health)

func _die() -> void:
	if dead:
		return
	dead = true
	mobile_fire = false
	velocity = Vector3.ZERO
	died.emit()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func respawn(at_position: Vector3) -> void:
	global_position = at_position
	health = max_health
	dead = false
	_leave_cover()
	for key in injuries.keys():
		injuries[key] = 0.0
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
	pitch = clamp(pitch + recoil_pitch, deg_to_rad(-65.0), deg_to_rad(55.0))
	camera_rig.rotation.x = pitch
func _apply_look(amount: Vector2) -> void:
	rotate_y(-amount.x)
	pitch = clamp(pitch - amount.y, deg_to_rad(-65.0), deg_to_rad(55.0))
	camera_rig.rotation.x = pitch
func _handle_gamepad_look(delta: float) -> void:
	if Input.get_connected_joypads().is_empty():
		return
	var d := Input.get_connected_joypads()[0]
	var look := Vector2(Input.get_joy_axis(d, JOY_AXIS_RIGHT_X), Input.get_joy_axis(d, JOY_AXIS_RIGHT_Y))
	if look.length() >= gamepad_deadzone:
		_apply_look(look.limit_length(1.0) * gamepad_look_speed * delta)
func _gamepad_move() -> Vector2:
	if Input.get_connected_joypads().is_empty():
		return Vector2.ZERO
	var d := Input.get_connected_joypads()[0]
	var value := Vector2(Input.get_joy_axis(d, JOY_AXIS_LEFT_X), Input.get_joy_axis(d, JOY_AXIS_LEFT_Y))
	return Vector2.ZERO if value.length() < gamepad_deadzone else value.limit_length(1.0)
func _gamepad_fire_pressed() -> bool:
	if Input.get_connected_joypads().is_empty():
		return false
	var d := Input.get_connected_joypads()[0]
	return Input.get_joy_axis(d, JOY_AXIS_TRIGGER_RIGHT) > 0.45 or Input.is_joy_button_pressed(d, JOY_BUTTON_RIGHT_SHOULDER)
func _gamepad_jump_pressed() -> bool:
	return not Input.get_connected_joypads().is_empty() and Input.is_joy_button_pressed(Input.get_connected_joypads()[0], JOY_BUTTON_A)
func _gamepad_sprint_pressed() -> bool:
	return not Input.get_connected_joypads().is_empty() and Input.is_joy_button_pressed(Input.get_connected_joypads()[0], JOY_BUTTON_LEFT_STICK)
func _gamepad_reload_pressed() -> bool:
	return not Input.get_connected_joypads().is_empty() and Input.is_joy_button_pressed(Input.get_connected_joypads()[0], JOY_BUTTON_X)
