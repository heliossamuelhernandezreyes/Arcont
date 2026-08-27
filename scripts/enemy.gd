extends CharacterBody3D

signal died(enemy: Node)
signal limb_lost(enemy: Node, limb: String)
signal staggered(enemy: Node, duration: float)
signal knocked_down(enemy: Node, duration: float)
signal crawl_started(enemy: Node)

@export var max_health := 100.0
@export var move_speed := 2.4
@export var acceleration := 10.0
@export var contact_damage := 8.0
@export var attack_cooldown := 0.8
@export var separation_radius := 1.15
@export var separation_strength := 1.35
@export var gib_lifetime := 6.0
@export var head_health := 42.0
@export var arm_health := 34.0
@export var leg_health := 44.0
@export var leg_speed_penalty := 0.32
@export var both_legs_speed_penalty := 0.58
@export var crawl_speed_multiplier := 0.24
@export var crawl_damage_multiplier := 0.68
@export var knockback_decay := 9.0
@export var max_knockback_speed := 7.5
@export var knockdown_damage_threshold := 32.0

const BODY_STAND_POS := Vector3(0.0, 0.98, 0.0)
const HEAD_STAND_POS := Vector3(0.0, 1.78, 0.0)
const ARM_L_STAND_POS := Vector3(-0.48, 1.05, -0.10)
const ARM_R_STAND_POS := Vector3(0.48, 1.05, -0.10)
const COLLISION_STAND_POS := Vector3(0.0, 0.95, 0.0)
const ARM_L_STAND_ROT := Vector3(72.0, 0.0, -8.0)
const ARM_R_STAND_ROT := Vector3(72.0, 0.0, 8.0)

var health := 100.0
var target: Node3D
var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var attack_timer := 0.0
var dead := false
var active := true
var ai_interval := 0.08
var ai_timer := 0.0
var desired_direction := Vector3.ZERO
var gore_parts_limit := 6

var limb_hp := {}
var head_missing := false
var arm_l_missing := false
var arm_r_missing := false
var leg_l_disabled := false
var leg_r_disabled := false

var stagger_timer := 0.0
var knockdown_timer := 0.0
var external_velocity := Vector3.ZERO
var crawling := false

@onready var collision: CollisionShape3D = $Collision
@onready var body_mesh: MeshInstance3D = $Body
@onready var head_mesh: MeshInstance3D = $Head
@onready var arm_l_mesh: MeshInstance3D = $ArmL
@onready var arm_r_mesh: MeshInstance3D = $ArmR

func _ready() -> void:
	_reset_anatomy()
	target = get_tree().get_first_node_in_group("player") as Node3D
	ai_timer = randf_range(0.0, ai_interval)
	add_to_group("enemies_active")

func activate(at_position: Vector3, new_target: Node3D, new_ai_interval := 0.08, new_gore_parts := 6) -> void:
	global_position = at_position
	target = new_target
	dead = false
	active = true
	visible = true
	velocity = Vector3.ZERO
	external_velocity = Vector3.ZERO
	desired_direction = Vector3.ZERO
	stagger_timer = 0.0
	knockdown_timer = 0.0
	crawling = false
	ai_interval = maxf(new_ai_interval, 0.03)
	gore_parts_limit = clampi(new_gore_parts, 0, 6)
	ai_timer = randf_range(0.0, ai_interval)
	_reset_anatomy()
	if not is_in_group("enemies_active"):
		add_to_group("enemies_active")
	collision.set_deferred("disabled", false)
	set_physics_process(true)

func deactivate() -> void:
	active = false
	dead = true
	visible = false
	velocity = Vector3.ZERO
	external_velocity = Vector3.ZERO
	if is_in_group("enemies_active"):
		remove_from_group("enemies_active")
	collision.set_deferred("disabled", true)
	set_physics_process(false)

func set_performance_profile(new_ai_interval: float, new_gore_parts: int) -> void:
	ai_interval = maxf(new_ai_interval, 0.03)
	gore_parts_limit = clampi(new_gore_parts, 0, 6)

