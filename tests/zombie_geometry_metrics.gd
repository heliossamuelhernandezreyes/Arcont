extends SceneTree

const ZOMBIE_ASSETS := [
	"res://assets/provisional/cc0_runtime/zombies/Zombie_Male.fbx",
	"res://assets/provisional/cc0_runtime/zombies/Zombie_Female.fbx",
]

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var failed := false
	for path in ZOMBIE_ASSETS:
		var packed := load(path) as PackedScene
		if packed == null:
			push_error("GEOMETRY METRICS: unable to load %s" % path)
			failed = true
			continue
		var instance := packed.instantiate()
		root.add_child(instance)
		await process_frame
		var metrics := _measure_node(instance)
		print("ARCONT_GEOMETRY asset=%s mesh_instances=%d surfaces=%d vertices=%d indices=%d triangles=%d" % [
			path,
			metrics.mesh_instances,
			metrics.surfaces,
			metrics.vertices,
			metrics.indices,
			metrics.triangles,
		])
		if metrics.mesh_instances <= 0 or metrics.triangles <= 0:
			push_error("GEOMETRY METRICS: no drawable triangle geometry found in %s" % path)
			failed = true
		instance.queue_free()
		await process_frame
	quit(1 if failed else 0)

func _measure_node(node: Node) -> Dictionary:
	var result := {
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
		var mesh_instance := node as MeshInstance3D
		var mesh := mesh_instance.mesh
		if mesh != null:
			result.mesh_instances += 1
			for surface in mesh.get_surface_count():
				result.surfaces += 1
				var arrays := mesh.surface_get_arrays(surface)
				if arrays.size() <= Mesh.ARRAY_INDEX:
					continue
				var vertices = arrays[Mesh.ARRAY_VERTEX]
				var indices = arrays[Mesh.ARRAY_INDEX]
				var vertex_count := vertices.size() if vertices != null else 0
				var index_count := indices.size() if indices != null else 0
				result.vertices += vertex_count
				result.indices += index_count
				var primitive := mesh.surface_get_primitive_type(surface)
				var element_count := index_count if index_count > 0 else vertex_count
				match primitive:
					Mesh.PRIMITIVE_TRIANGLES:
						result.triangles += element_count / 3
					Mesh.PRIMITIVE_TRIANGLE_STRIP:
						result.triangles += max(element_count - 2, 0)
	for child in node.get_children():
		_measure_recursive(child, result)
