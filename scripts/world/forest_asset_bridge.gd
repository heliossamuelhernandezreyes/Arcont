@tool
class_name ForestAssetBridge
extends Node3D

@export var ecology_path: NodePath = NodePath("../Ecology")
@export var chunk_size: float = 48.0
@export var rock_scene_path: String = "res://assets/cc0/polyhaven/forest/rock_moss_set_01/rock_moss_set_01_1k.gltf"
@export var stump_scene_path: String = "res://assets/cc0/polyhaven/forest/tree_stump_01/tree_stump_01_1k.gltf"
@export var pine_lod0_path: String = "res://assets/runtime/forest/pine_tree_01/pine_tree_01_lod0.glb"
@export var pine_lod1_path: String = "res://assets/runtime/forest/pine_tree_01/pine_tree_01_lod1.glb"
@export var pine_lod2_path: String = "res://assets/runtime/forest/pine_tree_01/pine_tree_01_lod2.glb"
@export var pine_lod3_path: String = "res://assets/runtime/forest/pine_tree_01/pine_tree_01_lod3.glb"
@export var pine_hlod_path: String = "res://assets/runtime/forest/pine_tree_01/pine_tree_01_hlod.glb"

const TREE_LOD0_END := 3.0
const TREE_LOD1_END := 10.0
const TREE_LOD2_END := 25.0
const TREE_LOD3_END := 50.0
const TREE_HLOD_END := 310.0
const EXPECTED_PINE_VARIANTS := 3

func _ready() -> void:
	call_deferred("rebuild")

func rebuild() -> void:
	_clear_generated()
	var ecology := get_node_or_null(ecology_path) as ForestEcology
	if ecology == null:
		return
	if ecology.tree_positions.is_empty():
		ecology.generate()
	await get_tree().process_frame
	_hide_provisional(ecology, "Trees_")
	if _mobile_pine_lods_available():
		_build_mobile_pine_forest(ecology)
	else:
		_build_conifer_forest(ecology)
	var rock_mesh: Mesh = _load_first_mesh(rock_scene_path)
	var stump_mesh: Mesh = _load_first_mesh(stump_scene_path)
	if rock_mesh != null:
		_hide_provisional(ecology, "Rocks_")
		_build_asset_layer("RockCC0", ecology.rock_positions, rock_mesh, 130.0, Vector3.ONE * 0.72, 9101)
	if stump_mesh != null:
		_hide_provisional(ecology, "Deadwood_")
		_build_asset_layer("StumpCC0", ecology.deadwood_positions, stump_mesh, 92.0, Vector3.ONE * 0.82, 12011)

func _mobile_pine_lods_available() -> bool:
	return ResourceLoader.exists(pine_lod0_path) and ResourceLoader.exists(pine_lod1_path) and ResourceLoader.exists(pine_lod2_path) and ResourceLoader.exists(pine_lod3_path) and ResourceLoader.exists(pine_hlod_path)

