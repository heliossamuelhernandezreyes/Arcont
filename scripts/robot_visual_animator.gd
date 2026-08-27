extends Node

var host: CharacterBody3D
var body: Node3D
var wheel_l: Node3D
var wheel_r: Node3D
var turret: Node3D
var optic: Node3D
var budget: Node
var phase := 0.0
var update_accumulator := 0.0
var suspension_bias := 1.0
var idle_scan_bias := 1.0

func _ready() -> void:
	host = get_parent() as CharacterBody3D
	body = host.get_node_or_null("Body") as Node3D
	wheel_l = host.get_node_or_null("WheelL") as Node3D
	wheel_r = host.get_node_or_null("WheelR") as Node3D
	turret = host.get_node_or_null("Turret") as Node3D
	optic = host.get_node_or_null("Turret/Optic") as Node3D
	var scene := get_tree().current_scene
	if scene: budget = scene.get_node_or_null("PerformanceBudget")
	phase = randf_range(0.0, TAU)
	suspension_bias = randf_range(0.88, 1.12)
	idle_scan_bias = randf_range(0.85, 1.15)

func _process(delta: float) -> void:
	if host == null or not is_instance_valid(host): return
	update_accumulator += delta
	var interval := _quality_interval()
	if interval > 0.0 and update_accumulator < interval: return
	var step := update_accumulator if interval > 0.0 else delta
	update_accumulator = 0.0
	var quality := _quality()
	var speed := Vector2(host.velocity.x, host.velocity.z).length()
	phase += step * (2.0 + speed * 2.6)
	if wheel_l: wheel_l.rotate_x(speed * step * 4.2)
	if wheel_r: wheel_r.rotate_x(speed * step * 4.2)
	if body:
		var bob_amp := (0.004 if quality == 0 else 0.012) * suspension_bias
		body.position.y = 0.66 + sin(phase) * minf(bob_amp, speed * 0.0025)
		body.rotation_degrees.z = sin(phase * 0.5) * minf(1.5 if quality >= 1 else 0.65, speed * 0.22) * suspension_bias
	if turret and speed < 0.2 and quality >= 1:
		turret.rotation_degrees.z = sin(phase * 0.28 * idle_scan_bias) * (1.4 if quality == 2 else 0.75)
	if optic and quality >= 1:
		var pulse := 1.0 + sin(phase * 1.7) * (0.04 if quality == 2 else 0.02)
		optic.scale = Vector3.ONE * pulse

func _quality() -> int:
	if budget and budget.has_method("get_animation_quality"): return int(budget.get_animation_quality())
	return 1 if OS.has_feature("mobile") else 2

func _quality_interval() -> float:
	if budget and budget.has_method("get_animation_update_interval"): return float(budget.get_animation_update_interval())
	return 1.0 / 30.0 if OS.has_feature("mobile") else 0.0
