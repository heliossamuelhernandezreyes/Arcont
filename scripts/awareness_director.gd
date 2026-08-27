extends Node
class_name AwarenessDirector

@export var default_memory_seconds := 7.0
var last_sound_position := Vector3.ZERO
var last_sound_radius := 0.0
var last_sound_time_ms := -100000
var last_sound_category := ""

func report_sound(position: Vector3, radius: float, category := "generic") -> void:
	last_sound_position = position
	last_sound_radius = maxf(radius, 0.0)
	last_sound_time_ms = Time.get_ticks_msec()
	last_sound_category = category

func recent_sound_for(listener_position: Vector3, max_age := 3.5) -> Dictionary:
	var age := float(Time.get_ticks_msec() - last_sound_time_ms) / 1000.0
	if age > max_age or age < 0.0:
		return {}
	var distance := listener_position.distance_to(last_sound_position)
	if distance > last_sound_radius:
		return {}
	return {
		"position": last_sound_position,
		"age": age,
		"strength": clampf(1.0 - distance / maxf(last_sound_radius, 0.01), 0.0, 1.0),
		"category": last_sound_category
	}
