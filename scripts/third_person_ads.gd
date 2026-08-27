extends Node
class_name ThirdPersonADS

@export var hip_distance := 3.35
@export var hip_height := 0.55
@export var hip_shoulder := 0.72
@export var ads_distance := 1.72
@export var ads_height := 0.48
@export var ads_shoulder := 0.54
@export var transition_speed := 11.0
@export var collision_margin := 0.16
@export var aim_body_turn_speed := 13.0

var player: CharacterBody3D
var camera_rig: Node3D
var camera: Camera3D
var weapon: Node
var body_visual: Node3D
var gun: Node3D
var hip_gun_position := Vector3.ZERO
var hip_gun_rotation := Vector3.ZERO
var initialized_visual := false

func _ready() -> void:
	player = get_parent() as CharacterBody3D
	if player == null: return
	camera_rig = player.get_node_or_null("CameraRig") as Node3D
	camera = player.get_node_or_null("CameraRig/Camera3D") as Camera3D
	weapon = player.get_node_or_null("CameraRig/Camera3D/Weapon")
	body_visual = player.get_node_or_null("BodyVisual") as Node3D
	gun = player.get_node_or_null("CameraRig/Camera3D/Gun") as Node3D
	call_deferred("_capture_weapon_pose")

func _capture_weapon_pose() -> void:
	if gun == null: return
	hip_gun_position = gun.position
	hip_gun_rotation = gun.rotation
	initialized_visual = true

func _process(delta: float) -> void:
	if player == null or camera == null or camera_rig == null or weapon == null: return
	var aiming := bool(weapon.get("aiming"))
	var shoulder := float(player.get("shoulder_side"))
	if is_zero_approx(shoulder): shoulder = 1.0
	var target := _camera_target(aiming, shoulder)
	_apply_camera_collision(target, delta)
	_update_weapon_pose(aiming, shoulder, delta)
	_update_operator_pose(aiming, delta)

func _camera_target(aiming: bool, shoulder: float) -> Vector3:
	var target := Vector3.ZERO
	if aiming:
		target = Vector3(ads_shoulder * shoulder, ads_height, ads_distance)
	else:
		target = Vector3(hip_shoulder * shoulder, hip_height, hip_distance)
	var in_cover := bool(player.get("in_cover"))
	if in_cover:
		var peek := float(player.get("cover_peek_side"))
		if absf(peek) > 0.01: target.x += peek * (0.30 if aiming else 0.46)
		var cover_height := float(player.get("cover_height"))
		if aiming and cover_height <= 1.25: target.y += 0.36
	return target

func _apply_camera_collision(target_local: Vector3, delta: float) -> void:
	var target_global := camera_rig.to_global(target_local)
	var origin := camera_rig.global_position
	var safe_local := target_local
	var world := player.get_world_3d()
	if world != null:
		var query := PhysicsRayQueryParameters3D.create(origin, target_global)
		query.exclude = [player.get_rid()]
		query.collide_with_areas = false
		var hit := world.direct_space_state.intersect_ray(query)
		if not hit.is_empty():
			var point: Vector3 = hit.get("position", origin)
			var direction := (target_global - origin).normalized()
			safe_local = camera_rig.to_local(point - direction * collision_margin)
	camera.position = camera.position.lerp(safe_local, minf(delta * transition_speed, 1.0))

func _update_weapon_pose(aiming: bool, shoulder: float, delta: float) -> void:
	if gun == null or not initialized_visual: return
	var slot := int(weapon.get("slot"))
	var target_pos := hip_gun_position
	var target_rot := hip_gun_rotation
	if aiming:
		match slot:
			0: target_pos = Vector3(0.12 * shoulder, -0.13, -0.84)
			1: target_pos = Vector3(0.10 * shoulder, -0.12, -0.88)
			_: target_pos = Vector3(0.08 * shoulder, -0.11, -0.78)
		target_rot = Vector3(deg_to_rad(-1.8), deg_to_rad(-1.2 * shoulder), deg_to_rad(0.8 * shoulder))
	gun.position = gun.position.lerp(target_pos, minf(delta * 13.0, 1.0))
	gun.rotation = gun.rotation.lerp(target_rot, minf(delta * 13.0, 1.0))

func _update_operator_pose(aiming: bool, delta: float) -> void:
	if body_visual == null: return
	var target_yaw := 0.0
	var target_pitch := 0.0
	if aiming:
		# Turn the visible operator toward the camera aim direction while preserving procedural lean.
		target_yaw = rad_to_deg(player.get("pitch")) * 0.0
		target_pitch = clampf(rad_to_deg(float(player.get("pitch"))) * 0.12, -5.5, 5.5)
	body_visual.rotation_degrees.y = lerpf(body_visual.rotation_degrees.y, target_yaw, minf(delta * aim_body_turn_speed, 1.0))
	var current_x := body_visual.rotation_degrees.x
	body_visual.rotation_degrees.x = lerpf(current_x, target_pitch, minf(delta * 8.0, 1.0))

func is_aiming() -> bool:
	return weapon != null and bool(weapon.get("aiming"))
