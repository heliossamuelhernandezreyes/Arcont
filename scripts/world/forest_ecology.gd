@tool
class_name ForestEcology
extends Node3D

@export var terrain_path: NodePath = NodePath("../Terrain")
@export var seed: int = 842113
@export_range(6.0, 18.0, 0.5) var spacing: float = 9.0
@export_range(24.0, 96.0, 4.0) var chunk_size: float = 48.0
@export_range(0.0, 1.0, 0.01) var density: float = 0.72
@export_range(0.0, 1.0, 0.01) var route_exclusion: float = 0.16
@export_range(0.0, 1.0, 0.01) var clearing_exclusion: float = 0.18
@export_range(0.0, 1.0, 0.01) var water_exclusion: float = 0.66
@export_range(0.0, 1.0, 0.01) var steep_slope_limit: float = 0.78
@export_range(0.0, 1.0, 0.01) var understory_density: float = 0.58
@export_range(0.0, 1.0, 0.01) var rock_density: float = 0.32
@export_range(0.0, 1.0, 0.01) var deadwood_density: float = 0.13
@export_range(0.0, 1.0, 0.01) var riparian_density: float = 0.50
@export var regenerate: bool = false:
	set(value):
		regenerate = false
		if value and is_inside_tree():
			generate()

var tree_positions: Array[Vector3] = []
var tree_scales := PackedFloat32Array()
var tree_yaws := PackedFloat32Array()
var rock_positions: Array[Vector3] = []
var understory_positions: Array[Vector3] = []
var deadwood_positions: Array[Vector3] = []
var riparian_positions: Array[Vector3] = []
var chunk_tree_counts: Dictionary = {}
var rejected_route: int = 0
var rejected_clearing: int = 0
var rejected_water: int = 0
var rejected_slope: int = 0

var _cluster_noise := FastNoiseLite.new()
var _species_noise := FastNoiseLite.new()
var _micro_noise := FastNoiseLite.new()
var _rng := RandomNumberGenerator.new()

func _ready() -> void:
	generate()

func generate() -> void:
	_clear_generated()
	var terrain := get_node_or_null(terrain_path) as ForestTerrain
	if terrain == null:
		return
	if terrain.heights.is_empty():
		terrain.generate()
	_setup_noise()
	_scatter_trees(terrain)
	_scatter_understory(terrain)
	_scatter_rocks(terrain)
	_scatter_deadwood(terrain)
	_scatter_riparian(terrain)
	_build_chunked_forest()
	_build_chunked_understory()
	_build_chunked_rocks()
	_build_chunked_deadwood()
	_build_chunked_riparian()

func _setup_noise() -> void:
	_cluster_noise.seed = seed
	_cluster_noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	_cluster_noise.frequency = 0.0105
	_cluster_noise.fractal_type = FastNoiseLite.FRACTAL_FBM
	_cluster_noise.fractal_octaves = 3
	_cluster_noise.fractal_gain = 0.52
	_species_noise.seed = seed + 1907
	_species_noise.noise_type = FastNoiseLite.TYPE_SIMPLEX
	_species_noise.frequency = 0.018
	_micro_noise.seed = seed + 5119
	_micro_noise.noise_type = FastNoiseLite.TYPE_SIMPLEX
	_micro_noise.frequency = 0.035
	_rng.seed = seed

func _scatter_trees(terrain: ForestTerrain) -> void:
	tree_positions.clear()
	tree_scales.clear()
	tree_yaws.clear()
	chunk_tree_counts.clear()
	rejected_route = 0
	rejected_clearing = 0
	rejected_water = 0
	rejected_slope = 0
	var half: float = terrain.world_size * 0.5
	var cells: int = int(floor(terrain.world_size / spacing))
	for gz in range(cells):
		for gx in range(cells):
			var base_x: float = -half + (float(gx) + 0.5) * spacing
			var base_z: float = -half + (float(gz) + 0.5) * spacing
			var jitter: float = spacing * 0.38
			var wx: float = base_x + _rng.randf_range(-jitter, jitter)
			var wz: float = base_z + _rng.randf_range(-jitter, jitter)
			var cluster: float = _cluster_noise.get_noise_2d(wx, wz) * 0.5 + 0.5
			var local_density: float = density * smoothstep(0.20, 0.82, cluster)
			if _rng.randf() > local_density:
				continue
			var masks: Color = _sample_masks(terrain, wx, wz)
			if masks.a > route_exclusion:
				rejected_route += 1
				continue
			var clearing: float = _sample_field(terrain, terrain.clearing_mask, wx, wz)
			if clearing > clearing_exclusion:
				rejected_clearing += 1
				continue
			if masks.b > water_exclusion:
				rejected_water += 1
				continue
			if masks.r > steep_slope_limit:
				rejected_slope += 1
				continue
			var moisture_bonus: float = lerpf(0.86, 1.12, masks.g)
			if _rng.randf() > clampf(moisture_bonus, 0.0, 1.0):
				continue
			var y: float = terrain.sample_height(wx, wz)
			var scale_value: float = _rng.randf_range(0.82, 1.22)
			var species_signal: float = _species_noise.get_noise_2d(wx, wz)
			if species_signal > 0.28:
				scale_value *= 1.08
			elif species_signal < -0.34:
				scale_value *= 0.90
			tree_positions.append(Vector3(wx, y, wz))
			tree_scales.append(scale_value)
			tree_yaws.append(_rng.randf_range(-PI, PI))
			var chunk: Vector2i = _chunk_for(wx, wz)
			chunk_tree_counts[chunk] = int(chunk_tree_counts.get(chunk, 0)) + 1