func _reset_anatomy() -> void:
	health = max_health
	limb_hp = {
		"head": head_health,
		"arm_l": arm_health,
		"arm_r": arm_health,
		"leg_l": leg_health,
		"leg_r": leg_health
	}
	head_missing = false
	arm_l_missing = false
	arm_r_missing = false
	leg_l_disabled = false
	leg_r_disabled = false
	crawling = false
	stagger_timer = 0.0
	knockdown_timer = 0.0
	external_velocity = Vector3.ZERO
	_restore_standing_visual()
	if is_instance_valid(head_mesh):
		head_mesh.visible = true
	if is_instance_valid(arm_l_mesh):
		arm_l_mesh.visible = true
	if is_instance_valid(arm_r_mesh):
		arm_r_mesh.visible = true

func _physics_process(delta: float) -> void:
	if dead or not active:
		return
	attack_timer = maxf(attack_timer - delta, 0.0)
	stagger_timer = maxf(stagger_timer - delta, 0.0)
	var was_knocked_down := knockdown_timer > 0.0
	knockdown_timer = maxf(knockdown_timer - delta, 0.0)
	if was_knocked_down and knockdown_timer <= 0.0 and not crawling:
		_restore_standing_visual()

	ai_timer -= delta
	if ai_timer <= 0.0:
		ai_timer = ai_interval
		_update_ai_direction()
	if not is_on_floor():
		velocity.y -= gravity * delta

	var locomotion := Vector3.ZERO
	if stagger_timer <= 0.0 and knockdown_timer <= 0.0:
		locomotion = desired_direction * _current_move_speed()
	velocity.x = move_toward(velocity.x, locomotion.x + external_velocity.x, acceleration * delta)
	velocity.z = move_toward(velocity.z, locomotion.z + external_velocity.z, acceleration * delta)
	external_velocity = external_velocity.move_toward(Vector3.ZERO, knockback_decay * delta)
	move_and_slide()

func _current_move_speed() -> float:
	if crawling:
		return move_speed * crawl_speed_multiplier
	if leg_l_disabled and leg_r_disabled:
		return move_speed * (1.0 - both_legs_speed_penalty)
	if leg_l_disabled or leg_r_disabled:
		return move_speed * (1.0 - leg_speed_penalty)
	return move_speed

func _update_ai_direction() -> void:
	if target == null or not is_instance_valid(target):
		target = get_tree().get_first_node_in_group("player") as Node3D
		return
	var to_target := target.global_position - global_position
	to_target.y = 0.0
	var chase := to_target.normalized() if to_target.length() > 0.05 else Vector3.ZERO
	var separation := Vector3.ZERO
	var neighbors_checked := 0
	for other in get_tree().get_nodes_in_group("enemies_active"):
		if other == self or not (other is Node3D):
			continue
		var offset: Vector3 = global_position - other.global_position
		offset.y = 0.0
		var distance := offset.length()
		if distance > 0.001 and distance < separation_radius:
			separation += offset.normalized() * (1.0 - distance / separation_radius)
			neighbors_checked += 1
			if neighbors_checked >= 6:
				break
	desired_direction = (chase + separation * separation_strength).normalized()
	if desired_direction.length_squared() > 0.001 and knockdown_timer <= 0.0:
		look_at(global_position + Vector3(desired_direction.x, 0.0, desired_direction.z), Vector3.UP)

	var attack_range := 1.05 if crawling else 1.25
	if to_target.length() < attack_range and attack_timer <= 0.0 and stagger_timer <= 0.0 and knockdown_timer <= 0.0:
		attack_timer = attack_cooldown * (1.35 if crawling else 1.0)
		if target.has_method("apply_damage"):
			var push_direction := target.global_position - global_position
			push_direction.y = 0.0
			var arm_factor := 1.0
			if arm_l_missing and arm_r_missing:
				arm_factor = 0.45
			elif arm_l_missing or arm_r_missing:
				arm_factor = 0.72
			var crawl_factor := crawl_damage_multiplier if crawling else 1.0
			target.apply_damage(contact_damage * arm_factor * crawl_factor, push_direction)

