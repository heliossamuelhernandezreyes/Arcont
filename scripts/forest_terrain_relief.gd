extends Node3D

# Continuous deterministic terrain for the forest-village vertical slice.
# One grid drives both rendering and HeightMapShape3D collision so the player,
# vegetation and tactical landmarks can share the same authored relief contract.
@export var seed := 84721
@export var map_width := 171
@export var map_depth := 221
@export var cell_size := 1.0
@export var height_scale := 1.0

var heights := PackedFloat32Array()
var terrain_material: StandardMaterial3D

func _ready() -> void:
 terrain_material = _material(Color(0.085, 0.125, 0.052), 0.98)
 _build_height_field()
 _build_render_mesh()
 _build_collision()
 set_meta("art_layer", "continuous_forest_relief")
 set_meta("art_status", "ART-PASS-4-HEIGHTMAP")
 set_meta("terrain_grid", Vector2i(map_width, map_depth))
 set_meta("design_rule", "village basin + outer ridges + drainage valley + tactical corridors")

func _material(color: Color, roughness: float) -> StandardMaterial3D:
 var m := StandardMaterial3D.new()
 m.albedo_color = color
 m.roughness = roughness
 return m

func _build_height_field() -> void:
 heights.resize(map_width * map_depth)
 var half_x := float(map_width - 1) * 0.5
 var half_z := float(map_depth - 1) * 0.5
 for z in range(map_depth):
  for x in range(map_width):
   var wx := (float(x) - half_x) * cell_size
   var wz := (float(z) - half_z) * cell_size
   heights[z * map_width + x] = _height_at_world(wx, wz)

func _height_at_world(x: float, z: float) -> float:
 # Low-frequency deterministic noise without runtime Noise resources.
 var broad := sin(x * 0.041 + float(seed) * 0.00013) * 0.72
 broad += cos(z * 0.034 - float(seed) * 0.00017) * 0.58
 broad += sin((x + z) * 0.023) * 0.44
 # Outer forest rises into a natural bowl around the settlement.
 var nx := absf(x) / 85.0
 var nz := absf(z - 5.0) / 110.0
 var edge := clamp(maxf(nx, nz), 0.0, 1.25)
 var ridge := pow(maxf(edge - 0.38, 0.0), 1.65) * 7.0
 # Keep village and main combat spine readable and traversable.
 var village_d := Vector2(x, z - 18.0).length()
 var basin_mask := smoothstep(22.0, 58.0, village_d)
 var h := (broad * 0.72 + ridge) * basin_mask
 # Drainage valley around the stream crossing near z=-40.
 var stream_d := absf(z + 40.0 + sin(x * 0.035) * 2.4)
 var stream_cut := (1.0 - smoothstep(3.0, 14.0, stream_d)) * 1.35
 h -= stream_cut
 # Main north/south road gets a gentle grading corridor.
 var road_d := absf(x - sin(z * 0.018) * 2.5)
 var road_mask := 1.0 - smoothstep(5.0, 13.0, road_d)
 h = lerpf(h, h * 0.28, road_mask * 0.72)
 return h * height_scale

func get_height_at(world_x: float, world_z: float) -> float:
 return _height_at_world(world_x, world_z)

func get_slope_at(world_x: float, world_z: float) -> float:
 var step := maxf(cell_size, 0.5)
 var dx := _height_at_world(world_x + step, world_z) - _height_at_world(world_x - step, world_z)
 var dz := _height_at_world(world_x, world_z + step) - _height_at_world(world_x, world_z - step)
 return Vector2(dx, dz).length() / (2.0 * step)

func _build_render_mesh() -> void:
 var vertices := PackedVector3Array()
 var normals := PackedVector3Array()
 var uvs := PackedVector2Array()
 var indices := PackedInt32Array()
 vertices.resize(map_width * map_depth)
 normals.resize(map_width * map_depth)
 uvs.resize(map_width * map_depth)
 var half_x := float(map_width - 1) * 0.5
 var half_z := float(map_depth - 1) * 0.5
 for z in range(map_depth):
  for x in range(map_width):
   var idx := z * map_width + x
   var wx := (float(x) - half_x) * cell_size
   var wz := (float(z) - half_z) * cell_size
   vertices[idx] = Vector3(wx, heights[idx], wz)
   uvs[idx] = Vector2(float(x) / 12.0, float(z) / 12.0)
   var h_l := _sample_grid(x - 1, z)
   var h_r := _sample_grid(x + 1, z)
   var h_d := _sample_grid(x, z - 1)
   var h_u := _sample_grid(x, z + 1)
   normals[idx] = Vector3(h_l - h_r, 2.0 * cell_size, h_d - h_u).normalized()
 for z in range(map_depth - 1):
  for x in range(map_width - 1):
   var a := z * map_width + x
   var b := a + 1
   var c := a + map_width
   var d := c + 1
   indices.append_array(PackedInt32Array([a, c, b, b, c, d]))
 var arrays := []
 arrays.resize(Mesh.ARRAY_MAX)
 arrays[Mesh.ARRAY_VERTEX] = vertices
 arrays[Mesh.ARRAY_NORMAL] = normals
 arrays[Mesh.ARRAY_TEX_UV] = uvs
 arrays[Mesh.ARRAY_INDEX] = indices
 var mesh := ArrayMesh.new()
 mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
 var visual := MeshInstance3D.new()
 visual.name = "ContinuousTerrain"
 visual.mesh = mesh
 visual.material_override = terrain_material
 visual.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
 visual.visibility_range_end = 240.0
 visual.visibility_range_end_margin = 18.0
 visual.set_meta("terrain_surface", true)
 add_child(visual)

func _sample_grid(x: int, z: int) -> float:
 var sx := clampi(x, 0, map_width - 1)
 var sz := clampi(z, 0, map_depth - 1)
 return heights[sz * map_width + sx]

func _build_collision() -> void:
 var body := StaticBody3D.new()
 body.name = "TerrainCollision"
 var collision := CollisionShape3D.new()
 collision.name = "HeightMapCollision"
 var shape := HeightMapShape3D.new()
 shape.map_width = map_width
 shape.map_depth = map_depth
 shape.map_data = heights
 collision.shape = shape
 collision.scale = Vector3(cell_size, 1.0, cell_size)
 body.add_child(collision)
 body.set_meta("collision_type", "HeightMapShape3D")
 add_child(body)
