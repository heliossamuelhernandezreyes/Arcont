extends Node3D

# ART-PASS-12: temporary coherence pass for the provisional low-poly forest.
# Imported FBX roots carry art-layer metadata while visible geometry may not.

func _ready() -> void:
 call_deferred("_apply")

func _apply() -> void:
 var scatter: Node = get_parent().get_node_or_null("EnvironmentScatter")
 var polish: Node = get_parent().get_node_or_null("ForestVillagePolish")
 var tree_mat := _material(Color(0.035,0.060,0.027),0.97)
 var shrub_mat := _material(Color(0.050,0.082,0.032),0.98)
 var grass_mat := _material(Color(0.070,0.090,0.036),0.99)
 var stone_mat := _material(Color(0.145,0.155,0.145),1.0)
 var toned_cells: int = 0
 var toned_polish: int = 0
 if scatter != null:
  for node: Node in _all_nodes(scatter):
   if not node is MultiMeshInstance3D:
    continue
   var kind := String(node.get_meta("biome_kind", ""))
   match kind:
    "tree": (node as MultiMeshInstance3D).material_override = tree_mat
    "shrub": (node as MultiMeshInstance3D).material_override = shrub_mat
    "grass": (node as MultiMeshInstance3D).material_override = grass_mat
    "stone": (node as MultiMeshInstance3D).material_override = stone_mat
    _: continue
   toned_cells += 1
 if polish != null:
  for node: Node in _all_nodes(polish):
   if not node is GeometryInstance3D:
    continue
   var layer := _effective_layer(node,polish)
   if layer == "canopy_frame_polish":
    (node as GeometryInstance3D).material_override = tree_mat
    toned_polish += 1
   elif layer == "understory_polish":
    (node as GeometryInstance3D).material_override = shrub_mat
    toned_polish += 1
   elif layer == "ground_polish":
    (node as GeometryInstance3D).material_override = grass_mat
    toned_polish += 1
 set_meta("art_status","ART-PASS-12-FOREST-TONE")
 set_meta("toned_cells",toned_cells)
 set_meta("toned_polish_geometry",toned_polish)
 set_meta("forest_tone_contract","FOREST-TONE-PLACEHOLDER-V4")
 set_meta("layer_resolution","nearest ancestor art_layer")
 set_meta("final_tree_asset",false)

func _effective_layer(node: Node, stop: Node) -> String:
 var current: Node = node
 while current != null:
  if current.has_meta("art_layer"):
   return String(current.get_meta("art_layer", ""))
  if current == stop:
   break
  current = current.get_parent()
 return ""

func _material(color: Color, roughness: float) -> StandardMaterial3D:
 var mat := StandardMaterial3D.new()
 mat.albedo_color = color
 mat.roughness = roughness
 mat.metallic = 0.0
 return mat

func _all_nodes(root: Node) -> Array[Node]:
 var result: Array[Node] = [root]
 var index: int = 0
 while index < result.size():
  var current: Node = result[index]
  for child: Node in current.get_children():
   result.append(child)
  index += 1
 return result
