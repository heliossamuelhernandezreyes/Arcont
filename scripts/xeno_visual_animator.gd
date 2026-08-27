extends Node

var host: CharacterBody3D
var body: Node3D
var head: Node3D
var arm_l: Node3D
var arm_r: Node3D
var weapon: Node3D
var core: Node3D
var phase := 0.0

func _ready() -> void:
	host = get_parent() as CharacterBody3D
	body = host.get_node_or_null("Body") as Node3D
	head = host.get_node_or_null("Head") as Node3D
	arm_l = host.get_node_or_null("ArmL") as Node3D
	arm_r = host.get_node_or_null("ArmR") as Node3D
	weapon = host.get_node_or_null("Weapon") as Node3D
	core = host.get_node_or_null("Body/Core") as Node3D
	phase = randf_range(0.0, TAU)

func _process(delta: float) -> void:
	if host == null or not is_instance_valid(host): return
	phase += delta * 2.4
	var speed := Vector2(host.velocity.x, host.velocity.z).length()
	var stride := sin(phase * (1.0 + speed * 0.28))
	if body:
		body.position.y = 0.15 + sin(phase * 1.2) * 0.018
		body.rotation_degrees.z = stride * minf(3.0, speed * 0.65)
	if head:
		head.rotation_degrees.y = sin(phase * 0.37) * 7.0
		head.rotation_degrees.z = sin(phase * 0.53) * 2.5
	if arm_l: arm_l.rotation_degrees.x = 14.0 + stride * minf(16.0, 4.0 + speed * 3.0)
	if arm_r: arm_r.rotation_degrees.x = 14.0 - stride * minf(16.0, 4.0 + speed * 3.0)
	var charging := bool(host.get("charging"))
	if weapon:
		weapon.rotation_degrees.x = lerpf(weapon.rotation_degrees.x, -16.0 if charging else -8.0, minf(delta * 8.0, 1.0))
		weapon.rotation_degrees.z = lerpf(weapon.rotation_degrees.z, -3.0 if charging else -7.0, minf(delta * 8.0, 1.0))
	if core:
		var pulse := 1.0 + sin(phase * (3.4 if charging else 1.6)) * (0.12 if charging else 0.04)
		core.scale = Vector3.ONE * pulse