func apply_hit(hit_point: Vector3, shot_direction: Vector3, base_damage := 34.0, damage_type := "ballistic", impact_force := 1.0) -> void:
	if dead or not active:
		return
	var local_hit := to_local(hit_point)
	var zone := _zone_from_local_hit(local_hit)
	var multiplier := _zone_multiplier(zone)
	var damage := base_damage * multiplier
	var limb_damage := damage
	if damage_type == "shotgun":
		limb_damage *= 1.35
	elif damage_type == "heavy":
		limb_damage *= 1.6

	_apply_impact_reaction(zone, damage, shot_direction, damage_type, impact_force)

	if zone == "head" and not head_missing:
		_damage_limb("head", limb_damage, shot_direction)
	elif zone == "arm_l" and not arm_l_missing:
		_damage_limb("arm_l", limb_damage, shot_direction)
	elif zone == "arm_r" and not arm_r_missing:
		_damage_limb("arm_r", limb_damage, shot_direction)
	elif zone == "leg_l" and not leg_l_disabled:
		_damage_limb("leg_l", limb_damage, shot_direction)
	elif zone == "leg_r" and not leg_r_disabled:
		_damage_limb("leg_r", limb_damage, shot_direction)

	if dead:
		return
	health -= damage
	if health <= 0.0:
		_die(shot_direction, zone)

func _apply_impact_reaction(zone: String, damage: float, shot_direction: Vector3, damage_type: String, impact_force: float) -> void:
	var stagger_duration := 0.12
	match zone:
		"head":
			stagger_duration = 0.32
		"leg_l", "leg_r":
			stagger_duration = 0.24
		"torso":
			stagger_duration = 0.18
		_:
			stagger_duration = 0.13
	if damage_type == "shotgun":
		stagger_duration += 0.10
	elif damage_type == "heavy":
		stagger_duration += 0.18
	stagger_timer = maxf(stagger_timer, stagger_duration)
	staggered.emit(self, stagger_duration)

	var horizontal_direction := shot_direction
	horizontal_direction.y = 0.0
	if horizontal_direction.length_squared() > 0.001:
		horizontal_direction = horizontal_direction.normalized()
	var force_scale := clampf((damage / 24.0) * impact_force, 0.35, max_knockback_speed)
	if damage_type == "shotgun":
		force_scale *= 1.25
	elif damage_type == "heavy":
		force_scale *= 1.55
	external_velocity += horizontal_direction * force_scale
	if external_velocity.length() > max_knockback_speed:
		external_velocity = external_velocity.normalized() * max_knockback_speed

	var should_fall := damage >= knockdown_damage_threshold
	should_fall = should_fall or (damage_type == "shotgun" and damage >= 20.0 and zone != "arm_l" and zone != "arm_r")
	should_fall = should_fall or damage_type == "heavy"
	if should_fall and not crawling:
		_knock_down(0.78 if damage_type == "shotgun" else 0.62)

func _knock_down(duration: float) -> void:
	if dead or crawling:
		return
	knockdown_timer = maxf(knockdown_timer, duration)
	stagger_timer = maxf(stagger_timer, duration * 0.55)
	_set_fallen_visual()
	knocked_down.emit(self, duration)

func _zone_from_local_hit(local_hit: Vector3) -> String:
	if local_hit.y > 1.38:
		return "head"
	if local_hit.y > 0.78:
		if local_hit.x < -0.24:
			return "arm_l"
		if local_hit.x > 0.24:
			return "arm_r"
		return "torso"
	if local_hit.y < 0.52:
		return "leg_l" if local_hit.x < 0.0 else "leg_r"
	return "torso"

func _zone_multiplier(zone: String) -> float:
	match zone:
		"head":
			return 2.4
		"arm_l", "arm_r":
			return 0.85
		"leg_l", "leg_r":
			return 0.75
		_:
			return 1.0

