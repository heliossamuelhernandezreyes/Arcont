extends CharacterBody3D

signal died(enemy: Node)

@export var max_health := 100.0
@export var move_speed := 2.4
@export var acceleration := 10.0
@export var contact_damage := 8.0
@export var attack_cooldown := 0.8

var health := 100.0
var target: Node3D
var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var attack_timer := 0.0
var dead := false

func _ready() -> void:
	health = max_health
	target = get_tree().get_first_node_in_group("player") as Node3D

func _physics_process(delta: float) -> void:
	if dead:
		return
	attack_timer = max(attack_timer - delta, 0.0)
	if not is_on_floor():
		velocity.y -= gravity * delta
	if target and is_instance_valid(target):
		var to_target := target.global_position - global_position
		to_target.y = 0.0
		if to_target.length() > 0.05:
			var dir := to_target.normalized()
			velocity.x = move_toward(velocity.x, dir.x * move_speed, acceleration * delta)
			velocity.z = move_toward(velocity.z, dir.z * move_speed, acceleration * delta)
			look_at(global_position + Vector3(dir.x, 0.0, dir.z), Vector3.UP)
		if to_target.length() < 1.25 and attack_timer <= 0.0:
			attack_timer = attack_cooldown
			# Placeholder de contacto. Más adelante se conectará a vida/armadura del jugador.
			print("ARCONT zombie attack: ", contact_damage)
	move_and_slide()

func apply_hit(hit_point: Vector3, shot_direction: Vector3, base_damage := 34.0) -> void:
	if dead:
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
	print("ARCONT hit zone=", zone, " damage=", snapped(damage, 0.1), " hp=", snapped(max(health, 0.0), 0.1))
	if health <= 0.0:
		_die(shot_direction, zone)

func _die(shot_direction: Vector3, zone: String) -> void:
	if dead:
		return
	dead = true
	died.emit(self)
	_spawn_physics_parts(shot_direction, zone)
	queue_free()

func _spawn_physics_parts(shot_direction: Vector3, zone: String) -> void:
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
	for i in parts.size():
		var data: Dictionary = parts[i]
		var body := RigidBody3D.new()
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
		var collision := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = data.size
		collision.shape = shape
		body.add_child(collision)
		root.add_child(body)
		var extra := 1.8 if zone == "head" and i == 0 else 1.0
		body.apply_central_impulse((shot_direction.normalized() * 4.8 + Vector3.UP * 2.0) * data.mass * extra)
		body.apply_torque_impulse(Vector3(randf_range(-2.0, 2.0), randf_range(-2.0, 2.0), randf_range(-2.0, 2.0)))
		var timer := root.get_tree().create_timer(8.0)
		timer.timeout.connect(body.queue_free)
