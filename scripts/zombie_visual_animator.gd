extends Node

var host: CharacterBody3D
var body: Node3D
var head: Node3D
var arm_l: Node3D
var arm_r: Node3D
var leg_l: Node3D
var leg_r: Node3D
var jaw: Node3D
var budget: Node
var phase := 0.0
var update_accumulator := 0.0
var gait_scale := 1.0
var head_bias := 0.0
var torso_bias := 0.0
var jaw_scale := 1.0
var stride_bias := 1.0

func _ready() -> void:
	host = get_parent() as CharacterBody3D
	body = host.get_node_or_null("Body") as Node3D
	head = host.get_node_or_null("Head") as Node3D
	arm_l = host.get_node_or_null("ArmL") as Node3D
	arm_r = host.get_node_or_null("ArmR") as Node3D
	leg_l = host.get_node_or_null("Body/LegL") as Node3D
	leg_r = host.get_node_or_null("Body/LegR") as Node3D
	jaw = host.get_node_or_null("Head/Jaw") as Node3D
	var scene := get_tree().current_scene
	if scene: budget = scene.get_node_or_null("PerformanceBudget")
	phase = randf_range(0.0, TAU)
	gait_scale = randf_range(0.82, 1.18)
	head_bias = randf_range(-5.5, 5.5)
	torso_bias = randf_range(-3.5, 3.5)
	jaw_scale = randf_range(0.72, 1.28)
	stride_bias = randf_range(0.86, 1.16)

func _process(delta: float) -> void:
	if host == null or not is_instance_valid(host) or not host.visible: return
	var crawling := bool(host.get("crawling"))
	var knockdown := float(host.get("knockdown_timer"))
	if crawling or knockdown > 0.0: return
	update_accumulator += delta
	var interval := _quality_interval()
	if interval > 0.0 and update_accumulator < interval: return
	var step := update_accumulator if interval > 0.0 else delta
	update_accumulator = 0.0
	var quality := _quality()
	var speed := Vector2(host.velocity.x, host.velocity.z).length()
	phase += step * lerpf(1.4, 7.4, clampf(speed / 3.0, 0.0, 1.0)) * gait_scale
	var gait := sin(phase)
	var bob := absf(sin(phase * 0.5))
	if body:
		body.rotation_degrees.z = -4.0 + torso_bias + gait * minf(speed * 1.6 * stride_bias, 4.5)
		body.position.y = 0.98 + bob * minf(speed * 0.012, 0.025)
	if head and not bool(host.get("head_missing")):
		var yaw_amp := 2.0 if quality == 0 else (4.0 if quality == 1 else 7.0)
		head.rotation_degrees = Vector3(8.0 + sin(phase * 0.55) * 2.5, -7.0 + head_bias + sin(phase * 0.32) * yaw_amp, -5.0 + gait * 2.2)
	if arm_l and not bool(host.get("arm_l_missing")):
		arm_l.rotation_degrees.x = 72.0 + gait * minf(18.0, 5.0 + speed * 4.0) * stride_bias
	if arm_r and not bool(host.get("arm_r_missing")):
		arm_r.rotation_degrees.x = 72.0 - gait * minf(18.0, 5.0 + speed * 4.0) / stride_bias
	if leg_l:
		leg_l.rotation_degrees.x = -gait * minf(24.0, speed * 7.0) * stride_bias
		leg_l.visible = not bool(host.get("leg_l_disabled"))
	if leg_r:
		leg_r.rotation_degrees.x = gait * minf(24.0, speed * 7.0) / stride_bias
		leg_r.visible = not bool(host.get("leg_r_disabled"))
	if jaw and head and head.visible and quality >= 1:
		jaw.rotation_degrees.x = -13.0 + absf(sin(phase * 0.8)) * 9.0 * jaw_scale

func _quality() -> int:
	if budget and budget.has_method("get_animation_quality"): return int(budget.get_animation_quality())
	return 1 if OS.has_feature("mobile") else 2

func _quality_interval() -> float:
	if budget and budget.has_method("get_animation_update_interval"): return float(budget.get_animation_update_interval())
	return 1.0 / 30.0 if OS.has_feature("mobile") else 0.0
