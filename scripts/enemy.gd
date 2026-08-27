extends CharacterBody3D

signal died(enemy: Node)

@export var max_health := 100.0
@export var move_speed := 2.4
@export var acceleration := 10.0
@export var contact_damage := 8.0
@export var attack_cooldown := 0.8
@export var separation_radius := 1.15
@export var separation_strength := 1.35
@export var gib_lifetime := 6.0

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

@onready var collision: CollisionShape3D = $Collision

func _ready() -> void:
	health = max_health
	target = get_tree().get_first_node_in_group("player") as Node3D
	ai_timer = randf_range(0.0, ai_interval)
	add_to_group("enemies_active")

func activate(at_position: Vector3, new_target: Node3D, new_ai_interval := 0.08, new_gore_parts := 6) -> void:
	global_position = at_position
	target = new_target
	health = max_health
	dead = false
	active = true
	visible = true
	velocity = Vector3.ZERO
	desired_direction = Vector3.ZERO
	ai_interval = maxf(new_ai_interval, 0.03)
	gore_parts_limit = clampi(new_gore_parts, 0, 6)
	ai_timer = randf_range(0.0, ai_interval)
	if not is_in_group("enemies_active"):
		add_to_group("enemies_active")
	collision.set_deferred("disabled", false)
	set_physics_process(true)

func deactivate() -> void:
	active = false
	dead = true
	visible = false
	velocity = Vector3.ZERO
	if is_in_group("enemies_active"):
		remove_from_group("enemies_active")
	collision.set_deferred("disabled", true)
	set_physics_process(false)

func set_performance_profile(new_ai_interval: float, new_gore_parts: int) -> void:
	ai_interval = maxf(new_ai_interval, 0.03)
	gore_parts_limit = clampi(new_gore_parts, 0, 6)

func _physics_process(delta: float) -> void:
	if dead or not active:
		return
	attack_timer = maxf(attack_timer - delta, 0.0)
	ai_timer -= delta
	if ai_timer <= 0.0:
		ai_timer = ai_interval
		_update_ai_direction()
	if not is_on_floor():
		velocity.y -= gravity * delta
	velocity.x = move_toward(velocity.x, desired_direction.x * move_speed, acceleration * delta)
	velocity.z = move_toward(velocity.z, desired_direction.z * move_speed, acceleration * delta)
	move_and_slide()

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
	if desired_direction.length_squared() > 0.001:
		look_at(global_position + Vector3(desired_direction.x, 0.0, desired_direction.z), Vector3.UP)
	if to_target.length() < 1.25 and attack_timer <= 0.0:
		attack_timer = attack_cooldown
		if target.has_method("apply_damage"):
			var push_direction := target.global_position - global_position
			push_direction.y = 0.0
			target.apply_damage(contact_damage, push_direction)

func apply_hit(hit_point: Vector3, shot_direction: Vector3, base_damage := 34.0) -> void:
	if dead or not active:
		return
	var local_hit := to_local(hit_point)
	var multiplier := 1.0
	var zone := "torso"
	if local_hit.y > 0.72:
		zone = "head"
		multiplier = 2.4
	elif local_hit.y < -0.45:
		zone = "legs"
		multiplier = 0.7
	var damage := base_damage * multiplier
	health -= damage
	if health <= 0.0:
		_die(shot_direction, zone)

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
	var parts := [
		{"offset": Vector3(0, 0.72, 0), "size": Vector3(0.42, 0.42, 0.42), "mass": 1.2},
		{"offset": Vector3(0, 0.18, 0), "size": Vector3(0.62, 0.75, 0.34), "mass": 4.0},
		{"offset": Vector3(-0.42, 0.20, 0), "size": Vector3(0.20, 0.66, 0.20), "mass": 1.2},
		{"offset": Vector3(0.42, 0.20, 0), "size": Vector3(0.20, 0.66, 0.20), "mass": 1.2},
		{"offset": Vector3(-0.18, -0.58, 0), "size": Vector3(0.24, 0.82, 0.26), "mass": 1.8},
		{"offset": Vector3(0.18, -0.58, 0), "size": Vector3(0.24, 0.82, 0.26), "mass": 1.8}
	]
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
		mat.albedo_color = Color(0.32, 0.48, 0.27) if i != 0 else Color(0.42, 0.58, 0.31)
		mesh_instance.material_override = mat
		body.add_child(mesh_instance)
		var shape_node := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = data.size
		shape_node.shape = shape
		body.add_child(shape_node)
		root.add_child(body)
		var extra := 1.8 if zone == "head" and i == 0 else 1.0
		body.apply_central_impulse((shot_direction.normalized() * 4.8 + Vector3.UP * 2.0) * data.mass * extra)
		body.apply_torque_impulse(Vector3(randf_range(-2.0, 2.0), randf_range(-2.0, 2.0), randf_range(-2.0, 2.0)))
		root.get_tree().create_timer(gib_lifetime).timeout.connect(body.queue_free)
