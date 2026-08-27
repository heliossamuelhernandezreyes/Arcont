extends Node

signal ammo_changed(current: int, reserve: int, magazine_size: int)
signal reload_state_changed(active: bool)
signal recoil_requested(pitch: float, yaw: float)
signal shot_fired
signal impact_feedback(hit_point: Vector3, hit_normal: Vector3, organic: bool)

@export var weapon_name := "Prototype Shotgun"
@export var damage := 18.0
@export var fire_interval := 0.72
@export var magazine_size := 8
@export var reserve_ammo := 48
@export var reload_time := 1.9
@export var recoil_pitch := 0.055
@export var recoil_yaw := 0.016
@export var pellets := 8
@export var spread_degrees := 5.2
@export var range := 55.0
@export var impact_force := 8.5
@export var penetration_energy := 0.95
@export var max_penetrations := 2

@onready var camera: Camera3D = get_parent() as Camera3D
var ammo_in_mag := 8
var fire_timer := 0.0
var reload_timer := 0.0
var reloading := false

func _ready() -> void:
	ammo_in_mag = magazine_size
	ammo_changed.emit(ammo_in_mag, reserve_ammo, magazine_size)

func _process(delta: float) -> void:
	fire_timer = maxf(fire_timer - delta, 0.0)
	if reloading:
		reload_timer -= delta
		if reload_timer <= 0.0: _finish_reload()

func try_fire() -> bool:
	if reloading or fire_timer > 0.0: return false
	if ammo_in_mag <= 0:
		request_reload()
		return false
	fire_timer = fire_interval
	ammo_in_mag -= 1
	ammo_changed.emit(ammo_in_mag, reserve_ammo, magazine_size)
	shot_fired.emit()
	var handling := _player_controller()
	var recoil_mult := 1.0
	if handling and handling.has_method("get_recoil_multiplier"): recoil_mult = float(handling.get_recoil_multiplier())
	recoil_requested.emit(recoil_pitch * recoil_mult, randf_range(-recoil_yaw, recoil_yaw) * recoil_mult)
	_fire_shotgun()
	return true

func _fire_shotgun() -> void:
	var world := camera.get_world_3d()
	if world == null: return
	var origin := camera.global_position
	var forward := -camera.global_transform.basis.z
	var right := camera.global_transform.basis.x
	var up := camera.global_transform.basis.y
	var spread_mult := 1.0
	var handling := _player_controller()
	if handling and handling.has_method("get_weapon_spread_multiplier"): spread_mult = float(handling.get_weapon_spread_multiplier())
	var spread := tan(deg_to_rad(spread_degrees * spread_mult))
	var player := handling as CollisionObject3D
	var exclude: Array[RID] = []
	if player: exclude.append(player.get_rid())
	for _i in pellets:
		var direction := (forward + right * randf_range(-spread, spread) + up * randf_range(-spread, spread)).normalized()
		_trace_pellet(world.direct_space_state, origin, direction, exclude)

func _trace_pellet(space_state: PhysicsDirectSpaceState3D, origin: Vector3, direction: Vector3, exclude: Array[RID]) -> void:
	var energy := penetration_energy
	var current_origin := origin
	var travelled := 0.0
	var penetrations := 0
	var local_exclude := exclude.duplicate()
	while energy > 0.05 and travelled < range:
		var remaining := range - travelled
		var query := PhysicsRayQueryParameters3D.create(current_origin, current_origin + direction * remaining)
		query.exclude = local_exclude
		query.collide_with_areas = false
		var result := space_state.intersect_ray(query)
		if result.is_empty(): return
		var collider: Object = result.get("collider")
		var hit_point: Vector3 = result.get("position", current_origin)
		var hit_normal: Vector3 = result.get("normal", -direction)
		travelled += current_origin.distance_to(hit_point)
		var organic := bool(collider != null and collider.has_method("apply_hit"))
		impact_feedback.emit(hit_point, hit_normal, organic)
		if organic:
			var scale := Ballistics.damage_scale(energy, penetration_energy)
			collider.apply_hit(hit_point, direction, damage * scale, "shotgun", impact_force * scale)
			return
		Ballistics.apply_surface_damage(collider, damage, energy, hit_point, direction)
		var new_energy := Ballistics.energy_after_surface(energy, collider)
		if new_energy <= 0.05 or penetrations >= max_penetrations: return
		energy = new_energy
		penetrations += 1
		if collider is CollisionObject3D: local_exclude.append((collider as CollisionObject3D).get_rid())
		var skip_distance := Ballistics.thickness_for(collider) + 0.08
		current_origin = hit_point + direction * skip_distance
		travelled += skip_distance

func _player_controller() -> Node:
	var node: Node = camera
	for _i in 4:
		if node == null: break
		if node.is_in_group("player"): return node
		node = node.get_parent()
	return null

func request_reload() -> bool:
	if reloading or ammo_in_mag >= magazine_size or reserve_ammo <= 0: return false
	reloading = true
	var reload_mult := 1.0
	var handling := _player_controller()
	if handling and handling.has_method("get_reload_time_multiplier"): reload_mult = float(handling.get_reload_time_multiplier())
	reload_timer = reload_time * reload_mult
	reload_state_changed.emit(true)
	return true

func _finish_reload() -> void:
	var moved := mini(magazine_size - ammo_in_mag, reserve_ammo)
	ammo_in_mag += moved
	reserve_ammo -= moved
	reloading = false
	reload_timer = 0.0
	reload_state_changed.emit(false)
	ammo_changed.emit(ammo_in_mag, reserve_ammo, magazine_size)

func cancel_reload() -> void:
	if not reloading: return
	reloading = false
	reload_timer = 0.0
	reload_state_changed.emit(false)

func add_ammo(amount: int) -> void:
	if amount <= 0: return
	reserve_ammo += amount
	ammo_changed.emit(ammo_in_mag, reserve_ammo, magazine_size)
