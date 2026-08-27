extends Node

var host: CharacterBody3D
var body: Node3D
var head: Node3D
var arm_l: Node3D
var arm_r: Node3D
var weapon: Node3D
var core: Node3D
var budget: Node
var phase := 0.0
var update_accumulator := 0.0
var sway_bias := 1.0
var pulse_bias := 1.0

func _ready() -> void:
	host = get_parent() as CharacterBody3D
	body = host.get_node_or_null("Body") as Node3D
	head = host.get_node_or_null("Head") as Node3D
	arm_l = host.get_node_or_null("ArmL") as Node3D
	arm_r = host.get_node_or_null("ArmR") as Node3D
	weapon = host.get_node_or_null("Weapon") as Node3D
	core = host.get_node_or_null("Body/Core") as Node3D
	var scene := get_tree().current_scene
	if scene: budget = scene.get_node_or_null("PerformanceBudget")
	phase = randf_range(0.0, TAU)
	sway_bias = randf_range(0.88, 1.14)
	pulse_bias = randf_range(0.90, 1.18)

func _process(delta: float) -> void:
	if host == null or not is_instance_valid(host): return
	update_accumulator += delta
	var interval := _quality_interval()
	if interval > 0.0 and update_accumulator < interval: return
	var step := update_accumulator if interval > 0.0 else delta
	update_accumulator = 0.0
	var quality := _quality()
	phase += step * 2.4 * sway_bias
	var speed := Vector2(host.velocity.x, host.velocity.z).length()
	var stride := sin(phase * (1.0 + speed * 0.28))
	if body:
		var bob_amp := 0.006 if quality == 0 else (0.012 if quality == 1 else 0.018)
		body.position.y = 0.15 + sin(phase * 1.2) * bob_amp
		body.rotation_degrees.z = stride * minf(3.0 if quality >= 1 else 1.2, speed * 0.65) * sway_bias
	if head and quality >= 1:
		head.rotation_degrees.y = sin(phase * 0.37) * (7.0 if quality == 2 else 3.5) * sway_bias
		head.rotation_degrees.z = sin(phase * 0.53) * (2.5 if quality == 2 else 1.2)
	if arm_l: arm_l.rotation_degrees.x = 14.0 + stride * minf(16.0, 4.0 + speed * 3.0) * sway_bias
	if arm_r: arm_r.rotation_degrees.x = 14.0 - stride * minf(16.0, 4.0 + speed * 3.0) / sway_bias
	var charging := bool(host.get("charging"))
	if weapon:
		weapon.rotation_degrees.x = lerpf(weapon.rotation_degrees.x, -16.0 if charging else -8.0, minf(step * 8.0, 1.0))
		weapon.rotation_degrees.z = lerpf(weapon.rotation_degrees.z, -3.0 if charging else -7.0, minf(step * 8.0, 1.0))
	if core and quality >= 1:
		var amp := (0.12 if charging else 0.04) * pulse_bias
		if quality == 1: amp *= 0.55
		var pulse := 1.0 + sin(phase * (3.4 if charging else 1.6)) * amp
		core.scale = Vector3.ONE * pulse

func _quality() -> int:
	if budget and budget.has_method("get_animation_quality"): return int(budget.get_animation_quality())
	return 1 if OS.has_feature("mobile") else 2

func _quality_interval() -> float:
	if budget and budget.has_method("get_animation_update_interval"): return float(budget.get_animation_update_interval())
	return 1.0 / 30.0 if OS.has_feature("mobile") else 0.0
