extends CharacterBody3D

signal died(enemy: Node)
@export var max_health := 120.0
@export var move_speed := 3.6
@export var preferred_distance := 13.0
@export var fire_range := 24.0
@export var fire_interval := 1.15
@export var shot_damage := 16.0
@export var accuracy_spread := 0.04
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
	if not active: return
	if player == null or not is_instance_valid(player):
		player = get_tree().get_first_node_in_group("player") as Node3D
		return
	fire_timer = maxf(fire_timer-delta,0.0)
	if not is_on_floor(): velocity.y -= gravity*delta
	var to_player := player.global_position-global_position
	var flat := Vector3(to_player.x,0.0,to_player.z)
	var distance := flat.length()
	var desired := Vector3.ZERO
	if distance > preferred_distance+2.5: desired = flat.normalized()*move_speed
	elif distance < preferred_distance-2.5: desired = -flat.normalized()*move_speed*0.7
	velocity.x = move_toward(velocity.x,desired.x,8.0*delta)
	velocity.z = move_toward(velocity.z,desired.z,8.0*delta)
	if flat.length_squared()>0.1: look_at(global_position+flat,Vector3.UP)
	move_and_slide()
	if distance <= fire_range and fire_timer<=0.0: _try_fire()

func _try_fire() -> void:
	var world := get_world_3d()
	if world == null or player == null: return
	var origin := global_position+Vector3.UP*1.25
	var aim := player.global_position+Vector3.UP*0.65
	aim += Vector3(randf_range(-accuracy_spread,accuracy_spread),randf_range(-accuracy_spread,accuracy_spread),randf_range(-accuracy_spread,accuracy_spread))*origin.distance_to(aim)
	var query := PhysicsRayQueryParameters3D.create(origin,aim)
	query.exclude = [get_rid()]; query.collide_with_areas = false
	var result := world.direct_space_state.intersect_ray(query)
	fire_timer = fire_interval
	if result.is_empty(): return
	var collider: Object = result.get("collider")
	if collider == player and player.has_method("apply_damage"):
		var zone := _pick_hit_zone()
		player.apply_damage(shot_damage,(player.global_position-global_position).normalized(),zone,1.0)

func _pick_hit_zone() -> String:
	var roll := randf()
	if roll < 0.08: return "head"
	if roll < 0.58: return "torso"
	if roll < 0.73: return "left_arm"
	if roll < 0.88: return "right_arm"
	return "left_leg" if randf()<0.5 else "right_leg"

func apply_hit(_hit_point: Vector3, direction: Vector3, amount: float, _weapon_type := "shotgun", impact_force := 1.0) -> void:
	if not active: return
	health = maxf(health-amount,0.0)
	velocity += direction.normalized()*impact_force*0.12
	if health<=0.0:
		active=false
		remove_from_group("enemies_active")
		died.emit(self)
		queue_free()
