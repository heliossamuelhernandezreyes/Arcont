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

func _build_centerline(terrain: ForestTerrain) -> void:
	centerline.clear()
	widths.clear()
	var side: int = terrain.resolution + 1
	var half: float = terrain.world_size * 0.5
	for s in range(longitudinal_samples + 1):
		var u: float = float(s) / float(longitudinal_samples)
		var x_index: int = clampi(int(round(u * terrain.resolution)), 0, terrain.resolution)
		var best_z: int = 0
		var best_score: float = -1.0
		for z in range(side):
			var i: int = z * side + x_index
			var score: float = terrain.flow[i] * 0.78 + terrain.moisture[i] * 0.22
			if score > best_score:
				best_score = score
				best_z = z
		var wx: float = lerpf(-half, half, u)
		var wz: float = -half + (float(best_z) / float(terrain.resolution)) * terrain.world_size
		var y: float = terrain.sample_height(wx, wz) + water_offset
		centerline.append(Vector3(wx, y, wz))
		var flow_value: float = terrain.flow[best_z * side + x_index]
		var width_factor: float = clampf((flow_value - flow_threshold) / maxf(0.001, 1.0 - flow_threshold), 0.0, 1.0)
		widths.append(base_width * lerpf(0.65, 1.35, width_factor))

func _build_water_mesh(terrain: ForestTerrain) -> void:
	if centerline.size() < 2:
		mesh = null
		return
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(centerline.size()):
		var prev: Vector3 = centerline[maxi(0, i - 1)]
		var next: Vector3 = centerline[mini(centerline.size() - 1, i + 1)]
		var tangent: Vector3 = next - prev
		tangent.y = 0.0
		if tangent.length_squared() < 0.0001:
			tangent = Vector3.RIGHT
		tangent = tangent.normalized()
		var side_vec: Vector3 = Vector3(-tangent.z, 0.0, tangent.x)
		var half_width: float = widths[i] * 0.5
		var left: Vector3 = centerline[i] - side_vec * half_width
		var right: Vector3 = centerline[i] + side_vec * half_width
		left.y = terrain.sample_height(left.x, left.z) + water_offset
		right.y = terrain.sample_height(right.x, right.z) + water_offset
		st.set_uv(Vector2(0.0, float(i) / 8.0)); st.add_vertex(left)
		st.set_uv(Vector2(1.0, float(i) / 8.0)); st.add_vertex(right)
	for i in range(centerline.size() - 1):
		var a: int = i * 2
		var b: int = a + 1
		var c: int = a + 2
		var d: int = a + 3
		st.add_index(a); st.add_index(b); st.add_index(c)
		st.add_index(b); st.add_index(d); st.add_index(c)
	st.generate_normals()
	mesh = st.commit()
