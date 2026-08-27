extends RefCounted
class_name Ballistics

static func resistance_for(collider: Object) -> float:
	if collider == null: return 1.0
	if collider.has_meta("ballistic_resistance"): return float(collider.get_meta("ballistic_resistance"))
	var n := String(collider.name).to_lower()
	if "car" in n: return 0.32
	if "barricade" in n or "checkpointcover" in n: return 0.52
	if "building" in n or "concrete" in n or "sidewalk" in n: return 0.95
	if "rubble" in n: return 0.78
	if "alien" in n: return 0.68
	return 0.85

static func energy_resistance_for(collider: Object) -> float:
	if collider == null: return 1.0
	if collider.has_meta("energy_resistance"): return float(collider.get_meta("energy_resistance"))
	var n := String(collider.name).to_lower()
	if "alien" in n: return 0.92
	if "building" in n or "concrete" in n: return 0.78
	if "rubble" in n: return 0.62
	if "car" in n: return 0.38
	if "barricade" in n or "checkpointcover" in n: return 0.42
	return 0.58

static func thickness_for(collider: Object) -> float:
	if collider == null: return 0.6
	if collider.has_meta("ballistic_thickness"): return float(collider.get_meta("ballistic_thickness"))
	var n := String(collider.name).to_lower()
	if "car" in n: return 0.22
	if "barricade" in n or "checkpointcover" in n: return 0.35
	if "rubble" in n: return 0.55
	if "building" in n: return 1.4
	return 0.65

static func cover_height_for(collider: Object) -> float:
	if collider == null: return 1.8
	if collider.has_meta("cover_height"): return float(collider.get_meta("cover_height"))
	var n := String(collider.name).to_lower()
	if "barricade" in n or "checkpointcover" in n or "carbody" in n: return 1.1
	if "rubble" in n: return 0.8
	return 1.8

static func is_destructible_cover(collider: Object) -> bool:
	if collider == null: return false
	if collider.has_meta("destructible_cover"): return bool(collider.get_meta("destructible_cover"))
	var n := String(collider.name).to_lower()
	return "barricade" in n or "checkpointcover" in n

static func apply_surface_damage(collider: Object, raw_damage: float, energy: float, hit_point := Vector3.ZERO, hit_direction := Vector3.ZERO) -> bool:
	if not is_destructible_cover(collider): return false
	if collider.has_method("apply_ballistic_hit"):
		collider.apply_ballistic_hit(raw_damage, energy, hit_point, hit_direction)
		return false
	return _fallback_cover_damage(collider, raw_damage * clampf(0.35 + energy * 0.60, 0.2, 1.25), hit_direction)

static func apply_energy_surface_damage(collider: Object, raw_damage: float, energy: float, hit_point := Vector3.ZERO, hit_direction := Vector3.ZERO) -> bool:
	if not is_destructible_cover(collider): return false
	if collider.has_method("apply_energy_hit"):
		collider.apply_energy_hit(raw_damage, energy, hit_point, hit_direction)
		return false
	var thermal := clampf(1.30 - energy_resistance_for(collider) * 0.55, 0.55, 1.35)
	return _fallback_cover_damage(collider, raw_damage * clampf(0.58 + energy * 0.92, 0.3, 1.8) * thermal, hit_direction)

static func _fallback_cover_damage(collider: Object, structural_damage: float, _hit_direction: Vector3) -> bool:
	var maximum := float(collider.get_meta("cover_max_integrity", 140.0))
	var integrity := float(collider.get_meta("cover_integrity", maximum))
	integrity = maxf(integrity - structural_damage, 0.0)
	collider.set_meta("cover_integrity", integrity)
	collider.set_meta("cover_max_integrity", maximum)
	collider.set_meta("cover_height", cover_height_for(collider))
	collider.set_meta("destructible_cover", true)
	var ratio := integrity / maxf(maximum, 1.0)
	var stage := 0
	if ratio <= 0.28: stage = 3
	elif ratio <= 0.58: stage = 2
	elif ratio <= 0.82: stage = 1
	var previous := int(collider.get_meta("damage_stage", -1))
	if stage != previous:
		collider.set_meta("damage_stage", stage)
		_apply_fallback_visual_stage(collider, stage)
		var base_resistance := 0.52
		collider.set_meta("ballistic_resistance", maxf(base_resistance - float(stage) * 0.07, 0.18))
		collider.set_meta("energy_resistance", maxf(0.42 - float(stage) * 0.055, 0.12))
	if integrity <= 0.0 and collider is Node:
		(collider as Node).queue_free()
		return true
	return false

static func _apply_fallback_visual_stage(collider: Object, stage: int) -> void:
	if not (collider is Node): return
	var node := collider as Node
	for child in node.get_children():
		if child is MeshInstance3D:
			var mi := child as MeshInstance3D
			if mi.material_override is StandardMaterial3D:
				var mat := (mi.material_override as StandardMaterial3D).duplicate() as StandardMaterial3D
				var darken := 1.0 - float(stage) * 0.14
				mat.albedo_color = mat.albedo_color * Color(darken, darken * 0.94, darken * 0.90, 1.0)
				mat.roughness = minf(mat.roughness + float(stage) * 0.06, 1.0)
				mi.material_override = mat
	if node is Node3D:
		var n3 := node as Node3D
		if not n3.has_meta("base_cover_rotation_z"): n3.set_meta("base_cover_rotation_z", n3.rotation.z)
		n3.rotation.z = float(n3.get_meta("base_cover_rotation_z")) + deg_to_rad(float(stage) * 1.4)

static func energy_after_surface(energy: float, collider: Object) -> float:
	return maxf(energy - resistance_for(collider) * thickness_for(collider), 0.0)

static func xeno_energy_after_surface(energy: float, collider: Object) -> float:
	# Alien lance couples differently to matter: thin metal is poor cover, alien growth is excellent cover.
	return maxf(energy - energy_resistance_for(collider) * thickness_for(collider) * 0.82, 0.0)

static func damage_scale(energy: float, initial_energy: float) -> float:
	if initial_energy <= 0.0: return 0.0
	return clampf(energy / initial_energy, 0.0, 1.0)
