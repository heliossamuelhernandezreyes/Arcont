extends Node
class_name TacticalMobility

signal stance_changed(state: String)

@export var crouch_speed_multiplier := 0.58
@export var crouch_height := 1.12
@export var crouch_visual_drop := 0.42
@export var slide_duration := 0.62
@export var slide_speed := 10.8
@export var slide_friction := 8.0
@export var vault_forward_distance := 1.35
@export var vault_height_min := 0.45
@export var vault_height_max := 1.35
@export var vault_duration := 0.34
@export var severe_leg_threshold := 1.25

var player: CharacterBody3D
var collision: CollisionShape3D
var body_visual: Node3D
var camera_rig: Node3D
var standing_height := 1.8
var base_body_y := 0.0
var base_camera_y := 0.0
var crouched := false
var sliding := false
var vaulting := false
var slide_remaining := 0.0
var slide_direction := Vector3.ZERO
var slide_velocity := 0.0
var vault_elapsed := 0.0
var vault_start := Vector3.ZERO
var vault_end := Vector3.ZERO

func _ready() -> void:
	player = get_parent() as CharacterBody3D
	if player == null: return
	collision = player.get_node_or_null("Collision") as CollisionShape3D
	body_visual = player.get_node_or_null("BodyVisual") as Node3D
	camera_rig = player.get_node_or_null("CameraRig") as Node3D
	if collision and collision.shape is CapsuleShape3D:
		standing_height = (collision.shape as CapsuleShape3D).height
	if body_visual: base_body_y = body_visual.position.y
	if camera_rig: base_camera_y = camera_rig.position.y

func _physics_process(delta: float) -> void:
	if player == null: return
	if sliding:
		slide_remaining = maxf(slide_remaining - delta, 0.0)
		slide_velocity = maxf(slide_velocity - slide_friction * delta, 0.0)
		if slide_remaining <= 0.0 or slide_velocity <= 1.0:
			_end_slide()
	if vaulting:
		_update_vault(delta)
	_update_stance_visual(delta)

func toggle_crouch() -> void:
	if vaulting: return
	if sliding:
		_end_slide()
		return
	if crouched:
		if _can_stand(): _set_crouched(false)
	else:
		_set_crouched(true)

func request_slide() -> bool:
	if player == null or vaulting or sliding or not player.is_on_floor(): return false
	var speed := Vector2(player.velocity.x, player.velocity.z).length()
	if speed < 5.0 or _leg_load() >= severe_leg_threshold: return false
	if bool(player.get("in_cover")): return false
	var horizontal := Vector3(player.velocity.x, 0.0, player.velocity.z)
	if horizontal.length_squared() < 0.01: return false
	sliding = true
	crouched = true
	slide_remaining = slide_duration * clampf(1.15 - _leg_load() * 0.25, 0.58, 1.0)
	slide_direction = horizontal.normalized()
	slide_velocity = slide_speed * clampf(1.0 - _leg_load() * 0.22, 0.55, 1.0)
	stance_changed.emit("slide")
	return true

func try_vault() -> bool:
	if player == null or vaulting or sliding or not player.is_on_floor(): return false
	if _leg_load() >= severe_leg_threshold: return false
	if bool(player.get("in_cover")) and float(player.get("cover_height")) > vault_height_max: return false
	var world := player.get_world_3d()
	if world == null: return false
	var forward := -player.global_transform.basis.z
	forward.y = 0.0
	forward = forward.normalized()
	var origin_low := player.global_position + Vector3.UP * 0.55
	var front_query := PhysicsRayQueryParameters3D.create(origin_low, origin_low + forward * vault_forward_distance)
	front_query.exclude = [player.get_rid()]
	var front_hit := world.direct_space_state.intersect_ray(front_query)
	if front_hit.is_empty(): return false
	var obstacle_point: Vector3 = front_hit.get("position", origin_low)
	var top_origin := obstacle_point + Vector3.UP * (vault_height_max + 0.45) - forward * 0.10
	var down_query := PhysicsRayQueryParameters3D.create(top_origin, obstacle_point - Vector3.UP * 0.15)
	down_query.exclude = [player.get_rid()]
	var top_hit := world.direct_space_state.intersect_ray(down_query)
	if top_hit.is_empty(): return false
	var top_point: Vector3 = top_hit.get("position", obstacle_point)
	var obstacle_height := top_point.y - player.global_position.y
	if obstacle_height < vault_height_min or obstacle_height > vault_height_max: return false
	var landing := top_point + forward * 0.95 + Vector3.UP * 0.05
	var clearance_query := PhysicsRayQueryParameters3D.create(landing + Vector3.UP * 0.15, landing + Vector3.UP * 1.55)
	clearance_query.exclude = [player.get_rid()]
	if not world.direct_space_state.intersect_ray(clearance_query).is_empty(): return false
	vaulting = true
	crouched = false
	vault_elapsed = 0.0
	vault_start = player.global_position
	vault_end = landing
	player.velocity = Vector3.ZERO
	if player.has_method("_leave_cover"): player.call("_leave_cover")
	stance_changed.emit("vault")
	return true