func _scatter_understory(terrain: ForestTerrain) -> void:
	understory_positions.clear()
	_rng.seed = seed + 10001
	var sample_spacing: float = 6.0
	var half: float = terrain.world_size * 0.5
	var cells: int = int(floor(terrain.world_size / sample_spacing))
	for gz in range(cells):
		for gx in range(cells):
			if _rng.randf() > understory_density:
				continue
			var wx: float = -half + (float(gx) + _rng.randf_range(0.18, 0.82)) * sample_spacing
			var wz: float = -half + (float(gz) + _rng.randf_range(0.18, 0.82)) * sample_spacing
			var masks: Color = _sample_masks(terrain, wx, wz)
			var clearing: float = _sample_field(terrain, terrain.clearing_mask, wx, wz)
			var patch: float = _micro_noise.get_noise_2d(wx, wz) * 0.5 + 0.5
			if masks.a > 0.10 or clearing > 0.24 or masks.b > 0.74 or masks.r > 0.70 or patch < 0.30:
				continue
			understory_positions.append(Vector3(wx, terrain.sample_height(wx, wz), wz))

func _scatter_rocks(terrain: ForestTerrain) -> void:
	rock_positions.clear()
	_rng.seed = seed + 20003
	var sample_spacing: float = 11.0
	var half: float = terrain.world_size * 0.5
	var cells: int = int(floor(terrain.world_size / sample_spacing))
	for gz in range(cells):
		for gx in range(cells):
			if _rng.randf() > rock_density:
				continue
			var wx: float = -half + (float(gx) + _rng.randf()) * sample_spacing
			var wz: float = -half + (float(gz) + _rng.randf()) * sample_spacing
			var masks: Color = _sample_masks(terrain, wx, wz)
			var clearing: float = _sample_field(terrain, terrain.clearing_mask, wx, wz)
			var geology: float = _cluster_noise.get_noise_2d(wx + 490.0, wz - 320.0) * 0.5 + 0.5
			if masks.a > 0.12 or clearing > 0.34 or masks.b > 0.80:
				continue
			if masks.r < 0.26 and geology < 0.66:
				continue
			rock_positions.append(Vector3(wx, terrain.sample_height(wx, wz), wz))

func _scatter_deadwood(terrain: ForestTerrain) -> void:
	deadwood_positions.clear()
	_rng.seed = seed + 30011
	var sample_spacing: float = 17.0
	var half: float = terrain.world_size * 0.5
	var cells: int = int(floor(terrain.world_size / sample_spacing))
	for gz in range(cells):
		for gx in range(cells):
			if _rng.randf() > deadwood_density:
				continue
			var wx: float = -half + (float(gx) + _rng.randf()) * sample_spacing
			var wz: float = -half + (float(gz) + _rng.randf()) * sample_spacing
			var masks: Color = _sample_masks(terrain, wx, wz)
			if masks.a > 0.11 or masks.b > 0.76 or masks.r > 0.64:
				continue
			deadwood_positions.append(Vector3(wx, terrain.sample_height(wx, wz), wz))

