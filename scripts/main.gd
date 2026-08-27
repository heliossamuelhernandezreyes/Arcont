extends Node3D

const ENEMY_SCENE := preload("res://scenes/enemy.tscn")

@export var first_wave_size := 8
@export var wave_growth := 4
@export var spawn_radius := 11.5
@export var time_between_waves := 2.5
@export var mobile_enemy_cap := 36
@export var desktop_enemy_cap := 64

var wave := 0
var alive := 0
var waiting_for_next_wave := false
var game_over := false
var enemy_pool: Array[Node] = []

@onready var player: Node3D = $Player
@onready var weapon: Node = $Player/Head/Camera3D/Weapon
@onready var budget: Node = $PerformanceBudget
@onready var feedback: Node = $CombatFeedback
@onready var wave_label: Label = $HUD/Wave
@onready var alive_label: Label = $HUD/Alive
@onready var health_label: Label = $HUD/Health
@onready var ammo_label: Label = $HUD/Ammo
@onready var reload_label: Label = $HUD/Reload
@onready var info_label: Label = $HUD/Info

func _ready() -> void:
	player.add_to_group("player")
	player.health_changed.connect(_on_player_health_changed)
	player.died.connect(_on_player_died)
	weapon.ammo_changed.connect(_on_ammo_changed)
	weapon.reload_state_changed.connect(_on_reload_state_changed)
	weapon.shot_fired.connect(feedback.on_shot_fired)
	weapon.impact_feedback.connect(feedback.on_hit_feedback)
	budget.profile_changed.connect(_on_performance_profile_changed)
	_on_player_health_changed(player.health, player.max_health)
	_on_ammo_changed(weapon.ammo_in_mag, weapon.reserve_ammo, weapon.magazine_size)
	_start_next_wave()

func _start_next_wave() -> void:
	if waiting_for_next_wave or game_over:
		return
	wave += 1
	var requested: int = first_wave_size + (wave - 1) * wave_growth
	var cap: int = mobile_enemy_cap if OS.has_feature("mobile") else desktop_enemy_cap
	var count: int = mini(requested, cap)
	alive = count
	for i in count:
		_spawn_enemy(i, count)
	_update_hud()

func _spawn_enemy(index: int, total: int) -> void:
	var enemy: Node
	if enemy_pool.is_empty():
		enemy = ENEMY_SCENE.instantiate()
		enemy.died.connect(_on_enemy_died)
		$Enemies.add_child(enemy)
	else:
		enemy = enemy_pool.pop_back()
	var safe_total: float = maxf(float(total), 1.0)
	var angle: float = TAU * float(index) / safe_total + randf_range(-0.18, 0.18)
	var radius: float = spawn_radius + randf_range(-1.5, 1.5)
	var spawn_position := Vector3(cos(angle) * radius, 0.0, sin(angle) * radius)
	if enemy.has_method("activate"):
		enemy.activate(spawn_position, player, budget.ai_interval, budget.gore_parts)
	else:
		enemy.position = spawn_position

func _on_enemy_died(enemy: Node) -> void:
	alive = maxi(alive - 1, 0)
	if enemy.has_method("deactivate"):
		enemy.deactivate()
	if not enemy_pool.has(enemy):
		enemy_pool.append(enemy)
	_update_hud()
	if alive == 0 and not waiting_for_next_wave and not game_over:
		waiting_for_next_wave = true
		await get_tree().create_timer(time_between_waves).timeout
		waiting_for_next_wave = false
		_start_next_wave()

func _on_performance_profile_changed(ai_interval: float, gore_parts: int) -> void:
	for enemy in get_tree().get_nodes_in_group("enemies_active"):
		if enemy.has_method("set_performance_profile"):
			enemy.set_performance_profile(ai_interval, gore_parts)

func _on_player_health_changed(current: float, maximum: float) -> void:
	health_label.text = "VIDA %03d / %03d" % [roundi(current), roundi(maximum)]

func _on_player_died() -> void:
	game_over = true
	info_label.text = "ARCONT // OPERADOR CAIDO\nReinicio manual pendiente del prototipo"
	reload_label.text = ""

func _on_ammo_changed(current: int, reserve: int, _magazine_size: int) -> void:
	ammo_label.text = "%02d / %03d" % [current, reserve]

func _on_reload_state_changed(active: bool) -> void:
	reload_label.text = "RECARGANDO..." if active else ""

func _update_hud() -> void:
	wave_label.text = "OLEADA %02d" % wave
	alive_label.text = "HOSTILES %02d" % alive
