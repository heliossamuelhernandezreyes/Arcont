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
	if "barricade" in name_lower or "checkpoint" in name_lower:
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
	if "barricade" in name_lower:
		return 0.35
	if "rubble" in name_lower:
		return 0.55
	if "building" in name_lower:
		return 1.4
	return 0.65

static func energy_after_surface(energy: float, collider: Object) -> float:
	return maxf(energy - resistance_for(collider) * thickness_for(collider), 0.0)

static func damage_scale(energy: float, initial_energy: float) -> float:
	if initial_energy <= 0.0:
		return 0.0
	return clampf(energy / initial_energy, 0.0, 1.0)
