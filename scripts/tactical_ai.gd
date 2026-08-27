extends RefCounted
class_name TacticalAI

static func has_line_of_sight(actor: CollisionObject3D, target: Node3D, from_height := 1.2, target_height := 0.7) -> bool:
	if actor == null or target == null or actor.get_world_3d() == null:
		return false
	var start := actor.global_position + Vector3.UP * from_height
	var finish := target.global_position + Vector3.UP * target_height
	var query := PhysicsRayQueryParameters3D.create(start, finish)
	query.exclude = [actor.get_rid()]
	query.collide_with_areas = false
	var result := actor.get_world_3d().direct_space_state.intersect_ray(query)
	var visible: bool = result.is_empty() or result.get("collider") == target
	if visible:
		_report_contact_throttled(actor, target.global_position)
	return visible

static func _report_contact_throttled(actor: CollisionObject3D, position: Vector3) -> void:
	var now := Time.get_ticks_msec()
	var last := int(actor.get_meta("last_radio_report_ms", -100000))
	if now - last < 1200:
		return
	actor.set_meta("last_radio_report_ms", now)
	var scene := actor.get_tree().current_scene
	if scene == null:
		return
	var awareness := scene.get_node_or_null("AwarenessDirector")
	if awareness and awareness.has_method("report_contact"):
		awareness.report_contact(position, "armed")

static func point_has_cover(actor: CollisionObject3D, target: Node3D, point: Vector3) -> bool:
	if actor == null or target == null or actor.get_world_3d() == null:
		return false
	var start := target.global_position + Vector3.UP * 0.75
	var finish := point + Vector3.UP * 0.75
	var query := PhysicsRayQueryParameters3D.create(start, finish)
	query.exclude = [actor.get_rid()]
	query.collide_with_areas = false
	var result := actor.get_world_3d().direct_space_state.intersect_ray(query)
	if result.is_empty():
		return false
	var hit_pos: Vector3 = result.get("position", finish)
	return hit_pos.distance_to(finish) > 0.65

static func best_cover(actor: CollisionObject3D, target: Node3D, preferred_distance: float, max_search := 28.0) -> Vector3:
	return best_cover_near(actor, target, actor.global_position, preferred_distance, max_search)

static func best_cover_near(actor: CollisionObject3D, target: Node3D, anchor: Vector3, preferred_distance: float, max_search := 28.0) -> Vector3:
	var candidates: Array[Vector3] = []
	for node in actor.get_tree().get_nodes_in_group("tactical_cover"):
		if node is Node3D:
			candidates.append((node as Node3D).global_position)
	for point in _vertical_slice_cover_points():
		candidates.append(point)
	var best := Vector3.ZERO
	var found := false
	var best_score := INF
	for point in candidates:
		var actor_distance := actor.global_position.distance_to(point)
		if actor_distance > max_search:
			continue
		if not point_has_cover(actor, target, point):
			continue
		var target_distance := target.global_position.distance_to(point)
		var score := actor_distance * 0.32 + point.distance_to(anchor) * 0.62 + absf(target_distance - preferred_distance) * 0.55
		for ally in actor.get_tree().get_nodes_in_group("tactical_enemy"):
			if ally == actor or not ally is Node3D:
				continue
			var separation := (ally as Node3D).global_position.distance_to(point)
			if separation < 2.4:
				score += (2.4 - separation) * 5.0
		if score < best_score:
			best_score = score
			best = point
			found = true
	return best if found else Vector3.INF

static func flank_point(actor: Node3D, target: Node3D, side: float, radius := 12.0) -> Vector3:
	var to_actor := actor.global_position - target.global_position
	to_actor.y = 0.0
	if to_actor.length_squared() < 0.01:
		to_actor = Vector3.FORWARD
	var radial := to_actor.normalized()
	var lateral := Vector3.UP.cross(radial).normalized() * signf(side)
	return target.global_position + (radial * 0.35 + lateral * 0.94).normalized() * radius

static func squad_role(actor: Node) -> String:
	var tactical := actor.get_tree().get_nodes_in_group("tactical_enemy")
	var index := tactical.find(actor)
	if index < 0:
		index = actor.get_instance_id() % 3
	match index % 3:
		0: return "suppress"
		1: return "flank_left"
		_: return "flank_right"

static func _vertical_slice_cover_points() -> Array[Vector3]:
	return [
		Vector3(-2.9,0.2,-21.2), Vector3(3.0,0.2,-20.5), Vector3(-3.2,0.2,26.2),
		Vector3(-12.4,0.2,5.5), Vector3(12.2,0.2,3.2), Vector3(-2.4,0.2,-8.4),
		Vector3(2.8,0.2,15.4), Vector3(-14.3,0.2,4.0), Vector3(-2.0,0.2,7.4),
		Vector3(2.0,0.2,6.2), Vector3(-9.3,0.2,13.7), Vector3(10.0,0.2,-15.3)
	]