func _build_mobile_pine_forest(ecology: ForestEcology) -> void:
	var lod0 := _load_meshes(pine_lod0_path)
	var lod1 := _load_meshes(pine_lod1_path)
	var lod2 := _load_meshes(pine_lod2_path)
	var lod3 := _load_meshes(pine_lod3_path)
	var hlod := _load_meshes(pine_hlod_path)
	var variant_count: int = mini(lod0.size(), mini(lod1.size(), mini(lod2.size(), mini(lod3.size(), hlod.size()))))
	if variant_count <= 0:
		_build_conifer_forest(ecology)
		return
	var groups := _group_indices(ecology.tree_positions)
	for key: Vector2i in groups.keys():
		var indices: Array = groups[key]
		var root := Node3D.new()
		root.name = "MobilePines_%d_%d" % [key.x, key.y]
		add_child(root)
		var variant_buckets: Array[Array] = []
		for variant_i in range(variant_count):
			variant_buckets.append([])
		for source_variant: Variant in indices:
			var source_i: int = int(source_variant)
			var variant_i: int = _variant_for_tree(source_i, variant_count)
			variant_buckets[variant_i].append(source_i)
		for variant_i in range(variant_count):
			var bucket: Array = variant_buckets[variant_i]
			if bucket.is_empty():
				continue
			var suffix := "V%d" % variant_i
			var near := _make_mm("PineLOD0_30k_%s" % suffix, lod0[variant_i], bucket.size(), 0.0, TREE_LOD0_END)
			var medium := _make_mm("PineLOD1_15k_%s" % suffix, lod1[variant_i], bucket.size(), TREE_LOD0_END, TREE_LOD1_END)
			var far := _make_mm("PineLOD2_6k_%s" % suffix, lod2[variant_i], bucket.size(), TREE_LOD1_END, TREE_LOD2_END)
			var very_far := _make_mm("PineLOD3_2k_%s" % suffix, lod3[variant_i], bucket.size(), TREE_LOD2_END, TREE_LOD3_END)
			var horizon := _make_mm("PineHLOD_96_%s" % suffix, hlod[variant_i], bucket.size(), TREE_LOD3_END, TREE_HLOD_END)
			root.add_child(near)
			root.add_child(medium)
			root.add_child(far)
			root.add_child(very_far)
			root.add_child(horizon)
			for local_i in range(bucket.size()):
				var source_i: int = int(bucket[local_i])
				var p: Vector3 = ecology.tree_positions[source_i]
				var s: float = ecology.tree_scales[source_i]
				var yaw: float = ecology.tree_yaws[source_i]
				var transform := Transform3D(Basis(Vector3.UP, yaw).scaled(Vector3.ONE * s), p)
				near.multimesh.set_instance_transform(local_i, transform)
				medium.multimesh.set_instance_transform(local_i, transform)
				far.multimesh.set_instance_transform(local_i, transform)
				very_far.multimesh.set_instance_transform(local_i, transform)
				horizon.multimesh.set_instance_transform(local_i, transform)

func _variant_for_tree(source_i: int, variant_count: int) -> int:
	if variant_count <= 1:
		return 0
	return posmod(source_i * 1103515245 + 12345, variant_count)

func _build_conifer_forest(ecology: ForestEcology) -> void:
	var trunk := CylinderMesh.new()
	trunk.top_radius = 0.22; trunk.bottom_radius = 0.42; trunk.height = 8.8; trunk.radial_segments = 7; trunk.rings = 1
	trunk.material = _material(Color(0.155, 0.085, 0.038, 1.0), 0.96)
	var lower := CylinderMesh.new()
	lower.top_radius = 0.18; lower.bottom_radius = 3.25; lower.height = 5.0; lower.radial_segments = 9; lower.rings = 1
	lower.material = _material(Color(0.055, 0.18, 0.055, 1.0), 0.98)
	var middle := CylinderMesh.new()
	middle.top_radius = 0.12; middle.bottom_radius = 2.65; middle.height = 4.4; middle.radial_segments = 9; middle.rings = 1
	middle.material = _material(Color(0.06, 0.205, 0.062, 1.0), 0.98)
	var upper := CylinderMesh.new()
	upper.top_radius = 0.05; upper.bottom_radius = 1.95; upper.height = 3.8; upper.radial_segments = 8; upper.rings = 1
	upper.material = _material(Color(0.07, 0.23, 0.07, 1.0), 0.98)
	var far := CylinderMesh.new()
	far.top_radius = 0.05; far.bottom_radius = 3.05; far.height = 9.6; far.radial_segments = 6; far.rings = 1
	far.material = _material(Color(0.045, 0.145, 0.045, 1.0), 1.0)
	var groups := _group_indices(ecology.tree_positions)
	for key: Vector2i in groups.keys():
		var indices: Array = groups[key]
		var root := Node3D.new()
		root.name = "Conifers_%d_%d" % [key.x, key.y]
		add_child(root)
		var trunks := _make_mm("Trunks", trunk, indices.size(), 0.0, 145.0)
		var low := _make_mm("LowerCrown", lower, indices.size(), 0.0, 128.0)
		var mid := _make_mm("MiddleCrown", middle, indices.size(), 0.0, 128.0)
		var top := _make_mm("UpperCrown", upper, indices.size(), 0.0, 128.0)
		var distant := _make_mm("FarCrown", far, indices.size(), 112.0, 310.0)
		root.add_child(trunks); root.add_child(low); root.add_child(mid); root.add_child(top); root.add_child(distant)
		for local_i in range(indices.size()):
			var source_i: int = int(indices[local_i])
			var p: Vector3 = ecology.tree_positions[source_i]
			var s: float = ecology.tree_scales[source_i]
			var yaw: float = ecology.tree_yaws[source_i]
			var b := Basis(Vector3.UP, yaw).scaled(Vector3.ONE * s)
			trunks.multimesh.set_instance_transform(local_i, Transform3D(b, p + Vector3.UP * 4.4 * s))
			low.multimesh.set_instance_transform(local_i, Transform3D(b, p + Vector3.UP * 7.2 * s))
			mid.multimesh.set_instance_transform(local_i, Transform3D(b, p + Vector3.UP * 9.4 * s))
			top.multimesh.set_instance_transform(local_i, Transform3D(b, p + Vector3.UP * 11.3 * s))
			distant.multimesh.set_instance_transform(local_i, Transform3D(b, p + Vector3.UP * 8.1 * s))

