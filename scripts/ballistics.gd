extends RefCounted
class_name Ballistics

static func resistance_for(collider: Object) -> float:
	if collider == null:
		return 1.0
	if collider.has_meta("ballistic_resistance"):
		return float(collider.get_meta("ballistic_resistance"))
	var name_lower := String(collider.name).to_lower()
	if "car" in name_lower:
		return 0.32
	if "barricade" in name_lower or "checkpointcover" in name_lower:
		return 0.52
	if "building" in name_lower or "concrete" in name_lower or "sidewalk" in name_lower:
		return 0.95
	if "rubble" in name_lower:
		return 0.78
	if "alien" in name_lower:
		return 0.68
	return 0.85

static func thickness_for(collider: Object) -> float:
	if collider == null:
		return 0.6
	if collider.has_meta("ballistic_thickness"):
		return float(collider.get_meta("ballistic_thickness"))
	var name_lower := String(collider.name).to_lower()
	if "car" in name_lower:
		return 0.22
	if "barricade" in name_lower or "checkpointcover" in name_lower:
		return 0.35
	if "rubble" in name_lower:
		return 0.55
	if "building" in name_lower:
		return 1.4
	return 0.65

static func cover_height_for(collider: Object) -> float:
	if collider == null:
		return 1.8
	if collider.has_meta("cover_height"):
		return float(collider.get_meta("cover_height"))
	var name_lower := String(collider.name).to_lower()
	if "barricade" in name_lower or "checkpointcover" in name_lower or "carbody" in name_lower:
		return 1.1
	if "rubble" in name_lower:
		return 0.8
	return 1.8

static func is_destructible_cover(collider: Object) -> bool:
	if collider == null:
		return false
	if collider.has_meta("destructible_cover"):
		return bool(collider.get_meta("destructible_cover"))
	var name_lower := String(collider.name).to_lower()
	return "barricade" in name_lower or "checkpointcover" in name_lower

static func apply_surface_damage(collider: Object, raw_damage: float, energy: float) -> bool:
	if not is_destructible_cover(collider):
		return false
	var maximum := 140.0
	if collider.has_meta("cover_max_integrity"):
		maximum = float(collider.get_meta("cover_max_integrity"))
	var integrity := maximum
	if collider.has_meta("cover_integrity"):
		integrity = float(collider.get_meta("cover_integrity"))
	integrity = maxf(integrity - raw_damage * clampf(0.35 + energy * 0.60, 0.2, 1.25), 0.0)
	collider.set_meta("cover_integrity", integrity)
	collider.set_meta("cover_max_integrity", maximum)
	collider.set_meta("cover_height", cover_height_for(collider))
	collider.set_meta("destructible_cover", true)
	if integrity <= 0.0 and collider is Node:
		(collider as Node).queue_free()
		return true
	return false

static func energy_after_surface(energy: float, collider: Object) -> float:
	return maxf(energy - resistance_for(collider) * thickness_for(collider), 0.0)

static func damage_scale(energy: float, initial_energy: float) -> float:
	if initial_energy <= 0.0:
		return 0.0
	return clampf(energy / initial_energy, 0.0, 1.0)
