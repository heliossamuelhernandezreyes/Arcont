extends RefCounted
class_name AssetScaleNormalizer

const MIN_EXTENT := 0.001

static func visual_bounds(root: Node3D) -> AABB:
 var bounds := AABB()
 var has_bounds := false
 var inv := root.global_transform.affine_inverse()
 var meshes := _collect_meshes(root)
 for node in meshes:
  var mesh_instance := node as MeshInstance3D
  if mesh_instance.mesh == null:
   continue
  var relative := inv * mesh_instance.global_transform
  var transformed: AABB = relative * mesh_instance.get_aabb()
  if not has_bounds:
   bounds = transformed
   has_bounds = true
  else:
   bounds = bounds.merge(transformed)
 return bounds

static func normalize_longest_extent(root: Node3D, target_m: float) -> float:
 if target_m <= 0.0:
  return 1.0
 root.scale = Vector3.ONE
 var bounds := visual_bounds(root)
 var longest := maxf(bounds.size.x, maxf(bounds.size.y, bounds.size.z))
 if longest <= MIN_EXTENT:
  root.set_meta("metric_scale_factor", 1.0)
  root.set_meta("metric_longest_extent_m", longest)
  return 1.0
 var factor := target_m / longest
 root.scale = Vector3.ONE * factor
 root.set_meta("metric_scale_factor", factor)
 root.set_meta("metric_longest_extent_m", target_m)
 return factor

static func longest_extent(root: Node3D) -> float:
 var bounds := visual_bounds(root)
 return maxf(bounds.size.x, maxf(bounds.size.y, bounds.size.z))

static func _collect_meshes(root: Node) -> Array[Node]:
 var out: Array[Node] = []
 if root is MeshInstance3D:
  out.append(root)
 for child in root.get_children():
  out.append_array(_collect_meshes(child))
 return out