func _damage_limb(limb: String, amount: float, shot_direction: Vector3) -> void:
	if not limb_hp.has(limb):
		return
	limb_hp[limb] = float(limb_hp[limb]) - amount
	if float(limb_hp[limb]) > 0.0:
		return
	_sever_limb(limb, shot_direction)

func _sever_limb(limb: String, shot_direction: Vector3) -> void:
	match limb:
		"head":
			if head_missing:
				return
			head_missing = true
			head_mesh.visible = false
			_spawn_single_gib(HEAD_STAND_POS, Vector3(0.42, 0.42, 0.42), 1.2, shot_direction)
			limb_lost.emit(self, limb)
			_die(shot_direction, "head")
		"arm_l":
			if arm_l_missing:
				return
			arm_l_missing = true
			arm_l_mesh.visible = false
			_spawn_single_gib(ARM_L_STAND_POS, Vector3(0.18, 0.72, 0.18), 1.1, shot_direction)
			limb_lost.emit(self, limb)
		"arm_r":
			if arm_r_missing:
				return
			arm_r_missing = true
			arm_r_mesh.visible = false
			_spawn_single_gib(ARM_R_STAND_POS, Vector3(0.18, 0.72, 0.18), 1.1, shot_direction)
			limb_lost.emit(self, limb)
		"leg_l":
			if leg_l_disabled:
				return
			leg_l_disabled = true
			_spawn_single_gib(Vector3(-0.18, 0.30, 0.0), Vector3(0.24, 0.70, 0.26), 1.7, shot_direction)
			limb_lost.emit(self, limb)
			_on_leg_state_changed()
		"leg_r":
			if leg_r_disabled:
				return
			leg_r_disabled = true
			_spawn_single_gib(Vector3(0.18, 0.30, 0.0), Vector3(0.24, 0.70, 0.26), 1.7, shot_direction)
			limb_lost.emit(self, limb)
			_on_leg_state_changed()

func _on_leg_state_changed() -> void:
	if leg_l_disabled and leg_r_disabled:
		_enter_crawl()
	else:
		stagger_timer = maxf(stagger_timer, 0.45)
		_knock_down(0.52)

func _enter_crawl() -> void:
	if crawling or dead:
		return
	crawling = true
	knockdown_timer = 0.0
	stagger_timer = maxf(stagger_timer, 0.30)
	_set_crawl_visual()
	crawl_started.emit(self)

func _set_fallen_visual() -> void:
	if crawling:
		return
	body_mesh.position = Vector3(0.0, 0.48, 0.0)
	body_mesh.rotation_degrees = Vector3(0.0, 0.0, 72.0)
	if not head_missing:
		head_mesh.position = Vector3(0.48, 0.54, 0.0)
	if not arm_l_missing:
		arm_l_mesh.position = Vector3(-0.10, 0.52, -0.18)
	if not arm_r_missing:
		arm_r_mesh.position = Vector3(0.10, 0.52, 0.18)
	collision.position = Vector3(0.0, 0.52, 0.0)

func _set_crawl_visual() -> void:
	body_mesh.position = Vector3(0.0, 0.42, 0.0)
	body_mesh.rotation_degrees = Vector3(72.0, 0.0, 0.0)
	if not head_missing:
		head_mesh.position = Vector3(0.0, 0.62, -0.46)
	if not arm_l_missing:
		arm_l_mesh.position = Vector3(-0.34, 0.42, -0.34)
		arm_l_mesh.rotation_degrees = Vector3(88.0, 0.0, -20.0)
	if not arm_r_missing:
		arm_r_mesh.position = Vector3(0.34, 0.42, -0.34)
		arm_r_mesh.rotation_degrees = Vector3(88.0, 0.0, 20.0)
	collision.position = Vector3(0.0, 0.46, 0.0)

