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
		if reload_timer <= 0.0:
			_finish_reload()

func try_fire() -> bool:
	if reloading or fire_timer > 0.0:
		return false
	if ammo_in_mag <= 0:
		request_reload()
		return false
	fire_timer = fire_interval
	ammo_in_mag -= 1
	ammo_changed.emit(ammo_in_mag, reserve_ammo, magazine_size)
	shot_fired.emit()
	recoil_requested.emit(recoil_pitch, randf_range(-recoil_yaw, recoil_yaw))
	_fire_shotgun()
	return true

func _fire_shotgun() -> void:
	var world := camera.get_world_3d()
	if world == null:
		return
	var space_state := world.direct_space_state
	var origin := camera.global_position
	var forward := -camera.global_transform.basis.z
	var right := camera.global_transform.basis.x
	var up := camera.global_transform.basis.y
	var spread := tan(deg_to_rad(spread_degrees))
	var player := camera.get_parent().get_parent().get_parent() as CollisionObject3D
	var exclude: Array[RID] = []
	if player:
		exclude.append(player.get_rid())
	for _i in pellets:
		var offset := right * randf_range(-spread, spread) + up * randf_range(-spread, spread)
		var direction := (forward + offset).normalized()
		var query := PhysicsRayQueryParameters3D.create(origin, origin + direction * range)
		query.exclude = exclude
		query.collide_with_areas = false
		var result := space_state.intersect_ray(query)
		if result.is_empty():
			continue
		var collider = result.get("collider")
		var hit_point: Vector3 = result.get("position", origin)
		var hit_normal: Vector3 = result.get("normal", -direction)
		var organic := collider and collider.has_method("apply_hit")
		impact_feedback.emit(hit_point, hit_normal, organic)
		if organic:
			collider.apply_hit(hit_point, direction, damage, "shotgun", impact_force)

func request_reload() -> bool:
	if reloading or ammo_in_mag >= magazine_size or reserve_ammo <= 0:
		return false
	reloading = true
	reload_timer = reload_time
	reload_state_changed.emit(true)
	return true

func _finish_reload() -> void:
	var needed := magazine_size - ammo_in_mag
	var moved := mini(needed, reserve_ammo)
	ammo_in_mag += moved
	reserve_ammo -= moved
	reloading = false
	reload_timer = 0.0
	reload_state_changed.emit(false)
	ammo_changed.emit(ammo_in_mag, reserve_ammo, magazine_size)

func cancel_reload() -> void:
	if not reloading:
		return
	reloading = false
	reload_timer = 0.0
	reload_state_changed.emit(false)
