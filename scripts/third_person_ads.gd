extends Node
class_name ThirdPersonADS

@export var hip_distance := 3.85
@export var hip_height := 0.82
@export var hip_shoulder := 0.78
@export var ads_distance := 2.15
@export var ads_height := 0.68
@export var ads_shoulder := 0.58
@export var transition_speed := 12.0
@export var collision_margin := 0.18
@export var aim_body_turn_speed := 13.0

var player: CharacterBody3D
var camera_rig: Node3D
var camera: Camera3D
var weapon: Node
var body_visual: Node3D
var gun: Node3D

func _ready() -> void:
	player = get_parent() as CharacterBody3D
	if player == null: return
	process_physics_priority = 100
	camera_rig = player.get_node_or_null("CameraRig") as Node3D
	camera = player.get_node_or_null("CameraRig/Camera3D") as Camera3D
	weapon = player.get_node_or_null("CameraRig/Camera3D/Weapon")
	body_visual = player.get_node_or_null("BodyVisual") as Node3D
	gun = player.get_node_or_null("CameraRig/Camera3D/Gun") as Node3D
	# The old camera-child gun was a first-person prototype. Never render it in TPS.
	if gun != null: gun.visible = false

func _physics_process(delta: float) -> void:
	if player == null or camera == null or camera_rig == null or weapon == null: return
	var aiming := bool(weapon.get("aiming"))
	var shoulder := float(player.get("shoulder_side"))
	if is_zero_approx(shoulder): shoulder = 1.0
	_apply_camera_collision(_camera_target(aiming, shoulder), delta)
	_update_operator_pose(aiming, delta)

func _camera_target(aiming: bool, shoulder: float) -> Vector3:
	var target := Vector3(ads_shoulder * shoulder, ads_height, ads_distance) if aiming else Vector3(hip_shoulder * shoulder, hip_height, hip_distance)
	if bool(player.get("in_cover")):
		var peek := float(player.get("cover_peek_side"))
		if absf(peek) > 0.01: target.x += peek * (0.30 if aiming else 0.46)
		if aiming and float(player.get("cover_height")) <= 1.25: target.y += 0.36
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

func _update_weapon_pose(_aiming: bool, _shoulder: float, _delta: float) -> void:
	# Kept as API compatibility for smoke tests. Weapon visuals now belong on the operator rig, not Camera3D.
	if gun != null: gun.visible = false

func _update_operator_pose(aiming: bool, delta: float) -> void:
	if body_visual == null: return
	var target_pitch := 0.0
	if aiming: target_pitch = clampf(rad_to_deg(float(player.get("pitch"))) * 0.12, -5.5, 5.5)
	body_visual.rotation_degrees.x = lerpf(body_visual.rotation_degrees.x, target_pitch, minf(delta * 8.0, 1.0))

func is_aiming() -> bool:
	return weapon != null and bool(weapon.get("aiming"))