func _load_meshes(path: String) -> Array[Mesh]:
	var meshes: Array[Mesh] = []
	if not ResourceLoader.exists(path):
		return meshes
	var packed := load(path) as PackedScene
	if packed == null:
		return meshes
	var instance := packed.instantiate()
	_collect_meshes(instance, meshes)
	instance.free()
	return meshes

func _collect_meshes(node: Node, meshes: Array[Mesh]) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		if mi.mesh != null:
			meshes.append(mi.mesh)
	for child: Node in node.get_children():
		_collect_meshes(child, meshes)

func _load_first_mesh(path: String) -> Mesh:
	var meshes := _load_meshes(path)
	return meshes[0] if not meshes.is_empty() else null

func _hide_provisional(ecology: ForestEcology, prefix: String) -> void:
	for child: Node in ecology.get_children():
		if child.name.begins_with(prefix) and child is Node3D:
			(child as Node3D).visible = false

func _build_asset_layer(prefix: String, positions: Array[Vector3], mesh: Mesh, visibility_end: float, base_scale: Vector3, salt: int) -> void:
	var groups := _group_indices(positions)
	var rng := RandomNumberGenerator.new(); rng.seed = 842113 + salt
	for key: Vector2i in groups.keys():
		var indices: Array = groups[key]
		var node := _make_mm(prefix, mesh, indices.size(), 0.0, visibility_end)
		node.name = "%s_%d_%d" % [prefix, key.x, key.y]
		add_child(node)
		for i in range(indices.size()):
			var p: Vector3 = positions[int(indices[i])]
			var yaw: float = rng.randf_range(-PI, PI)
			var s: float = rng.randf_range(0.72, 1.18)
			var basis := Basis(Vector3.UP, yaw).scaled(base_scale * s)
			node.multimesh.set_instance_transform(i, Transform3D(basis, p))

func _group_indices(positions: Array[Vector3]) -> Dictionary:
	var groups: Dictionary = {}
	for i in range(positions.size()):
		var p: Vector3 = positions[i]
		var key := Vector2i(int(floor(p.x / chunk_size)), int(floor(p.z / chunk_size)))
		if not groups.has(key): groups[key] = []
		var bucket: Array = groups[key]; bucket.append(i); groups[key] = bucket
	return groups

func _make_mm(node_name: String, mesh: Mesh, count: int, begin: float, end: float) -> MultiMeshInstance3D:
	var node := MultiMeshInstance3D.new(); node.name = node_name
	node.visibility_range_begin = begin; node.visibility_range_end = end
	node.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
	var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = mesh; mm.instance_count = count
	node.multimesh = mm
	return node

func _material(color: Color, roughness: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new(); material.albedo_color = color; material.roughness = roughness
	return material

func _clear_generated() -> void:
	for child: Node in get_children(): child.queue_free()
