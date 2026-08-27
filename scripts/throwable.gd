extends RigidBody3D
class_name TacticalThrowable

var throwable_type := "GRENADE"
var owner_body: Node3D
var fuse_seconds := 2.4
var age := 0.0
var triggered := false

func configure(kind: String, owner: Node3D) -> void:
	throwable_type = kind.to_upper()
	owner_body = owner
	match throwable_type:
		"DECOY": fuse_seconds = 0.65
		"EMP": fuse_seconds = 1.6
		_: fuse_seconds = 2.4

func _ready() -> void:
	add_to_group("throwables")
	continuous_cd = true
	contact_monitor = true
	max_contacts_reported = 4
	var mesh := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.12
	sphere.height = 0.24
	mesh.mesh = sphere
	var material := StandardMaterial3D.new()
	match throwable_type:
		"DECOY": material.albedo_color = Color(1.0,0.72,0.10)
		"EMP": material.albedo_color = Color(0.20,0.72,1.0)
		_: material.albedo_color = Color(0.24,0.28,0.22)
	mesh.material_override = material
	add_child(mesh)
	var collision := CollisionShape3D.new()
	var shape := SphereShape3D.new()
	shape.radius = 0.13
	collision.shape = shape
	add_child(collision)

func _physics_process(delta: float) -> void:
	if triggered:return
	age += delta
	if age >= fuse_seconds:_trigger()

func _trigger() -> void:
	if triggered:return
	triggered = true
	match throwable_type:
		"DECOY": _activate_decoy()
		"EMP": _detonate_emp()
		_: _detonate_grenade()
	queue_free()

func _activate_decoy() -> void:
	var awareness := _awareness()
	if awareness and awareness.has_method("report_sound"):
		awareness.report_sound(global_position,22.0,"decoy")
	if awareness and awareness.has_method("sustain_lure"):
		awareness.sustain_lure(global_position,22.0,7.5,"decoy")

func _detonate_grenade() -> void:
	var awareness := _awareness()
	if awareness and awareness.has_method("report_sound"):awareness.report_sound(global_position,30.0,"explosion")
	_apply_radial_damage(7.0,82.0,9.0)
	_apply_cover_blast(7.5,68.0)

func _detonate_emp() -> void:
	var awareness := _awareness()
	if awareness and awareness.has_method("report_sound"):awareness.report_sound(global_position,14.0,"emp")
	for node in get_tree().get_nodes_in_group("xeno_enemy"):
		if node is Node3D and (node as Node3D).global_position.distance_to(global_position)<=9.0 and node.has_method("apply_emp"):
			node.apply_emp(5.0)
	for node in get_tree().get_nodes_in_group("friendly_companion"):
		if node is Node3D and (node as Node3D).global_position.distance_to(global_position)<=6.0 and node.has_method("apply_emp"):
			node.apply_emp(2.5)

func _apply_radial_damage(radius: float, max_damage: float, force: float) -> void:
	for node in get_tree().get_nodes_in_group("enemies_active"):
		if not node is Node3D:continue
		var body := node as Node3D
		var distance := body.global_position.distance_to(global_position)
		if distance>radius:continue
		var scale := 1.0-distance/radius
		var direction := (body.global_position-global_position).normalized()
		if node.has_method("apply_hit"):node.apply_hit(body.global_position,direction,max_damage*scale,"explosive",force*scale)
	var player := get_tree().get_first_node_in_group("player") as Node3D
	if player and player != owner_body:
		var distance := player.global_position.distance_to(global_position)
		if distance<=radius and player.has_method("apply_damage"):
			var scale := 1.0-distance/radius
			player.apply_damage(max_damage*0.7*scale,(player.global_position-global_position).normalized(),"torso",1.0)

func _apply_cover_blast(radius: float, damage: float) -> void:
	for node in get_tree().get_nodes_in_group("destructible_cover"):
		if not node is Node3D:continue
		var body := node as Node3D
		var distance := body.global_position.distance_to(global_position)
		if distance>radius:continue
		var scale := 1.0-distance/radius
		if node.has_method("apply_ballistic_hit"):
			node.apply_ballistic_hit(damage*scale,1.25,body.global_position,(body.global_position-global_position).normalized())

func _awareness() -> Node:
	var scene := get_tree().current_scene
	return scene.get_node_or_null("AwarenessDirector") if scene else null