func _restore_standing_visual() -> void:
	if not is_instance_valid(body_mesh):
		return
	body_mesh.position = BODY_STAND_POS
	body_mesh.rotation_degrees = Vector3.ZERO
	if is_instance_valid(head_mesh):
		head_mesh.position = HEAD_STAND_POS
		head_mesh.rotation_degrees = Vector3.ZERO
	if is_instance_valid(arm_l_mesh):
		arm_l_mesh.position = ARM_L_STAND_POS
		arm_l_mesh.rotation_degrees = ARM_L_STAND_ROT
	if is_instance_valid(arm_r_mesh):
		arm_r_mesh.position = ARM_R_STAND_POS
		arm_r_mesh.rotation_degrees = ARM_R_STAND_ROT
	if is_instance_valid(collision):
		collision.position = COLLISION_STAND_POS

func _spawn_single_gib(offset: Vector3, size: Vector3, mass_value: float, shot_direction: Vector3) -> void:
	if gore_parts_limit <= 0:
		return
	var root := get_tree().current_scene
	if root == null:
		return
	var body := RigidBody3D.new()
	body.add_to_group("gib")
	body.mass = mass_value
	body.global_position = global_position + offset
	body.rotation = rotation
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh_instance.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.28, 0.45, 0.22)
	mesh_instance.material_override = mat
	body.add_child(mesh_instance)
	var shape_node := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	shape_node.shape = shape
	body.add_child(shape_node)
	root.add_child(body)
	body.apply_central_impulse((shot_direction.normalized() * 5.0 + Vector3.UP * 1.6) * mass_value)
	body.apply_torque_impulse(Vector3(randf_range(-2.0, 2.0), randf_range(-2.0, 2.0), randf_range(-2.0, 2.0)))
	root.get_tree().create_timer(gib_lifetime).timeout.connect(body.queue_free)

func _die(shot_direction: Vector3, zone: String) -> void:
	if dead:
		return
	dead = true
	_spawn_physics_parts(shot_direction, zone)
	died.emit(self)

func _spawn_physics_parts(shot_direction: Vector3, zone: String) -> void:
	if gore_parts_limit <= 0:
		return
	var root := get_tree().current_scene
	if root == null:
		return
	var parts := []
	if not head_missing:
		parts.append({"offset": HEAD_STAND_POS, "size": Vector3(0.42, 0.42, 0.42), "mass": 1.2})
	parts.append({"offset": BODY_STAND_POS, "size": Vector3(0.62, 0.75, 0.34), "mass": 4.0})
	if not arm_l_missing:
		parts.append({"offset": ARM_L_STAND_POS, "size": Vector3(0.18, 0.72, 0.18), "mass": 1.2})
	if not arm_r_missing:
		parts.append({"offset": ARM_R_STAND_POS, "size": Vector3(0.18, 0.72, 0.18), "mass": 1.2})
	if not leg_l_disabled:
		parts.append({"offset": Vector3(-0.18, 0.30, 0), "size": Vector3(0.24, 0.70, 0.26), "mass": 1.8})
	if not leg_r_disabled:
		parts.append({"offset": Vector3(0.18, 0.30, 0), "size": Vector3(0.24, 0.70, 0.26), "mass": 1.8})
	var count := mini(gore_parts_limit, parts.size())
	for i in count:
		var data: Dictionary = parts[i]
		var body := RigidBody3D.new()
		body.add_to_group("gib")
		body.mass = data.mass
		body.global_position = global_position + data.offset
		body.rotation = rotation
		body.linear_damp = 0.15
		body.angular_damp = 0.1
		var mesh_instance := MeshInstance3D.new()
		var mesh := BoxMesh.new()
		mesh.size = data.size
		mesh_instance.mesh = mesh
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.32, 0.48, 0.27)
		mesh_instance.material_override = mat
		body.add_child(mesh_instance)
		var shape_node := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = data.size
		shape_node.shape = shape
		body.add_child(shape_node)
		root.add_child(body)
		var extra := 1.8 if zone == "head" else 1.0
		body.apply_central_impulse((shot_direction.normalized() * 4.8 + Vector3.UP * 2.0) * data.mass * extra)
		body.apply_torque_impulse(Vector3(randf_range(-2.0, 2.0), randf_range(-2.0, 2.0), randf_range(-2.0, 2.0)))
		root.get_tree().create_timer(gib_lifetime).timeout.connect(body.queue_free)