func _scatter_riparian(terrain: ForestTerrain) -> void:
	riparian_positions.clear()
	_rng.seed = seed + 40009
	var sample_spacing: float = 5.5
	var half: float = terrain.world_size * 0.5
	var cells: int = int(floor(terrain.world_size / sample_spacing))
	for gz in range(cells):
		for gx in range(cells):
			if _rng.randf() > riparian_density:
				continue
			var wx: float = -half + (float(gx) + _rng.randf()) * sample_spacing
			var wz: float = -half + (float(gz) + _rng.randf()) * sample_spacing
			var masks: Color = _sample_masks(terrain, wx, wz)
			if masks.a > 0.12 or masks.r > 0.48:
				continue
			if masks.g < 0.56 or masks.b < 0.16 or masks.b > 0.72:
				continue
			riparian_positions.append(Vector3(wx, terrain.sample_height(wx, wz), wz))

func _build_chunked_forest() -> void:
	var by_chunk := _group_positions(tree_positions)
	var trunk_mesh := CylinderMesh.new()
	trunk_mesh.top_radius = 0.34
	trunk_mesh.bottom_radius = 0.48
	trunk_mesh.height = 7.2
	trunk_mesh.radial_segments = 7
	trunk_mesh.rings = 1
	trunk_mesh.material = _material(Color(0.19, 0.105, 0.055, 1.0), 0.96)
	var canopy_mesh := SphereMesh.new()
	canopy_mesh.radius = 3.0
	canopy_mesh.height = 6.0
	canopy_mesh.radial_segments = 8
	canopy_mesh.rings = 5
	canopy_mesh.material = _material(Color(0.075, 0.22, 0.065, 1.0), 0.94)
	var far_canopy := SphereMesh.new()
	far_canopy.radius = 2.8
	far_canopy.height = 5.6
	far_canopy.radial_segments = 5
	far_canopy.rings = 3
	far_canopy.material = _material(Color(0.065, 0.17, 0.055, 1.0), 1.0)
	for key: Vector2i in by_chunk.keys():
		var indices: Array = by_chunk[key]
		var root := _chunk_root("Trees", key)
		var trunks := _make_multimesh("Trunks", trunk_mesh, indices.size(), 0.0, 155.0)
		var crowns := _make_multimesh("Canopies", canopy_mesh, indices.size(), 0.0, 140.0)
		var far := _make_multimesh("FarCanopies", far_canopy, indices.size(), 118.0, 310.0)
		root.add_child(trunks)
		root.add_child(crowns)
		root.add_child(far)
		for local_i in range(indices.size()):
			var source_i: int = int(indices[local_i])
			var p: Vector3 = tree_positions[source_i]
			var scale_value: float = tree_scales[source_i]
			var yaw: float = tree_yaws[source_i]
			var basis := Basis(Vector3.UP, yaw).scaled(Vector3.ONE * scale_value)
			trunks.multimesh.set_instance_transform(local_i, Transform3D(basis, p + Vector3.UP * 3.6 * scale_value))
			var crown_scale := Vector3(scale_value * 0.94, scale_value * (0.94 + 0.08 * sin(float(source_i))), scale_value * 0.94)
			crowns.multimesh.set_instance_transform(local_i, Transform3D(Basis(Vector3.UP, yaw).scaled(crown_scale), p + Vector3.UP * 8.2 * scale_value))
			far.multimesh.set_instance_transform(local_i, Transform3D(Basis(Vector3.UP, yaw).scaled(Vector3.ONE * scale_value), p + Vector3.UP * 8.0 * scale_value))

func _build_chunked_understory() -> void:
	var mesh := SphereMesh.new()
	mesh.radius = 0.78
	mesh.height = 1.25
	mesh.radial_segments = 5
	mesh.rings = 3
	mesh.material = _material(Color(0.11, 0.27, 0.075, 1.0), 1.0)
	_build_simple_layer("Understory", understory_positions, mesh, 86.0, Vector3(1.0, 0.72, 1.0))

func _build_chunked_rocks() -> void:
	var mesh := SphereMesh.new()
	mesh.radius = 0.95
	mesh.height = 1.45
	mesh.radial_segments = 6
	mesh.rings = 4
	mesh.material = _material(Color(0.31, 0.32, 0.285, 1.0), 1.0)
	_build_simple_layer("Rocks", rock_positions, mesh, 125.0, Vector3(1.35, 0.58, 1.0))

