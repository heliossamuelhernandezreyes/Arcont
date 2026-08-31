@tool
class_name ForestHydrology
extends MeshInstance3D

@export var terrain_path: NodePath = NodePath("../Terrain")
@export_range(2.0, 18.0, 0.25) var base_width: float = 7.0
@export_range(0.0, 2.0, 0.05) var water_offset: float = 0.22
@export_range(0.0, 1.0, 0.01) var flow_threshold: float = 0.48
@export_range(16, 256, 1) var longitudinal_samples: int = 96
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
	var half: float = terrain.world_size * 0.5
	for s in range(longitudinal_samples + 1):
		var u: float = float(s) / float(longitudinal_samples)
		var wx: float = lerpf(-half, half, u)
		var wz: float = terrain.channel_z_at_world_x(wx)
		var wy: float = terrain.channel_floor_height(wx) + water_offset + 0.08
		centerline.append(Vector3(wx, wy, wz))
		var flow_value: float = _sample_flow(terrain, wx, wz)
		var width_factor: float = clampf((flow_value - flow_threshold) / maxf(0.001, 1.0 - flow_threshold), 0.0, 1.0)
		widths.append(base_width * lerpf(0.78, 1.34, width_factor))

func _sample_flow(terrain: ForestTerrain, wx: float, wz: float) -> float:
	var fx: int = clampi(int(round((wx / terrain.world_size + 0.5) * terrain.resolution)), 0, terrain.resolution)
	var fz: int = clampi(int(round((wz / terrain.world_size + 0.5) * terrain.resolution)), 0, terrain.resolution)
	var side: int = terrain.resolution + 1
	return terrain.flow[fz * side + fx]

func _build_water_mesh(terrain: ForestTerrain) -> void:
	mesh = _build_ribbon(terrain, 1.0, 0.0, true)

func _build_bank_mesh(terrain: ForestTerrain) -> void:
	var bank := get_node_or_null("Banks") as MeshInstance3D
	if bank == null:
		bank = MeshInstance3D.new()
		bank.name = "Banks"
		add_child(bank)
	bank.mesh = _build_ribbon(terrain, 1.9, -0.04, false)
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
		var side_vec := Vector3(-tangent.z, 0.0, tangent.x)
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
