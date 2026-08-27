extends StaticBody3D

signal integrity_changed(current: float, maximum: float)
signal damage_stage_changed(stage: int)
signal destroyed

@export var max_integrity := 140.0
@export var cover_height := 1.1
@export var ballistic_resistance := 0.52
@export var ballistic_thickness := 0.35
@export var energy_resistance := 0.42

var integrity := 140.0
var destroyed_state := false
var damage_stage := 0
var base_rotation := Vector3.ZERO

func _ready() -> void:
	integrity = max_integrity
	base_rotation = rotation
	set_meta("ballistic_resistance", ballistic_resistance)
	set_meta("ballistic_thickness", ballistic_thickness)
	set_meta("energy_resistance", energy_resistance)
	set_meta("cover_height", cover_height)
	set_meta("destructible_cover", true)
	set_meta("cover_integrity", integrity)
	set_meta("cover_max_integrity", max_integrity)
	integrity_changed.emit(integrity, max_integrity)
	_update_visual_stage(true)

func apply_ballistic_hit(raw_damage: float, energy: float, hit_point := Vector3.ZERO, hit_direction := Vector3.ZERO) -> void:
	if destroyed_state: return
	var structural_damage := raw_damage * clampf(0.42 + energy * 0.72, 0.22, 1.45)
	_apply_structural_damage(structural_damage, hit_point, hit_direction)

func apply_energy_hit(raw_damage: float, energy: float, hit_point := Vector3.ZERO, hit_direction := Vector3.ZERO) -> void:
	if destroyed_state: return
	# Xeno energy heats and weakens thin military cover more efficiently than pellets.
	var thermal_factor := clampf(1.25 - energy_resistance * 0.55, 0.55, 1.35)
	var structural_damage := raw_damage * clampf(0.58 + energy * 0.92, 0.3, 1.8) * thermal_factor
	_apply_structural_damage(structural_damage, hit_point, hit_direction)

func _apply_structural_damage(amount: float, hit_point: Vector3, hit_direction: Vector3) -> void:
	integrity = maxf(integrity - amount, 0.0)
	set_meta("cover_integrity", integrity)
	integrity_changed.emit(integrity, max_integrity)
	_update_visual_stage(false)
	if integrity <= 0.0: _break_apart(hit_point, hit_direction)

func _update_visual_stage(force_update: bool) -> void:
	var ratio := integrity / maxf(max_integrity, 1.0)
	var next_stage := 0
	if ratio <= 0.28: next_stage = 3
	elif ratio <= 0.58: next_stage = 2
	elif ratio <= 0.82: next_stage = 1
	if next_stage == damage_stage and not force_update: return
	damage_stage = next_stage
	damage_stage_changed.emit(damage_stage)
	set_meta("damage_stage", damage_stage)
	# Deformation is deliberately subtle so cover collision remains predictable.
	rotation = base_rotation + Vector3(0.0, 0.0, deg_to_rad(float(damage_stage) * 1.4))
	for child in get_children():
		if child is MeshInstance3D:
			var mi := child as MeshInstance3D
			var material := mi.material_override
			if material is StandardMaterial3D:
				var local_mat := (material as StandardMaterial3D).duplicate() as StandardMaterial3D
				var darken := 1.0 - float(damage_stage) * 0.14
				local_mat.albedo_color = local_mat.albedo_color * Color(darken, darken * 0.94, darken * 0.90, 1.0)
				local_mat.roughness = minf(local_mat.roughness + float(damage_stage) * 0.06, 1.0)
				mi.material_override = local_mat
	# Damaged cover becomes progressively easier to penetrate.
	set_meta("ballistic_resistance", maxf(ballistic_resistance - float(damage_stage) * 0.07, 0.18))
	set_meta("energy_resistance", maxf(energy_resistance - float(damage_stage) * 0.055, 0.12))

func _break_apart(_hit_point: Vector3, hit_direction: Vector3) -> void:
	if destroyed_state: return
	destroyed_state = true
	destroyed.emit()
	var root := get_tree().current_scene
	if root != null:
		var chunk_count := 2 if OS.has_feature("mobile") else 4
		for i in chunk_count:
			var chunk := RigidBody3D.new()
			var mesh_instance := MeshInstance3D.new()
			var mesh := BoxMesh.new()
			mesh.size = Vector3(0.42, 0.24, 0.20)
			mesh_instance.mesh = mesh
			chunk.add_child(mesh_instance)
			var shape_node := CollisionShape3D.new()
			var shape := BoxShape3D.new()
			shape.size = mesh.size
			shape_node.shape = shape
			chunk.add_child(shape_node)
			root.add_child(chunk)
			chunk.global_position = global_position + Vector3(randf_range(-0.5,0.5),0.35+float(i)*0.12,randf_range(-0.3,0.3))
			chunk.linear_velocity = hit_direction.normalized()*randf_range(1.2,2.8) + Vector3(randf_range(-0.9,0.9),randf_range(0.8,2.2),randf_range(-0.9,0.9))
			root.get_tree().create_timer(3.0).timeout.connect(chunk.queue_free)
	queue_free()
