extends SceneTree

const ZOMBIE_ASSETS := [
	"res://assets/provisional/cc0_runtime/zombies/Zombie_Male.fbx",
	"res://assets/provisional/cc0_runtime/zombies/Zombie_Female.fbx",
]

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var failed: bool = false
	for path_variant in ZOMBIE_ASSETS:
		var path: String = String(path_variant)
		var packed: PackedScene = load(path) as PackedScene
		if packed == null:
			push_error("GEOMETRY METRICS: unable to load %s" % path)
			failed = true
			continue
		var instance: Node = packed.instantiate()
		root.add_child(instance)
		await process_frame
		var metrics: Dictionary = _measure_node(instance)
		print("ARCONT_GEOMETRY asset=%s mesh_instances=%d surfaces=%d vertices=%d indices=%d triangles=%d" % [
			path,
			int(metrics["mesh_instances"]),
			int(metrics["surfaces"]),
			int(metrics["vertices"]),
			int(metrics["indices"]),
			int(metrics["triangles"]),
		])
		if int(metrics["mesh_instances"]) <= 0 or int(metrics["triangles"]) <= 0:
			push_error("GEOMETRY METRICS: no drawable triangle geometry found in %s" % path)
			failed = true
		instance.queue_free()
		await process_frame
	quit(1 if failed else 0)

func _measure_node(node: Node) -> Dictionary:
	var result: Dictionary = {
		"mesh_instances": 0,
		"surfaces": 0,
		"vertices": 0,
		"indices": 0,
		"triangles": 0,
	}
	_measure_recursive(node, result)
	return result

func _measure_recursive(node: Node, result: Dictionary) -> void:
	if node is MeshInstance3D:
		var mesh_instance: MeshInstance3D = node as MeshInstance3D
		var mesh: Mesh = mesh_instance.mesh
		if mesh != null:
			result["mesh_instances"] = int(result["mesh_instances"]) + 1
			for surface: int in range(mesh.get_surface_count()):
				result["surfaces"] = int(result["surfaces"]) + 1
				var arrays: Array = mesh.surface_get_arrays(surface)
				if arrays.size() <= Mesh.ARRAY_INDEX:
					continue
				var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
				var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
				var vertex_count: int = vertices.size()
				var index_count: int = indices.size()
				result["vertices"] = int(result["vertices"]) + vertex_count
				result["indices"] = int(result["indices"]) + index_count
				var primitive: int = int(mesh.surface_get_primitive_type(surface))
				var element_count: int = index_count if index_count > 0 else vertex_count
				match primitive:
					Mesh.PRIMITIVE_TRIANGLES:
						result["triangles"] = int(result["triangles"]) + (element_count / 3)
					Mesh.PRIMITIVE_TRIANGLE_STRIP:
						result["triangles"] = int(result["triangles"]) + maxi(element_count - 2, 0)
	for child: Node in node.get_children():
		_measure_recursive(child, result)
