@tool
class_name ForestAssetBridge
extends Node3D

@export var ecology_path: NodePath = NodePath("../Ecology")
@export var chunk_size: float = 48.0
@export var rock_scene_path: String = "res://assets/cc0/polyhaven/forest/rock_moss_set_01/rock_moss_set_01_1k.gltf"
@export var stump_scene_path: String = "res://assets/cc0/polyhaven/forest/tree_stump_01/tree_stump_01_1k.gltf"

func _ready() -> void:
	call_deferred("rebuild")

func rebuild() -> void:
	_clear_generated()
	var ecology := get_node_or_null(ecology_path) as ForestEcology
	if ecology == null:
		return
	if ecology.rock_positions.is_empty() and ecology.deadwood_positions.is_empty():
		ecology.generate()
	await get_tree().process_frame
	var rock_mesh: Mesh = _load_first_mesh(rock_scene_path)
	var stump_mesh: Mesh = _load_first_mesh(stump_scene_path)
	if rock_mesh != null:
		_hide_provisional(ecology, "Rocks_")
		_build_layer("RockCC0", ecology.rock_positions, rock_mesh, 130.0, Vector3.ONE * 0.72, 9101)
	if stump_mesh != null:
		_hide_provisional(ecology, "Deadwood_")
		_build_layer("StumpCC0", ecology.deadwood_positions, stump_mesh, 92.0, Vector3.ONE * 0.82, 12011)

func _load_first_mesh(path: String) -> Mesh:
	if not ResourceLoader.exists(path):
		return null
	var packed := load(path) as PackedScene
	if packed == null:
		return null
	var instance := packed.instantiate()
	var mesh := _find_mesh(instance)
	instance.free()
	return mesh

func _find_mesh(node: Node) -> Mesh:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		if mi.mesh != null:
			return mi.mesh
	for child: Node in node.get_children():
		var found := _find_mesh(child)
		if found != null:
			return found
	return null

func _hide_provisional(ecology: ForestEcology, prefix: String) -> void:
	for child: Node in ecology.get_children():
		if child.name.begins_with(prefix) and child is Node3D:
			(child as Node3D).visible = false

func _build_layer(prefix: String, positions: Array[Vector3], mesh: Mesh, visibility_end: float, base_scale: Vector3, salt: int) -> void:
	var groups: Dictionary = {}
	for p: Vector3 in positions:
		var key := Vector2i(int(floor(p.x / chunk_size)), int(floor(p.z / chunk_size)))
		if not groups.has(key):
			groups[key] = []
		var bucket: Array = groups[key]
		bucket.append(p)
		groups[key] = bucket
	var rng := RandomNumberGenerator.new()
	rng.seed = 842113 + salt
	for key: Vector2i in groups.keys():
		var bucket: Array = groups[key]
		var node := MultiMeshInstance3D.new()
		node.name = "%s_%d_%d" % [prefix, key.x, key.y]
		node.visibility_range_end = visibility_end
		node.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		mm.instance_count = bucket.size()
		node.multimesh = mm
		add_child(node)
		for i in range(bucket.size()):
			var p: Vector3 = bucket[i]
			var yaw: float = rng.randf_range(-PI, PI)
			var s: float = rng.randf_range(0.72, 1.18)
			var basis := Basis(Vector3.UP, yaw).scaled(base_scale * s)
			mm.set_instance_transform(i, Transform3D(basis, p))

func _clear_generated() -> void:
	for child: Node in get_children():
		child.queue_free()
