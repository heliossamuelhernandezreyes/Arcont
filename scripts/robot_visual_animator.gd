extends Node

var host: CharacterBody3D
var body: Node3D
var wheel_l: Node3D
var wheel_r: Node3D
var turret: Node3D
var optic: Node3D
var phase := 0.0

func _ready() -> void:
	host = get_parent() as CharacterBody3D
	body = host.get_node_or_null("Body") as Node3D
	wheel_l = host.get_node_or_null("WheelL") as Node3D
	wheel_r = host.get_node_or_null("WheelR") as Node3D
	turret = host.get_node_or_null("Turret") as Node3D
	optic = host.get_node_or_null("Turret/Optic") as Node3D

func _process(delta: float) -> void:
	if host == null or not is_instance_valid(host): return
	var speed := Vector2(host.velocity.x, host.velocity.z).length()
	phase += delta * (2.0 + speed * 2.6)
	if wheel_l: wheel_l.rotate_x(speed * delta * 4.2)
	if wheel_r: wheel_r.rotate_x(speed * delta * 4.2)
	if body:
		body.position.y = 0.66 + sin(phase) * minf(0.012, speed * 0.0025)
		body.rotation_degrees.z = sin(phase * 0.5) * minf(1.5, speed * 0.22)
	if turret and speed < 0.2:
		turret.rotation_degrees.z = sin(phase * 0.28) * 1.4
	if optic:
		var pulse := 1.0 + sin(phase * 1.7) * 0.04
		optic.scale = Vector3.ONE * pulse