func _build_chunked_deadwood() -> void:
	var mesh := CylinderMesh.new()
	mesh.top_radius = 0.18
	mesh.bottom_radius = 0.28
	mesh.height = 4.2
	mesh.radial_segments = 6
	mesh.rings = 1
	mesh.material = _material(Color(0.17, 0.105, 0.055, 1.0), 1.0)
	var by_chunk := _group_positions(deadwood_positions)
	_rng.seed = seed + 70001
	for key: Vector2i in by_chunk.keys():
		var indices: Array = by_chunk[key]
		var root := _chunk_root("Deadwood", key)
		var inst := _make_multimesh("Logs", mesh, indices.size(), 0.0, 95.0)
		root.add_child(inst)
		for local_i in range(indices.size()):
			var p: Vector3 = deadwood_positions[int(indices[local_i])]
			var yaw: float = _rng.randf_range(-PI, PI)
			var basis := Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, PI * 0.5)
			basis = basis.scaled(Vector3(_rng.randf_range(0.8, 1.3), _rng.randf_range(0.8, 1.2), _rng.randf_range(0.8, 1.2)))
			inst.multimesh.set_instance_transform(local_i, Transform3D(basis, p + Vector3.UP * 0.24))

func _build_chunked_riparian() -> void:
	var mesh := CylinderMesh.new()
	mesh.top_radius = 0.035
	mesh.bottom_radius = 0.065
	mesh.height = 1.55
	mesh.radial_segments = 4
	mesh.rings = 1
	mesh.material = _material(Color(0.16, 0.34, 0.10, 1.0), 1.0)
	_build_simple_layer("Riparian", riparian_positions, mesh, 75.0, Vector3(1.0, 1.0, 1.0), 0.78)

func _build_simple_layer(prefix: String, positions: Array[Vector3], mesh: Mesh, visibility_end: float, scale_bias: Vector3, y_offset: float = 0.0) -> void:
	var by_chunk := _group_positions(positions)
	_rng.seed = seed + prefix.hash()
	for key: Vector2i in by_chunk.keys():
		var indices: Array = by_chunk[key]
		var root := _chunk_root(prefix, key)
		var inst := _make_multimesh(prefix, mesh, indices.size(), 0.0, visibility_end)
		root.add_child(inst)
		for local_i in range(indices.size()):
			var p: Vector3 = positions[int(indices[local_i])]
			var yaw: float = _rng.randf_range(-PI, PI)
			var s: float = _rng.randf_range(0.72, 1.32)
			var basis := Basis(Vector3.UP, yaw).scaled(scale_bias * s)
			inst.multimesh.set_instance_transform(local_i, Transform3D(basis, p + Vector3.UP * y_offset * s))

func _make_multimesh(node_name: String, mesh: Mesh, count: int, visibility_begin: float, visibility_end: float) -> MultiMeshInstance3D:
	var node := MultiMeshInstance3D.new()
	node.name = node_name
	node.visibility_range_begin = visibility_begin
	node.visibility_range_end = visibility_end
	node.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = count
	node.multimesh = mm
	return node

func _material(color: Color, roughness: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = roughness
	return material

func _group_positions(positions: Array[Vector3]) -> Dictionary:
	var result: Dictionary = {}
	for i in range(positions.size()):
		var p: Vector3 = positions[i]
		var key: Vector2i = _chunk_for(p.x, p.z)
		if not result.has(key):
			result[key] = []
		var indices: Array = result[key]
		indices.append(i)
		result[key] = indices
	return result

func _chunk_root(prefix: String, key: Vector2i) -> Node3D:
	var root := Node3D.new()
	root.name = "%s_%d_%d" % [prefix, key.x, key.y]
	add_child(root)
	return root

func _chunk_for(wx: float, wz: float) -> Vector2i:
	return Vector2i(int(floor(wx / chunk_size)), int(floor(wz / chunk_size)))

func _sample_masks(terrain: ForestTerrain, wx: float, wz: float) -> Color:
	return Color(
		_sample_field(terrain, terrain.slopes, wx, wz),
		_sample_field(terrain, terrain.moisture, wx, wz),
		_sample_field(terrain, terrain.flow, wx, wz),
		_sample_field(terrain, terrain.route_mask, wx, wz)
	)

func _sample_field(terrain: ForestTerrain, field: PackedFloat32Array, wx: float, wz: float) -> float:
	if field.is_empty():
		return 0.0
	var fx: float = clampf((wx / terrain.world_size + 0.5) * terrain.resolution, 0.0, terrain.resolution)
	var fz: float = clampf((wz / terrain.world_size + 0.5) * terrain.resolution, 0.0, terrain.resolution)
	var x: int = clampi(int(round(fx)), 0, terrain.resolution)
	var z: int = clampi(int(round(fz)), 0, terrain.resolution)
	return field[z * (terrain.resolution + 1) + x]

func _clear_generated() -> void:
	for child: Node in get_children():
		child.queue_free()
