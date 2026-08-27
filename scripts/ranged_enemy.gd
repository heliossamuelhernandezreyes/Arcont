extends CharacterBody3D

signal died(enemy: Node)
@export var max_health := 120.0
@export var move_speed := 3.6
@export var preferred_distance := 13.0
@export var fire_range := 24.0
@export var fire_interval := 1.15
@export var shot_damage := 16.0
@export var accuracy_spread := 0.04
@export var penetration_energy := 0.72
var health := 120.0
var player: Node3D
var fire_timer := 0.0
var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var active := true

func _ready() -> void:
	health = max_health
	player = get_tree().get_first_node_in_group("player") as Node3D
	add_to_group("ranged_enemy")
	add_to_group("enemies_active")

func _physics_process(delta: float) -> void:
	if not active:
		return
	if player == null or not is_instance_valid(player):
		player = get_tree().get_first_node_in_group("player") as Node3D
		return
	fire_timer = maxf(fire_timer - delta, 0.0)
	if not is_on_floor():
		velocity.y -= gravity * delta
	var flat := player.global_position - global_position
	flat.y = 0.0
	var distance := flat.length()
	var desired := Vector3.ZERO
	if distance > preferred_distance + 2.5:
		desired = flat.normalized() * move_speed
	elif distance < preferred_distance - 2.5:
		desired = -flat.normalized() * move_speed * 0.7
	velocity.x = move_toward(velocity.x, desired.x, 8.0 * delta)
	velocity.z = move_toward(velocity.z, desired.z, 8.0 * delta)
	if flat.length_squared() > 0.1:
		look_at(global_position + flat, Vector3.UP)
	move_and_slide()
	if distance <= fire_range and fire_timer <= 0.0:
		_try_fire()

func _try_fire() -> void:
	var world := get_world_3d()
	if world == null or player == null:
		return
	fire_timer = fire_interval
	var origin := global_position + Vector3.UP * 1.25
	var aim := player.global_position + Vector3.UP * 0.65
	aim += Vector3(randf_range(-accuracy_spread, accuracy_spread), randf_range(-accuracy_spread, accuracy_spread), randf_range(-accuracy_spread, accuracy_spread)) * origin.distance_to(aim)
	var direction := (aim - origin).normalized()
	_trace_round(world.direct_space_state, origin, direction)

func _trace_round(space_state: PhysicsDirectSpaceState3D, origin: Vector3, direction: Vector3) -> void:
	var energy := penetration_energy
	var current_origin := origin
	var exclude: Array[RID] = [get_rid()]
	for _pass in 2:
		var query := PhysicsRayQueryParameters3D.create(current_origin, current_origin + direction * fire_range)
		query.exclude = exclude
		query.collide_with_areas = false
		var result := space_state.intersect_ray(query)
		if result.is_empty():
			return
		var collider: Object = result.get("collider")
		var hit_point: Vector3 = result.get("position", current_origin)
		if collider == player and player.has_method("apply_damage"):
			var scale := Ballistics.damage_scale(energy, penetration_energy)
			player.apply_damage(shot_damage * scale, direction, _pick_hit_zone(), scale)
			return
		Ballistics.apply_surface_damage(collider, shot_damage, energy)
		var new_energy := Ballistics.energy_after_surface(energy, collider)
		if new_energy <= 0.05:
			return
		energy = new_energy
		if collider is CollisionObject3D:
			exclude.append((collider as CollisionObject3D).get_rid())
		current_origin = hit_point + direction * (Ballistics.thickness_for(collider) + 0.08)

func _pick_hit_zone() -> String:
	var roll := randf()
	if roll < 0.08:
		return "head"
	if roll < 0.58:
		return "torso"
	if roll < 0.73:
		return "left_arm"
	if roll < 0.88:
		return "right_arm"
	return "left_leg" if randf() < 0.5 else "right_leg"

func apply_hit(_hit_point: Vector3, direction: Vector3, amount: float, _weapon_type := "shotgun", impact_force := 1.0) -> void:
	if not active:
		return
	health = maxf(health - amount, 0.0)
	velocity += direction.normalized() * impact_force * 0.12
	if health <= 0.0:
		active = false
		remove_from_group("enemies_active")
		died.emit(self)
		queue_free()
