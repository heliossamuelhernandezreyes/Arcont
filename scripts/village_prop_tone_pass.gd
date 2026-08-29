extends Node

# ART-PASS-15: neutralize bright provisional props/vehicles that dominate the
# abandoned-village read in software captures. Gameplay nodes/collision stay intact.

func _ready() -> void:
 call_deferred("_apply")

func _apply() -> void:
 var env := get_parent().get_node_or_null("ForestVillage")
 if env == null:
  return
 var wood := _mat(Color(0.095,0.055,0.030),0.98)
 var vehicle := _mat(Color(0.080,0.095,0.095),0.91)
 var toned_props: int = 0
 var toned_vehicles: int = 0
 for node: Node in _all_nodes(env):
  if not node is GeometryInstance3D:
   continue
  var layer := _effective_layer(node,env)
  if layer == "prop":
   (node as GeometryInstance3D).material_override = wood
   toned_props += 1
  elif layer == "vehicle":
   (node as GeometryInstance3D).material_override = vehicle
   toned_vehicles += 1
 set_meta("art_status","ART-PASS-15-PROP-VEHICLE-TONE")
 set_meta("toned_prop_geometry",toned_props)
 set_meta("toned_vehicle_geometry",toned_vehicles)
 set_meta("visual_reason","remove bright provisional crate and vehicle dominance")

func _effective_layer(node: Node,stop: Node) -> String:
 var current: Node = node
 while current != null:
  if current.has_meta("art_layer"):
   return String(current.get_meta("art_layer",""))
  if current == stop:
   break
  current = current.get_parent()
 return ""

func _all_nodes(root: Node) -> Array[Node]:
 var out: Array[Node] = [root]
 var i: int = 0
 while i < out.size():
  var current: Node = out[i]
  for child: Node in current.get_children():
   out.append(child)
  i += 1
 return out

func _mat(color: Color,roughness: float) -> StandardMaterial3D:
 var m := StandardMaterial3D.new()
 m.albedo_color = color
 m.roughness = roughness
 return m
