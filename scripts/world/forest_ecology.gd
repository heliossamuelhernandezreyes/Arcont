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
@export var regenerate: bool = false:
	set(value):
		regenerate = false
		if value and is_inside_tree():
			generate()

var tree_positions: Array[Vector3] = []
var tree_scales := PackedFloat32Array()
var tree_yaws := PackedFloat32Array()
var chunk_tree_counts: Dictionary = {}
var rejected_route: int = 0
var rejected_clearing: int = 0
var rejected_water: int = 0
var rejected_slope: int = 0

var _cluster_noise := FastNoiseLite.new()
var _species_noise := FastNoiseLite.new()
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
	_scatter_candidates(terrain)
	_build_chunked_multimeshes(terrain)

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
	_rng.seed = seed

func _scatter_candidates(terrain: ForestTerrain) -> void:
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
			# Moist lowlands can support denser trees, but preserve a narrow riparian gap immediately at the stream.
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

func _build_chunked_multimeshes(terrain: ForestTerrain) -> void:
	var transforms_by_chunk: Dictionary = {}
	for i in range(tree_positions.size()):
		var p: Vector3 = tree_positions[i]
		var chunk: Vector2i = _chunk_for(p.x, p.z)
		if not transforms_by_chunk.has(chunk):
			transforms_by_chunk[chunk] = []
		var transforms: Array = transforms_by_chunk[chunk]
		transforms.append(_tree_transform(p, tree_scales[i], tree_yaws[i]))
		transforms_by_chunk[chunk] = transforms

	var trunk_mesh := CylinderMesh.new()
	trunk_mesh.top_radius = 0.34
	trunk_mesh.bottom_radius = 0.48
	trunk_mesh.height = 7.2
	trunk_mesh.radial_segments = 7
	trunk_mesh.rings = 1
	var trunk_material := StandardMaterial3D.new()
	trunk_material.albedo_color = Color(0.19, 0.105, 0.055, 1.0)
	trunk_material.roughness = 0.96
	trunk_mesh.material = trunk_material

	var canopy_mesh := SphereMesh.new()
	canopy_mesh.radius = 3.0
	canopy_mesh.height = 6.0
	canopy_mesh.radial_segments = 8
	canopy_mesh.rings = 5
	var canopy_material := StandardMaterial3D.new()
	canopy_material.albedo_color = Color(0.075, 0.22, 0.065, 1.0)
	canopy_material.roughness = 0.94
	canopy_mesh.material = canopy_material

	for key: Vector2i in transforms_by_chunk.keys():
		var transforms: Array = transforms_by_chunk[key]
		var chunk_root := Node3D.new()
		chunk_root.name = "Chunk_%d_%d" % [key.x, key.y]
		chunk_root.set_meta("tree_count", transforms.size())
		add_child(chunk_root)

		var trunks := MultiMeshInstance3D.new()
		trunks.name = "Trunks"
		trunks.visibility_range_end = 170.0
		trunks.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		var trunk_mm := MultiMesh.new()
		trunk_mm.transform_format = MultiMesh.TRANSFORM_3D
		trunk_mm.mesh = trunk_mesh
		trunk_mm.instance_count = transforms.size()
		trunks.multimesh = trunk_mm
		chunk_root.add_child(trunks)

		var canopies := MultiMeshInstance3D.new()
		canopies.name = "Canopies"
		canopies.visibility_range_end = 150.0
		canopies.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		var canopy_mm := MultiMesh.new()
		canopy_mm.transform_format = MultiMesh.TRANSFORM_3D
		canopy_mm.mesh = canopy_mesh
		canopy_mm.instance_count = transforms.size()
		canopies.multimesh = canopy_mm
		chunk_root.add_child(canopies)

		for i in range(transforms.size()):
			var base_transform: Transform3D = transforms[i]
			var scale_value: float = base_transform.basis.get_scale().x
			var yaw: float = base_transform.basis.get_euler().y
			var base: Vector3 = base_transform.origin
			var trunk_basis := Basis(Vector3.UP, yaw).scaled(Vector3(scale_value, scale_value, scale_value))
			var trunk_transform := Transform3D(trunk_basis, base + Vector3.UP * 3.6 * scale_value)
			trunk_mm.set_instance_transform(i, trunk_transform)
			var canopy_scale := Vector3(scale_value * 0.94, scale_value * _rng.randf_range(0.88, 1.12), scale_value * 0.94)
			var canopy_basis := Basis(Vector3.UP, yaw).scaled(canopy_scale)
			var canopy_transform := Transform3D(canopy_basis, base + Vector3.UP * 8.2 * scale_value)
			canopy_mm.set_instance_transform(i, canopy_transform)

func _tree_transform(position: Vector3, scale_value: float, yaw: float) -> Transform3D:
	return Transform3D(Basis(Vector3.UP, yaw).scaled(Vector3.ONE * scale_value), position)

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