func movement_speed_multiplier() -> float:
	if vaulting: return 0.0
	if sliding: return 1.0
	return crouch_speed_multiplier if crouched else 1.0

func apply_motion_override() -> void:
	if player == null: return
	if sliding:
		player.velocity.x = slide_direction.x * slide_velocity
		player.velocity.z = slide_direction.z * slide_velocity

func blocks_normal_movement() -> bool:
	return vaulting

func blocks_jump() -> bool:
	return vaulting or sliding

func is_crouched() -> bool:
	return crouched

func _update_vault(delta: float) -> void:
	vault_elapsed += delta
	var t := clampf(vault_elapsed / maxf(vault_duration, 0.01), 0.0, 1.0)
	var smooth := t * t * (3.0 - 2.0 * t)
	var pos := vault_start.lerp(vault_end, smooth)
	pos.y += sin(t * PI) * 0.52
	player.global_position = pos
	player.velocity = Vector3.ZERO
	if t >= 1.0:
		vaulting = false
		stance_changed.emit("crouch" if crouched else "stand")

func _end_slide() -> void:
	if not sliding: return
	sliding = false
	slide_remaining = 0.0
	slide_velocity = 0.0
	stance_changed.emit("crouch" if crouched else "stand")

func _set_crouched(active: bool) -> void:
	crouched = active
	stance_changed.emit("crouch" if crouched else "stand")

func _can_stand() -> bool:
	if player == null: return false
	var world := player.get_world_3d()
	if world == null: return true
	var start := player.global_position + Vector3.UP * 0.95
	var end := player.global_position + Vector3.UP * 1.75
	var query := PhysicsRayQueryParameters3D.create(start, end)
	query.exclude = [player.get_rid()]
	return world.direct_space_state.intersect_ray(query).is_empty()

func _update_stance_visual(delta: float) -> void:
	var crouch_alpha := 1.0 if crouched or sliding else 0.0
	if collision and collision.shape is CapsuleShape3D:
		var capsule := collision.shape as CapsuleShape3D
		var target_height := crouch_height if crouch_alpha > 0.5 else standing_height
		capsule.height = lerpf(capsule.height, target_height, minf(delta * 13.0, 1.0))
	if body_visual:
		var target_body_y := base_body_y - crouch_visual_drop * crouch_alpha
		body_visual.position.y = lerpf(body_visual.position.y, target_body_y, minf(delta * 12.0, 1.0))
		var target_pitch := -10.0 if sliding else (-4.0 if crouched else 0.0)
		body_visual.rotation_degrees.x = lerpf(body_visual.rotation_degrees.x, target_pitch, minf(delta * 10.0, 1.0))
	if camera_rig:
		var target_camera_y := base_camera_y - 0.34 * crouch_alpha
		camera_rig.position.y = lerpf(camera_rig.position.y, target_camera_y, minf(delta * 12.0, 1.0))

func _leg_load() -> float:
	if player == null: return 0.0
	var data = player.get("injuries")
	if not data is Dictionary: return 0.0
	var injuries := data as Dictionary
	return float(injuries.get("left_leg", 0.0)) + float(injuries.get("right_leg", 0.0))
