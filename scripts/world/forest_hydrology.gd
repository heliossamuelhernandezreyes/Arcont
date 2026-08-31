@tool
class_name ForestHydrology
extends MeshInstance3D

@export var terrain_path: NodePath = NodePath("../Terrain")
@export_range(2.0, 18.0, 0.25) var base_width: float = 7.0
@export_range(0.0, 2.0, 0.05) var water_offset: float = 0.22
@export_range(0.0, 1.0, 0.01) var flow_threshold: float = 0.48
@export_range(16, 256, 1) var longitudinal_samples: int = 96
@export_range(0, 12, 1) var smooth_passes: int = 5
@export_range(0.0, 0.35, 0.01) var max_surface_rise_per_sample: float = 0.12
@export var regenerate: bool = false:
	set(value):
		regenerate = false
		if value and is_inside_tree():
			generate()

var centerline := PackedVector3Array()
var widths := PackedFloat32Array()

func _ready() -> void:
	generate()

func generate() -> void:
	var terrain := get_node_or_null(terrain_path) as ForestTerrain
	if terrain == null:
		return
	if terrain.heights.is_empty():
		terrain.generate()
	_build_centerline(terrain)
	_build_water_mesh(terrain)
	_build_bank_mesh(terrain)

func _build_centerline(terrain: ForestTerrain) -> void:
	centerline.clear()
	widths.clear()
	var side: int = terrain.resolution + 1
	var half: float = terrain.world_size * 0.5
	var raw_z := PackedFloat32Array()
	var raw_flow := PackedFloat32Array()
	raw_z.resize(longitudinal_samples + 1)
	raw_flow.resize(longitudinal_samples + 1)

	for s in range(longitudinal_samples + 1):
		var u: float = float(s) / float(longitudinal_samples)
		var x_index: int = clampi(int(round(u * terrain.resolution)), 0, terrain.resolution)
		var best_z: int = 0
		var best_score: float = -1.0
		for z in range(side):
			var i: int = z * side + x_index
			var score: float = terrain.flow[i] * 0.82 + terrain.moisture[i] * 0.18
			if score > best_score:
				best_score = score
				best_z = z
		raw_z[s] = -half + (float(best_z) / float(terrain.resolution)) * terrain.world_size
		raw_flow[s] = terrain.flow[best_z * side + x_index]

	for _pass in range(smooth_passes):
		var filtered := raw_z.duplicate()
		for s in range(2, longitudinal_samples - 1):
			filtered[s] = (raw_z[s - 2] + raw_z[s - 1] * 2.0 + raw_z[s] * 4.0 + raw_z[s + 1] * 2.0 + raw_z[s + 2]) / 10.0
		raw_z = filtered

	var points := PackedVector3Array()
	var point_flows := PackedFloat32Array()
	points.resize(longitudinal_samples + 1)
	point_flows.resize(longitudinal_samples + 1)
	for s in range(longitudinal_samples + 1):
		var u: float = float(s) / float(longitudinal_samples)
		var wx: float = lerpf(-half, half, u)
		var wz: float = raw_z[s]
		points[s] = Vector3(wx, terrain.sample_height(wx, wz) + water_offset, wz)
		point_flows[s] = raw_flow[s]

	var start_mean: float = 0.0
	var end_mean: float = 0.0
	var sample_window: int = mini(5, points.size())
	for i in range(sample_window):
		start_mean += points[i].y
		end_mean += points[points.size() - 1 - i].y
	start_mean /= float(sample_window)
	end_mean /= float(sample_window)
	if start_mean < end_mean:
		points.reverse()
		point_flows.reverse()

	for i in range(points.size()):
		var p: Vector3 = points[i]
		if i > 0:
			p.y = minf(p.y, centerline[i - 1].y + max_surface_rise_per_sample)
		centerline.append(p)
		var width_factor: float = clampf((point_flows[i] - flow_threshold) / maxf(0.001, 1.0 - flow_threshold), 0.0, 1.0)
		widths.append(base_width * lerpf(0.72, 1.38, width_factor))

func _build_water_mesh(terrain: ForestTerrain) -> void:
	mesh = _build_ribbon(terrain, 1.0, 0.0, true)

func _build_bank_mesh(terrain: ForestTerrain) -> void:
	var bank := get_node_or_null("Banks") as MeshInstance3D
	if bank == null:
		bank = MeshInstance3D.new()
		bank.name = "Banks"
		add_child(bank)
	bank.mesh = _build_ribbon(terrain, 1.9, -0.055, false)
	var bank_material := StandardMaterial3D.new()
	bank_material.albedo_color = Color(0.13, 0.095, 0.055, 1.0)
	bank_material.roughness = 1.0
	bank.material_override = bank_material

func _build_ribbon(terrain: ForestTerrain, width_scale: float, height_bias: float, use_centerline_height: bool) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	if centerline.size() < 2:
		return st.commit()
	for i in range(centerline.size()):
		var prev: Vector3 = centerline[maxi(0, i - 1)]
		var next: Vector3 = centerline[mini(centerline.size() - 1, i + 1)]
		var tangent: Vector3 = next - prev
		tangent.y = 0.0
		if tangent.length_squared() < 0.0001:
			tangent = Vector3.RIGHT
		tangent = tangent.normalized()
		var side_vec: Vector3 = Vector3(-tangent.z, 0.0, tangent.x)
		var half_width: float = widths[i] * 0.5 * width_scale
		var left: Vector3 = centerline[i] - side_vec * half_width
		var right: Vector3 = centerline[i] + side_vec * half_width
		if use_centerline_height:
			left.y = centerline[i].y + height_bias
			right.y = centerline[i].y + height_bias
		else:
			left.y = terrain.sample_height(left.x, left.z) + water_offset + height_bias
			right.y = terrain.sample_height(right.x, right.z) + water_offset + height_bias
		st.set_uv(Vector2(0.0, float(i) / 8.0))
		st.add_vertex(left)
		st.set_uv(Vector2(1.0, float(i) / 8.0))
		st.add_vertex(right)
	for i in range(centerline.size() - 1):
		var a: int = i * 2
		var b: int = a + 1
		var c: int = a + 2
		var d: int = a + 3
		st.add_index(a)
		st.add_index(b)
		st.add_index(c)
		st.add_index(b)
		st.add_index(d)
		st.add_index(c)
	st.generate_normals()
	return st.commit()
