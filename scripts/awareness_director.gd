extends Node
class_name AwarenessDirector

@export var default_memory_seconds := 7.0
@export var radio_delay_min := 0.35
@export var radio_delay_max := 0.85
@export var intel_lifetime := 6.0
@export var infected_lure_seconds := 3.6

var last_sound_position := Vector3.ZERO
var last_sound_radius := 0.0
var last_sound_time_ms := -100000
var last_sound_category := ""
var shared_contact_position := Vector3.ZERO
var shared_contact_time_ms := -100000
var shared_contact_faction := ""
var pending_reports: Array[Dictionary] = []
var sound_lure: Node3D
var lure_expire_ms := -1

func _process(_delta: float) -> void:
	var now := Time.get_ticks_msec()
	for i in range(pending_reports.size() - 1, -1, -1):
		var report := pending_reports[i]
		if now >= int(report.get("deliver_ms", now + 1)):
			shared_contact_position = report.get("position", Vector3.ZERO)
			shared_contact_time_ms = now
			shared_contact_faction = String(report.get("faction", "armed"))
			pending_reports.remove_at(i)
	if sound_lure != null and is_instance_valid(sound_lure) and lure_expire_ms > 0 and now >= lure_expire_ms:
		sound_lure.queue_free()
		sound_lure = null
		lure_expire_ms = -1

func report_sound(position: Vector3, radius: float, category := "generic") -> void:
	last_sound_position = position
	last_sound_radius = maxf(radius, 0.0)
	last_sound_time_ms = Time.get_ticks_msec()
	last_sound_category = category
	if category in ["shotgun", "gunshot", "explosion", "decoy", "robot_fire"] and radius >= 5.0:
		_lure_infected(position, radius)

func _lure_infected(position: Vector3, radius: float) -> void:
	if sound_lure == null or not is_instance_valid(sound_lure):
		sound_lure = Node3D.new()
		sound_lure.name = "SoundLure"
		get_tree().current_scene.add_child(sound_lure)
	sound_lure.global_position = position
	lure_expire_ms = Time.get_ticks_msec() + int(infected_lure_seconds * 1000.0)
	for node in get_tree().get_nodes_in_group("enemies_active"):
		if not node is Node3D or node.is_in_group("tactical_enemy"):
			continue
		if (node as Node3D).global_position.distance_to(position) <= radius:
			node.set("target", sound_lure)

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

func report_contact(position: Vector3, faction := "armed") -> void:
	pending_reports.append({
		"position": position,
		"faction": faction,
		"deliver_ms": Time.get_ticks_msec() + int(randf_range(radio_delay_min, radio_delay_max) * 1000.0)
	})

func shared_intel_for(faction := "armed", max_age := -1.0) -> Dictionary:
	var allowed_age := intel_lifetime if max_age < 0.0 else max_age
	var age := float(Time.get_ticks_msec() - shared_contact_time_ms) / 1000.0
	if age < 0.0 or age > allowed_age:
		return {}
	if shared_contact_faction != faction and shared_contact_faction != "all":
		return {}
	return {"position": shared_contact_position, "age": age, "faction": shared_contact_faction}
