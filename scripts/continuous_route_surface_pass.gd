extends Node3D

# ART-PASS-10: turn correctness-first BoxMesh route segments into thin,
# terrain-sampled visual surfaces. ForestTerrainRelief remains the only ground
# collision owner; this pass is visual-only and preserves authored route groups.

var terrain: Node

func _ready() -> void:
 call_deferred("_build")

func _build() -> void:
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 var env := get_parent().get_node_or_null("ForestVillage")
 if env == null or terrain == null or not terrain.has_method("get_height_at"):
  return
 var converted := 0
 var source_segments := 0
 for child in env.get_children():
  if child is Node3D and bool(child.get_meta("terrain_following_path", false)):
   var result := _convert_group(child as Node3D)
   if bool(result.get("ok", false)):
    converted += 1
    source_segments += int(result.get("segments", 0))
 set_meta("art_status", "ART-PASS-10-CONTINUOUS-ROUTES")
 set_meta("route_surface_contract", "CONTINUOUS-ROUTE-SURFACE-V1")
 set_meta("converted_groups", converted)
 set_meta("source_segments", source_segments)
 set_meta("collision_owner", "ForestTerrainRelief")
 set_meta("mobile_validation", "PENDING")

func _convert_group(group: Node3D) -> Dictionary:
 var segments: Array[MeshInstance3D] = []
 for child in group.get_children():
  if child is MeshInstance3D and (child as MeshInstance3D).mesh is BoxMesh:
   segments.append(child as MeshInstance3D)
 if segments.is_empty():
  return {"ok": false, "segments": 0}

 var st := SurfaceTool.new()
 st.begin(Mesh.PRIMITIVE_TRIANGLES)
 var first_material: Material = segments[0].material_override
 var uv_scale := 0.18
 for segment in segments:
  var box := segment.mesh as BoxMesh
  var half_x := box.size.x * 0.5
  var half_z := box.size.z * 0.5
  var visual_offset := segment.global_position.y - _height(segment.global_position.x, segment.global_position.z)
  var corners := [
   Vector3(-half_x, 0.0, -half_z), Vector3(half_x, 0.0, -half_z),
   Vector3(half_x, 0.0, half_z), Vector3(-half_x, 0.0, half_z)
  ]
  var p: Array[Vector3] = []
  for local_corner in corners:
   var world := segment.global_transform * local_corner
   world.y = _height(world.x, world.z) + visual_offset + 0.008
   p.append(to_local(world))
  _triangle(st, p[0], p[1], p[2], uv_scale)
  _triangle(st, p[0], p[2], p[3], uv_scale)

 st.generate_normals()
 var mesh := st.commit()
 if mesh == null:
  return {"ok": false, "segments": segments.size()}
 var surface := MeshInstance3D.new()
 surface.name = "%s_ContinuousSurface" % group.name
 surface.mesh = mesh
 surface.material_override = first_material
 surface.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 surface.set_meta("art_layer", String(group.get_meta("art_layer", "terrain_path")))
 surface.set_meta("terrain_following_path", true)
 surface.set_meta("continuous_route_surface", true)
 surface.set_meta("source_segment_count", segments.size())
 surface.set_meta("terrain_sample_source", "ForestTerrainRelief.get_height_at")
 surface.set_meta("route_surface_contract", "CONTINUOUS-ROUTE-SURFACE-V1")
 add_child(surface)
 group.visible = false
 group.set_meta("superseded_visual_by", surface.name)
 return {"ok": true, "segments": segments.size()}

func _triangle(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, uv_scale: float) -> void:
 st.set_uv(Vector2(a.x, a.z) * uv_scale); st.add_vertex(a)
 st.set_uv(Vector2(b.x, b.z) * uv_scale); st.add_vertex(b)
 st.set_uv(Vector2(c.x, c.z) * uv_scale); st.add_vertex(c)

func _height(x: float, z: float) -> float:
 return float(terrain.call("get_height_at", x, z))
