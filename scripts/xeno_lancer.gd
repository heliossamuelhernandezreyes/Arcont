extends CharacterBody3D

signal died(enemy: Node)

@export var max_health := 180.0
@export var move_speed := 3.0
@export var preferred_distance := 17.0
@export var fire_range := 30.0
@export var fire_interval := 2.25
@export var charge_time := 0.68
@export var energy_damage := 24.0
@export var energy_power := 1.18
@export var suppression_radius := 2.6
@export var accuracy_spread := 0.022

@onready var core_light: OmniLight3D = $CoreLight
@onready var weapon_mesh: MeshInstance3D = $Weapon
var health := 180.0
var player: Node3D
var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var fire_timer := 0.8
var charging := false
var charge_remaining := 0.0
var active := true

func _ready() -> void:
	health = max_health
	player = get_tree().get_first_node_in_group("player") as Node3D
	add_to_group("xeno_enemy")
	add_to_group("enemies_active")

func _physics_process(delta: float) -> void:
	if not active: return
	if player == null or not is_instance_valid(player):
		player = get_tree().get_first_node_in_group("player") as Node3D
		return
	if not is_on_floor(): velocity.y -= gravity * delta
	fire_timer = maxf(fire_timer - delta, 0.0)
	var flat := player.global_position - global_position
	flat.y = 0.0
	var distance := flat.length()
	var desired := Vector3.ZERO
	if not charging:
		if distance > preferred_distance + 3.0: desired = flat.normalized() * move_speed
		elif distance < preferred_distance - 3.0: desired = -flat.normalized() * move_speed * 0.75
	velocity.x = move_toward(velocity.x, desired.x, 7.0 * delta)
	velocity.z = move_toward(velocity.z, desired.z, 7.0 * delta)
	if flat.length_squared() > 0.1: look_at(global_position + flat, Vector3.UP)
	move_and_slide()
	if charging:
		charge_remaining -= delta
		core_light.light_energy = lerpf(2.2, 7.0, 1.0 - clampf(charge_remaining / charge_time, 0.0, 1.0))
		if charge_remaining <= 0.0: _fire_lance()
	elif distance <= fire_range and fire_timer <= 0.0:
		_begin_charge()

func _begin_charge() -> void:
	charging = true
	charge_remaining = charge_time
	velocity.x *= 0.35
	velocity.z *= 0.35
	core_light.light_color = Color(0.86, 0.12, 1.0)
	core_light.light_energy = 2.2

func _fire_lance() -> void:
	charging = false
	fire_timer = fire_interval
	core_light.light_energy = 1.4
	if player == null: return
	var world := get_world_3d()
	if world == null: return
	var origin := global_position + Vector3.UP * 1.35
	var target := player.global_position + Vector3.UP * 0.72
	var distance := origin.distance_to(target)
	target += Vector3(randf_range(-accuracy_spread,accuracy_spread), randf_range(-accuracy_spread,accuracy_spread), randf_range(-accuracy_spread,accuracy_spread)) * distance
	var direction := (target - origin).normalized()
	_trace_energy(world.direct_space_state, origin, direction)

func _trace_energy(space_state: PhysicsDirectSpaceState3D, origin: Vector3, direction: Vector3) -> void:
	var energy := energy_power
	var current_origin := origin
	var exclude: Array[RID] = [get_rid()]
	var final_point := origin + direction * fire_range
	for _pass in 3:
		var query := PhysicsRayQueryParameters3D.create(current_origin, current_origin + direction * fire_range)
		query.exclude = exclude
		query.collide_with_areas = false
		var result := space_state.intersect_ray(query)
		if result.is_empty(): break
		var collider: Object = result.get("collider")
		var hit_point: Vector3 = result.get("position", final_point)
		final_point = hit_point
		if collider == player and player.has_method("apply_damage"):
			var scale := Ballistics.damage_scale(energy, energy_power)
			player.apply_damage(energy_damage * scale, direction, _pick_hit_zone(), 1.15 * scale)
			if player.has_method("apply_suppression"): player.apply_suppression(0.92, 1.05)
			break
		Ballistics.apply_energy_surface_damage(collider, energy_damage, energy, hit_point, direction)
		var next_energy := Ballistics.xeno_energy_after_surface(energy, collider)
		if next_energy <= 0.08: break
		energy = next_energy
		if collider is CollisionObject3D: exclude.append((collider as CollisionObject3D).get_rid())
		current_origin = hit_point + direction * (Ballistics.thickness_for(collider) + 0.10)
	_apply_energy_suppression(origin, final_point)
	_spawn_lance_visual(origin, final_point)

func _apply_energy_suppression(from: Vector3, to: Vector3) -> void:
	if player == null or not player.has_method("apply_suppression"): return
	var point := player.global_position + Vector3.UP * 0.7
	var segment := to - from
	if segment.length_squared() <= 0.001: return
	var t := clampf((point - from).dot(segment) / segment.length_squared(), 0.0, 1.0)
	var distance := (from + segment * t).distance_to(point)
	if distance <= suppression_radius:
		player.apply_suppression(lerpf(0.30,0.82,1.0-distance/suppression_radius),0.82)

func _spawn_lance_visual(from: Vector3, to: Vector3) -> void:
	var root := get_tree().current_scene
	if root == null: return
	var length := from.distance_to(to)
	if length <= 0.05: return
	var beam := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = Vector3(0.055,0.055,length)
	beam.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.72,0.06,1.0)
	mat.emission_enabled = true
	mat.emission = Color(0.9,0.12,1.0)
	mat.emission_energy_multiplier = 4.5
	beam.material_override = mat
	root.add_child(beam)
	beam.global_position = (from + to) * 0.5
	beam.look_at(to, Vector3.UP)
	root.get_tree().create_timer(0.09).timeout.connect(beam.queue_free)

func _pick_hit_zone() -> String:
	var roll := randf()
	if roll < 0.10: return "head"
	if roll < 0.62: return "torso"
	if roll < 0.76: return "left_arm"
	if roll < 0.90: return "right_arm"
	return "left_leg" if randf() < 0.5 else "right_leg"

func apply_hit(_hit_point: Vector3, direction: Vector3, amount: float, _weapon_type := "shotgun", impact_force := 1.0) -> void:
	if not active: return
	health = maxf(health - amount, 0.0)
	velocity += direction.normalized() * impact_force * 0.08
	if health <= 0.0:
		active = false
		remove_from_group("enemies_active")
		died.emit(self)
		queue_free()
