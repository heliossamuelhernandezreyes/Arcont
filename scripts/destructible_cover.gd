extends StaticBody3D

signal integrity_changed(current: float, maximum: float)
signal destroyed

@export var max_integrity := 140.0
@export var cover_height := 1.1
@export var ballistic_resistance := 0.52
@export var ballistic_thickness := 0.35

var integrity := 140.0
var destroyed_state := false

func _ready() -> void:
	integrity = max_integrity
	set_meta("ballistic_resistance", ballistic_resistance)
	set_meta("ballistic_thickness", ballistic_thickness)
	set_meta("cover_height", cover_height)
	set_meta("destructible_cover", true)
	integrity_changed.emit(integrity, max_integrity)

func apply_ballistic_hit(raw_damage: float, energy: float, hit_point := Vector3.ZERO, hit_direction := Vector3.ZERO) -> void:
	if destroyed_state:
		return
	var structural_damage := raw_damage * clampf(0.45 + energy * 0.75, 0.25, 1.5)
	integrity = maxf(integrity - structural_damage, 0.0)
	integrity_changed.emit(integrity, max_integrity)
	if integrity <= 0.0:
		_break_apart(hit_point, hit_direction)

func _break_apart(_hit_point: Vector3, hit_direction: Vector3) -> void:
	if destroyed_state:
		return
	destroyed_state = true
	destroyed.emit()
	var root := get_tree().current_scene
	if root != null:
		for i in 3:
			var chunk := RigidBody3D.new()
			var mesh_instance := MeshInstance3D.new()
			var mesh := BoxMesh.new()
			mesh.size = Vector3(0.45, 0.28, 0.22)
			mesh_instance.mesh = mesh
			chunk.add_child(mesh_instance)
			var shape_node := CollisionShape3D.new()
			var shape := BoxShape3D.new()
			shape.size = mesh.size
			shape_node.shape = shape
			chunk.add_child(shape_node)
			root.add_child(chunk)
			chunk.global_position = global_position + Vector3(randf_range(-0.5,0.5),0.45+float(i)*0.16,randf_range(-0.35,0.35))
			chunk.linear_velocity = hit_direction.normalized()*randf_range(1.5,3.0) + Vector3(randf_range(-1.0,1.0),randf_range(1.0,2.5),randf_range(-1.0,1.0))
			root.get_tree().create_timer(4.0).timeout.connect(chunk.queue_free)
	queue_free()
