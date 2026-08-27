extends Node3D

const ENEMY_SCENE := preload("res://scenes/enemy.tscn")

@export var first_wave_size := 8
@export var wave_growth := 4
@export var spawn_radius := 11.5
@export var time_between_waves := 2.5

var wave := 0
var alive := 0
var waiting_for_next_wave := false

@onready var player: Node3D = $Player
@onready var wave_label: Label = $HUD/Wave
@onready var alive_label: Label = $HUD/Alive

func _ready() -> void:
	player.add_to_group("player")
	_start_next_wave()

func _start_next_wave() -> void:
	if waiting_for_next_wave:
		return
	wave += 1
	var count: int = first_wave_size + (wave - 1) * wave_growth
	alive = count
	for i in count:
		_spawn_enemy(i, count)
	_update_hud()

func _spawn_enemy(index: int, total: int) -> void:
	var enemy := ENEMY_SCENE.instantiate()
	var safe_total: float = maxf(float(total), 1.0)
	var angle: float = TAU * float(index) / safe_total + randf_range(-0.18, 0.18)
	var radius: float = spawn_radius + randf_range(-1.5, 1.5)
	enemy.position = Vector3(cos(angle) * radius, 0.0, sin(angle) * radius)
	enemy.died.connect(_on_enemy_died)
	$Enemies.add_child(enemy)

func _on_enemy_died(_enemy: Node) -> void:
	alive = maxi(alive - 1, 0)
	_update_hud()
	if alive == 0 and not waiting_for_next_wave:
		waiting_for_next_wave = true
		await get_tree().create_timer(time_between_waves).timeout
		waiting_for_next_wave = false
		_start_next_wave()

func _update_hud() -> void:
	wave_label.text = "OLEADA %02d" % wave
	alive_label.text = "HOSTILES %02d" % alive
