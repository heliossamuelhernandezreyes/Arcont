@tool
class_name ForestTerrain
extends MeshInstance3D

@export_category("Terrain")
@export var seed: int = 731942
@export_range(64.0, 2048.0, 1.0) var world_size: float = 512.0
@export_range(32, 256, 1) var resolution: int = 128
@export_range(2.0, 80.0, 0.5) var relief: float = 34.0
@export_range(0.0, 24.0, 0.25) var valley_depth: float = 8.0
@export_range(0.0, 16.0, 0.25) var ridge_gain: float = 5.0
@export_range(0.0, 1.0, 0.01) var edge_falloff: float = 0.18
@export var generate_collision: bool = true
@export var regenerate: bool = false:
	set(value):
		regenerate = false
		if value and is_inside_tree():
			generate()

var heights := PackedFloat32Array()
var slopes := PackedFloat32Array()
var moisture := PackedFloat32Array()
var flow := PackedFloat32Array()
var route_mask := PackedFloat32Array()
var clearing_mask := PackedFloat32Array()
var _noise_macro := FastNoiseLite.new()
var _noise_detail := FastNoiseLite.new()

const CLEARING_CENTERS: Array[Vector2] = [
	Vector2(-126.0, 72.0),
	Vector2(22.0, -48.0),
	Vector2(146.0, 70.0)
]
const CLEARING_RADII: PackedFloat32Array = PackedFloat32Array([30.0, 43.0, 27.0])
const ROUTE_POINTS: Array[Vector2] = [
	Vector2(-238.0, 122.0),
	Vector2(-126.0, 72.0),
	Vector2(-34.0, 2.0),
	Vector2(22.0, -48.0),
	Vector2(86.0, 12.0),
	Vector2(146.0, 70.0),
	Vector2(232.0, 28.0)
]

func _ready() -> void:
	generate()

func generate() -> void:
	_setup_noise()
	_generate_height_field()
	_apply_clearings()
	_compute_derived_fields()
	_compute_composition_masks()
	_build_mesh()
	if generate_collision:
		_build_collision()

func _setup_noise() -> void:
	_noise_macro.seed = seed
	_noise_macro.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	_noise_macro.frequency = 0.0045
	_noise_macro.fractal_type = FastNoiseLite.FRACTAL_FBM
	_noise_macro.fractal_octaves = 5
	_noise_macro.fractal_gain = 0.48
	_noise_macro.fractal_lacunarity = 2.0
	_noise_macro.domain_warp_enabled = true
	_noise_macro.domain_warp_amplitude = 38.0
	_noise_macro.domain_warp_frequency = 0.003

	_noise_detail.seed = seed + 9187
	_noise_detail.noise_type = FastNoiseLite.TYPE_SIMPLEX
	_noise_detail.frequency = 0.018
	_noise_detail.fractal_type = FastNoiseLite.FRACTAL_RIDGED
	_noise_detail.fractal_octaves = 3
	_noise_detail.fractal_gain = 0.42

func _idx(x: int, z: int) -> int:
	return z * (resolution + 1) + x

func _generate_height_field() -> void:
	var side: int = resolution + 1
	heights.resize(side * side)
	for z in range(side):
		for x in range(side):
			var u: float = float(x) / float(resolution)
			var v: float = float(z) / float(resolution)
			var wx: float = (u - 0.5) * world_size
			var wz: float = (v - 0.5) * world_size
			var macro: float = _noise_macro.get_noise_2d(wx, wz)
			var detail: float = _noise_detail.get_noise_2d(wx, wz)
			var river_axis: float = (v - 0.52) - 0.16 * sin(u * TAU * 1.35 + macro * 1.6)
			var valley: float = exp(-pow(absf(river_axis) / 0.075, 2.0))
			var ridge: float = pow(absf(detail), 1.7)
			var border: float = minf(minf(u, 1.0 - u), minf(v, 1.0 - v))
			var edge: float = smoothstep(0.0, edge_falloff, border)
			var broad_relief: float = macro * relief * lerpf(1.0, 0.42, valley)
			var channel_grade: float = lerpf(5.5, -5.5, u) * valley
			var h: float = broad_relief + ridge * ridge_gain - valley * valley_depth + channel_grade
			h += (1.0 - edge) * relief * 0.22
			heights[_idx(x, z)] = h

