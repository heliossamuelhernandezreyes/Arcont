extends SceneTree

const CANDIDATES := {
	"human_scale": "res://assets/provisional/cc0_runtime/characters/human_scale_candidate/night-striker-reference.glb",
	"realistic_city_zombie": "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/InfectedCityMan.fbx",
	"mobile_zombie": "res://assets/provisional/cc0_runtime/zombies/mobile_reference/Zombie.fbx",
}

var failures: Array[String] = []

func _initialize() -> void:
	for label in CANDIDATES:
		_audit_scene(label, CANDIDATES[label])
	_audit_forest_folder()
	if failures.is_empty():
		print("RUNTIME_CANDIDATES_OK")
		quit(0)
	else:
		for failure in failures:
			push_error(failure)
		quit(1)

func _audit_scene(label: String, path: String) -> void:
	if not ResourceLoader.exists(path):
		failures.append("%s missing: %s" % [label, path])
		return
	var packed := load(path) as PackedScene
	if packed == null:
		failures.append("%s failed to load as PackedScene: %s" % [label, path])
		return
	var root := packed.instantiate()
	var stats := {"triangles": 0, "vertices": 0, "surfaces": 0, "meshes": 0, "skeletons": 0, "bones": 0, "animation_players": 0, "animations": 0}
	_collect_stats(root, stats)
	var bounds := _visual_bounds(root)
	var size := bounds.size
	print("RUNTIME_CANDIDATE|%s|triangles=%d|vertices=%d|surfaces=%d|meshes=%d|skeletons=%d|bones=%d|animation_players=%d|animations=%d|size=%.3fx%.3fx%.3f" % [label, stats.triangles, stats.vertices, stats.surfaces, stats.meshes, stats.skeletons, stats.bones, stats.animation_players, stats.animations, size.x, size.y, size.z])
	if stats.meshes <= 0 or stats.vertices <= 0:
		failures.append("%s has no usable mesh geometry" % label)
	if label != "mobile_zombie" and stats.skeletons <= 0:
		failures.append("%s has no Skeleton3D" % label)
	if size.y <= 0.01:
		failures.append("%s has invalid visual height %.4f" % [label, size.y])
	root.free()

func _collect_stats(node: Node, stats: Dictionary) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		if mi.mesh != null:
			stats.meshes += 1
			for surface_index in range(mi.mesh.get_surface_count()):
				stats.surfaces += 1
				var arrays := mi.mesh.surface_get_arrays(surface_index)
				if arrays.size() <= Mesh.ARRAY_VERTEX:
					continue
				var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
				stats.vertices += vertices.size()
				var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
				stats.triangles += indices.size() / 3 if not indices.is_empty() else vertices.size() / 3
	elif node is Skeleton3D:
		stats.skeletons += 1
		stats.bones += (node as Skeleton3D).get_bone_count()
	elif node is AnimationPlayer:
		stats.animation_players += 1
		var ap := node as AnimationPlayer
		for library_name in ap.get_animation_library_list():
			var library := ap.get_animation_library(library_name)
			stats.animations += library.get_animation_list().size()
	for child in node.get_children():
		_collect_stats(child, stats)

func _visual_bounds(root: Node) -> AABB:
	var initialized := false
	var result := AABB()
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(root, meshes)
	for mi in meshes:
		if mi.mesh == null:
			continue
		var box := mi.mesh.get_aabb()
		var transformed := _transform_aabb(box, mi.transform)
		if not initialized:
			result = transformed
			initialized = true
		else:
			result = result.merge(transformed)
	return result

func _collect_meshes(node: Node, result: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D:
		result.append(node as MeshInstance3D)
	for child in node.get_children():
		_collect_meshes(child, result)

func _transform_aabb(box: AABB, transform: Transform3D) -> AABB:
	var points := [
		box.position,
		box.position + Vector3(box.size.x, 0, 0),
		box.position + Vector3(0, box.size.y, 0),
		box.position + Vector3(0, 0, box.size.z),
		box.position + Vector3(box.size.x, box.size.y, 0),
		box.position + Vector3(box.size.x, 0, box.size.z),
		box.position + Vector3(0, box.size.y, box.size.z),
		box.end,
	]
	var first: Vector3 = transform * points[0]
	var min_v := first
	var max_v := first
	for point in points:
		var p: Vector3 = transform * point
		min_v = min_v.min(p)
		max_v = max_v.max(p)
	return AABB(min_v, max_v - min_v)

func _audit_forest_folder() -> void:
	var dir := DirAccess.open("res://assets/provisional/cc0_runtime/forest")
	if dir == null:
		failures.append("forest runtime folder missing")
		return
	var count := 0
	for file_name in dir.get_files():
		if file_name.get_extension().to_lower() in ["fbx", "glb", "gltf"]:
			var path := "res://assets/provisional/cc0_runtime/forest/%s" % file_name
			if ResourceLoader.exists(path) and load(path) is PackedScene:
				count += 1
	print("RUNTIME_FOREST|loadable_models=%d" % count)
	if count <= 0:
		failures.append("no loadable forest runtime models")
