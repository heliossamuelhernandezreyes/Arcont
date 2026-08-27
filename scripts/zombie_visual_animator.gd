extends Node

var host: CharacterBody3D
var body: Node3D
var head: Node3D
var arm_l: Node3D
var arm_r: Node3D
var leg_l: Node3D
var leg_r: Node3D
var jaw: Node3D
var phase := 0.0

func _ready() -> void:
	host = get_parent() as CharacterBody3D
	body = host.get_node_or_null("Body") as Node3D
	head = host.get_node_or_null("Head") as Node3D
	arm_l = host.get_node_or_null("ArmL") as Node3D
	arm_r = host.get_node_or_null("ArmR") as Node3D
	leg_l = host.get_node_or_null("Body/LegL") as Node3D
	leg_r = host.get_node_or_null("Body/LegR") as Node3D
	jaw = host.get_node_or_null("Head/Jaw") as Node3D
	phase = randf_range(0.0, TAU)

func _process(delta: float) -> void:
	if host == null or not is_instance_valid(host) or not host.visible: return
	var crawling := bool(host.get("crawling"))
	var knockdown := float(host.get("knockdown_timer"))
	if crawling or knockdown > 0.0: return
	var speed := Vector2(host.velocity.x, host.velocity.z).length()
	phase += delta * lerpf(1.4, 7.4, clampf(speed / 3.0, 0.0, 1.0))
	var gait := sin(phase)
	var bob := absf(sin(phase * 0.5))
	if body:
		body.rotation_degrees.z = -4.0 + gait * minf(speed * 1.6, 4.5)
		body.position.y = 0.98 + bob * minf(speed * 0.012, 0.025)
	if head and not bool(host.get("head_missing")):
		head.rotation_degrees = Vector3(8.0 + sin(phase * 0.55) * 2.5, -7.0 + sin(phase * 0.32) * 4.0, -5.0 + gait * 2.2)
	if arm_l and not bool(host.get("arm_l_missing")):
		arm_l.rotation_degrees.x = 72.0 + gait * minf(18.0, 5.0 + speed * 4.0)
	if arm_r and not bool(host.get("arm_r_missing")):
		arm_r.rotation_degrees.x = 72.0 - gait * minf(18.0, 5.0 + speed * 4.0)
	if leg_l:
		leg_l.rotation_degrees.x = -gait * minf(24.0, speed * 7.0)
		leg_l.visible = not bool(host.get("leg_l_disabled"))
	if leg_r:
		leg_r.rotation_degrees.x = gait * minf(24.0, speed * 7.0)
		leg_r.visible = not bool(host.get("leg_r_disabled"))
	if jaw and head and head.visible:
		jaw.rotation_degrees.x = -13.0 + absf(sin(phase * 0.8)) * 9.0
