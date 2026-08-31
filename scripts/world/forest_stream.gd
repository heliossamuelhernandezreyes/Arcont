@tool
class_name ForestStream
extends Node3D

@export var terrain_path: NodePath = NodePath("../Terrain")
@export_range(1.0, 20.0, 0.25) var min_width: float = 2.5
@export_range(1.0, 24.0, 0.25) var max_width: float = 8.0
@export_range(0.0, 2.0, 0.01) var water_offset: float = 0.12
@export_range(2, 16, 1) var smooth_passes: int = 6

var path_points: PackedVector3Array = PackedVector3Array()
var path_flow: PackedFloat32Array = PackedFloat32Array()

func _ready() -> void:
	build_stream()

func build_stream() -> void:
	var terrain := get_node_or_null(terrain_path) as ForestTerrain
	if terrain == null or terrain.heights.is_empty():
		return
	_build_path_from_flow(terrain)
	_build_bank_mesh(terrain)
	_build_water_mesh(terrain)

func _build_path_from_flow(terrain: ForestTerrain) -> void:
	path_points.clear()
	path_flow.clear()
	var side: int = terrain.resolution + 1
	var spacing: float = terrain.world_size / float(terrain.resolution)
	var raw_z: PackedFloat32Array = PackedFloat32Array()
	raw_z.resize(side)
	var raw_flow: PackedFloat32Array = PackedFloat32Array()
	raw_flow.resize(side)

	for x in range(side):
		var best_z: int = 0
		var best_score: float = -INF
		for z in range(side):
			var i: int = z * side + x
			var center_bias: float = 1.0 - absf(float(z) / float(terrain.resolution) - 0.5) * 0.12
			var score: float = terrain.flow[i] * center_bias
			if score > best_score:
				best_score = score
				best_z = z
		raw_z[x] = -terrain.world_size * 0.5 + float(best_z) * spacing
		raw_flow[x] = maxf(0.0, best_score)

	for _pass in range(smooth_passes):
		var filtered := raw_z.duplicate()
		for x in range(2, side - 2):
			filtered[x] = (raw_z[x - 2] + raw_z[x - 1] * 2.0 + raw_z[x] * 3.0 + raw_z[x + 1] * 2.0 + raw_z[x + 2]) / 9.0
		raw_z = filtered

	for x in range(side):
		var wx: float = -terrain.world_size * 0.5 + float(x) * spacing
		var wz: float = raw_z[x]
		var wy: float = terrain.sample_height(wx, wz) + water_offset
		path_points.append(Vector3(wx, wy, wz))
		path_flow.append(raw_flow[x])

	if path_points.size() >= 2 and path_points[0].y < path_points[path_points.size() - 1].y:
		path_points.reverse()
		path_flow.reverse()

func _build_bank_mesh(terrain: ForestTerrain) -> void:
	var mesh_instance := _mesh_child("Banks")
	mesh_instance.mesh = _build_ribbon(terrain, 1.85, -0.02)
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.115, 0.085, 0.055, 1.0)
	material.roughness = 1.0
	mesh_instance.material_override = material

func _build_water_mesh(terrain: ForestTerrain) -> void:
	var mesh_instance := _mesh_child("Water")
	mesh_instance.mesh = _build_ribbon(terrain, 1.0, 0.08)
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.055, 0.19, 0.22, 1.0)
	material.metallic = 0.0
	material.roughness = 0.24
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color.a = 0.82
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	mesh_instance.material_override = material

func _mesh_child(child_name: String) -> MeshInstance3D:
	var existing := get_node_or_null(child_name) as MeshInstance3D
	if existing != null:
		return existing
	var created := MeshInstance3D.new()
	created.name = child_name
	add_child(created)
	return created

func _build_ribbon(terrain: ForestTerrain, width_scale: float, vertical_offset: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	if path_points.size() < 2:
		return st.commit()

	for i in range(path_points.size()):
		var p: Vector3 = path_points[i]
		var prev: Vector3 = path_points[maxi(0, i - 1)]
		var next: Vector3 = path_points[mini(path_points.size() - 1, i + 1)]
		var tangent := Vector2(next.x - prev.x, next.z - prev.z).normalized()
		var normal := Vector2(-tangent.y, tangent.x)
		var flow_value: float = clampf(path_flow[i], 0.0, 1.0)
		var half_width: float = lerpf(min_width, max_width, smoothstep(0.25, 0.95, flow_value)) * 0.5 * width_scale
		var left_x: float = p.x + normal.x * half_width
		var left_z: float = p.z + normal.y * half_width
		var right_x: float = p.x - normal.x * half_width
		var right_z: float = p.z - normal.y * half_width
		var left_y: float = terrain.sample_height(left_x, left_z) + water_offset + vertical_offset
		var right_y: float = terrain.sample_height(right_x, right_z) + water_offset + vertical_offset
		st.set_uv(Vector2(0.0, float(i) / maxf(1.0, float(path_points.size() - 1)) * 12.0))
		st.add_vertex(Vector3(left_x, left_y, left_z))
		st.set_uv(Vector2(1.0, float(i) / maxf(1.0, float(path_points.size() - 1)) * 12.0))
		st.add_vertex(Vector3(right_x, right_y, right_z))

	for i in range(path_points.size() - 1):
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