func _apply_clearings() -> void:
	var side: int = resolution + 1
	var spacing: float = world_size / float(resolution)
	var target_heights: PackedFloat32Array = PackedFloat32Array()
	target_heights.resize(CLEARING_CENTERS.size())
	for c in range(CLEARING_CENTERS.size()):
		var center: Vector2 = CLEARING_CENTERS[c]
		var cx: int = clampi(int(round((center.x / world_size + 0.5) * resolution)), 0, resolution)
		var cz: int = clampi(int(round((center.y / world_size + 0.5) * resolution)), 0, resolution)
		target_heights[c] = heights[_idx(cx, cz)]

	for z in range(side):
		for x in range(side):
			var wx: float = -world_size * 0.5 + float(x) * spacing
			var wz: float = -world_size * 0.5 + float(z) * spacing
			var p := Vector2(wx, wz)
			var i: int = _idx(x, z)
			for c in range(CLEARING_CENTERS.size()):
				var radius: float = CLEARING_RADII[c]
				var d: float = p.distance_to(CLEARING_CENTERS[c])
				if d < radius:
					var blend: float = 1.0 - smoothstep(radius * 0.48, radius, d)
					heights[i] = lerpf(heights[i], target_heights[c], blend * 0.72)

func _compute_derived_fields() -> void:
	var side: int = resolution + 1
	var spacing: float = world_size / float(resolution)
	slopes.resize(side * side)
	moisture.resize(side * side)
	flow.resize(side * side)
	for z in range(side):
		for x in range(side):
			var xl: int = maxi(0, x - 1)
			var xr: int = mini(resolution, x + 1)
			var zd: int = maxi(0, z - 1)
			var zu: int = mini(resolution, z + 1)
			var dx: float = (heights[_idx(xr, z)] - heights[_idx(xl, z)]) / (maxf(1.0, float(xr - xl)) * spacing)
			var dz: float = (heights[_idx(x, zu)] - heights[_idx(x, zd)]) / (maxf(1.0, float(zu - zd)) * spacing)
			slopes[_idx(x, z)] = clampf(atan(Vector2(dx, dz).length()) / deg_to_rad(55.0), 0.0, 1.0)

	_compute_flow_accumulation()

	var min_h: float = INF
	var max_h: float = -INF
	for h: float in heights:
		min_h = minf(min_h, h)
		max_h = maxf(max_h, h)
	var height_span: float = maxf(0.001, max_h - min_h)
	for i in range(heights.size()):
		var lowland: float = 1.0 - clampf((heights[i] - min_h) / height_span, 0.0, 1.0)
		moisture[i] = clampf(flow[i] * 0.72 + lowland * 0.18 + (1.0 - slopes[i]) * 0.10, 0.0, 1.0)

func _compute_flow_accumulation() -> void:
	var side: int = resolution + 1
	var count: int = side * side
	var downstream := PackedInt32Array()
	downstream.resize(count)
	var accumulation := PackedFloat32Array()
	accumulation.resize(count)
	var order: Array[int] = []
	order.resize(count)

	for i in range(count):
		downstream[i] = -1
		accumulation[i] = 1.0
		order[i] = i

	for z in range(side):
		for x in range(side):
			var here: int = _idx(x, z)
			var best: int = here
			var best_h: float = heights[here]
			for oz in range(-1, 2):
				for ox in range(-1, 2):
					if ox == 0 and oz == 0:
						continue
					var nx: int = x + ox
					var nz: int = z + oz
					if nx < 0 or nx >= side or nz < 0 or nz >= side:
						continue
					var ni: int = _idx(nx, nz)
					if heights[ni] < best_h:
						best_h = heights[ni]
						best = ni
			if best != here:
				downstream[here] = best

	order.sort_custom(func(a: int, b: int) -> bool: return heights[a] > heights[b])
	for i: int in order:
		var target: int = downstream[i]
		if target >= 0:
			accumulation[target] += accumulation[i]

	var max_log: float = 0.0
	for value: float in accumulation:
		max_log = maxf(max_log, log(1.0 + value))
	for i in range(count):
		flow[i] = clampf(log(1.0 + accumulation[i]) / maxf(max_log, 0.001), 0.0, 1.0)

