extends Node
class_name NavigationGraph

var graph := AStar3D.new()
var point_positions: Array[Vector3] = []
var ready_for_queries := false

func _ready() -> void:
	_build_graph.call_deferred()

func _build_graph() -> void:
	graph.clear()
	point_positions = [
		Vector3(-4,0.2,-31),Vector3(4,0.2,-31),Vector3(-4,0.2,-23),Vector3(4,0.2,-23),
		Vector3(-5,0.2,-14),Vector3(5,0.2,-14),Vector3(-5,0.2,-5),Vector3(5,0.2,-5),
		Vector3(-5,0.2,5),Vector3(5,0.2,5),Vector3(-5,0.2,14),Vector3(5,0.2,14),
		Vector3(-4,0.2,23),Vector3(4,0.2,23),Vector3(-4,0.2,31),Vector3(4,0.2,31),
		Vector3(-14,0.2,-18),Vector3(-14,0.2,-4),Vector3(-14,0.2,8),Vector3(-14,0.2,18),
		Vector3(14,0.2,-20),Vector3(14,0.2,-5),Vector3(14,0.2,7),Vector3(14,0.2,18),
		Vector3(-24,0.2,2),Vector3(-24,0.2,9),Vector3(24,0.2,2),Vector3(24,0.2,9)
	]
	for i in point_positions.size():
		graph.add_point(i, point_positions[i])
	for i in point_positions.size():
		for j in range(i + 1, point_positions.size()):
			var a := point_positions[i]
			var b := point_positions[j]
			var distance := a.distance_to(b)
			if distance <= 12.5 and _segment_walkable(a, b):
				graph.connect_points(i, j, true)
	ready_for_queries = true

func _segment_walkable(a: Vector3, b: Vector3) -> bool:
	var world := get_world_3d()
	if world == null:
		return true
	var start := a + Vector3.UP * 0.8
	var finish := b + Vector3.UP * 0.8
	var query := PhysicsRayQueryParameters3D.create(start, finish)
	query.collide_with_areas = false
	var hit := world.direct_space_state.intersect_ray(query)
	return hit.is_empty()

func get_path(from: Vector3, to: Vector3) -> PackedVector3Array:
	if not ready_for_queries or graph.get_point_count() == 0:
		return PackedVector3Array([to])
	var from_id := graph.get_closest_point(from)
	var to_id := graph.get_closest_point(to)
	var route := graph.get_point_path(from_id, to_id)
	var output := PackedVector3Array()
	for p in route:
		output.append(p)
	output.append(to)
	return output

func next_waypoint(from: Vector3, to: Vector3, reach_distance := 1.2) -> Vector3:
	var route := get_path(from, to)
	if route.is_empty():
		return to
	for point in route:
		if from.distance_to(point) > reach_distance:
			return point
	return to
