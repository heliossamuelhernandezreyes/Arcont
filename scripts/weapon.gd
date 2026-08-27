extends Node

signal ammo_changed(current: int, reserve: int, magazine_size: int)
signal reload_state_changed(active: bool)
signal recoil_requested(pitch: float, yaw: float)
signal shot_fired

@export var damage := 34.0
@export var fire_interval := 0.16
@export var magazine_size := 24
@export var reserve_ammo := 144
@export var reload_time := 1.45
@export var recoil_pitch := 0.018
@export var recoil_yaw := 0.006

@onready var camera: Camera3D = get_parent() as Camera3D
@onready var ray: RayCast3D = $"../RayCast3D"

var ammo_in_mag := 24
var fire_timer := 0.0
var reload_timer := 0.0
var reloading := false

func _ready() -> void:
	ammo_in_mag = magazine_size
	ammo_changed.emit(ammo_in_mag, reserve_ammo, magazine_size)

func _process(delta: float) -> void:
	fire_timer = max(fire_timer - delta, 0.0)
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

	ray.force_raycast_update()
	if ray.is_colliding():
		var collider := ray.get_collider()
		var hit_point := ray.get_collision_point()
		var shot_direction := -camera.global_transform.basis.z
		if collider and collider.has_method("apply_hit"):
			collider.apply_hit(hit_point, shot_direction, damage)
		else:
			print("ARCONT impact: ", collider)
	return true

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