func _compute_composition_masks() -> void:
	var side: int = resolution + 1
	var spacing: float = world_size / float(resolution)
	route_mask.resize(side * side)
	clearing_mask.resize(side * side)
	for z in range(side):
		for x in range(side):
			var wx: float = -world_size * 0.5 + float(x) * spacing
			var wz: float = -world_size * 0.5 + float(z) * spacing
			var p := Vector2(wx, wz)
			var nearest_route: float = INF
			for s in range(ROUTE_POINTS.size() - 1):
				nearest_route = minf(nearest_route, _distance_to_segment(p, ROUTE_POINTS[s], ROUTE_POINTS[s + 1]))
			var route: float = 1.0 - smoothstep(3.8, 8.5, nearest_route)
			var clearing: float = 0.0
			for c in range(CLEARING_CENTERS.size()):
				var radius: float = CLEARING_RADII[c]
				var d: float = p.distance_to(CLEARING_CENTERS[c])
				clearing = maxf(clearing, 1.0 - smoothstep(radius * 0.72, radius, d))
			var i: int = _idx(x, z)
			route_mask[i] = route
			clearing_mask[i] = clearing

func _distance_to_segment(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab: Vector2 = b - a
	var denom: float = maxf(ab.length_squared(), 0.0001)
	var t: float = clampf((p - a).dot(ab) / denom, 0.0, 1.0)
	return p.distance_to(a + ab * t)

func _build_mesh() -> void:
	var side: int = resolution + 1
	var spacing: float = world_size / float(resolution)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for z in range(side):
		for x in range(side):
			var i: int = _idx(x, z)
			var wx: float = -world_size * 0.5 + x * spacing
			var wz: float = -world_size * 0.5 + z * spacing
			st.set_uv(Vector2(float(x) / resolution, float(z) / resolution) * 16.0)
			var composition: float = maxf(route_mask[i], clearing_mask[i] * 0.68)
			st.set_color(Color(slopes[i], moisture[i], flow[i], composition))
			st.add_vertex(Vector3(wx, heights[i], wz))
	for z in range(resolution):
		for x in range(resolution):
			var a: int = _idx(x, z)
			var b: int = _idx(x + 1, z)
			var c: int = _idx(x, z + 1)
			var d: int = _idx(x + 1, z + 1)
			st.add_index(a); st.add_index(b); st.add_index(c)
			st.add_index(b); st.add_index(d); st.add_index(c)
	st.generate_normals()
	st.generate_tangents()
	mesh = st.commit()

func _build_collision() -> void:
	var old: Node = get_node_or_null("TerrainBody")
	if old != null:
		old.queue_free()
	if mesh == null:
		return
	var body := StaticBody3D.new()
	body.name = "TerrainBody"
	var collision := CollisionShape3D.new()
	collision.name = "TerrainCollision"
	var shape := ConcavePolygonShape3D.new()
	shape.set_faces(mesh.get_faces())
	collision.shape = shape
	body.add_child(collision)
	add_child(body)

func sample_height(world_x: float, world_z: float) -> float:
	if heights.is_empty():
		return 0.0
	var fx: float = clampf((world_x / world_size + 0.5) * resolution, 0.0, resolution)
	var fz: float = clampf((world_z / world_size + 0.5) * resolution, 0.0, resolution)
	var x0: int = int(floor(fx))
	var z0: int = int(floor(fz))
	var x1: int = mini(resolution, x0 + 1)
	var z1: int = mini(resolution, z0 + 1)
	var tx: float = fx - x0
	var tz: float = fz - z0
	var h0: float = lerpf(heights[_idx(x0, z0)], heights[_idx(x1, z0)], tx)
	var h1: float = lerpf(heights[_idx(x0, z1)], heights[_idx(x1, z1)], tx)
	return lerpf(h0, h1, tz)
