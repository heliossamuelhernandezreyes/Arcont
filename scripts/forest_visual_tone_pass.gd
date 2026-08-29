extends Node3D

# ART-PASS-10C: temporary art-direction override for the current low-poly forest
# prototypes. Imported FBX roots carry the art-layer metadata while their visible
# GeometryInstance3D children usually do not, so layer lookup must walk ancestors.

func _ready() -> void:
 call_deferred("_apply")

func _apply() -> void:
 var scatter: Node = get_parent().get_node_or_null("EnvironmentScatter")
 var polish: Node = get_parent().get_node_or_null("ForestVillagePolish")
 var tree_mat := _material(Color(0.052,0.080,0.038),0.97)
 var shrub_mat := _material(Color(0.065,0.103,0.044),0.98)
 var grass_mat := _material(Color(0.090,0.115,0.048),0.99)
 var stone_mat := _material(Color(0.185,0.192,0.177),1.0)
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
   var layer := _effective_layer(node, polish)
   if layer == "canopy_frame_polish":
    (node as GeometryInstance3D).material_override = tree_mat
    toned_polish += 1
   elif layer == "understory_polish":
    (node as GeometryInstance3D).material_override = shrub_mat
    toned_polish += 1
   elif layer == "ground_polish":
    (node as GeometryInstance3D).material_override = grass_mat
    toned_polish += 1
 set_meta("art_status","ART-PASS-10C-FOREST-TONE")
 set_meta("toned_cells",toned_cells)
 set_meta("toned_polish_geometry",toned_polish)
 set_meta("forest_tone_contract","FOREST-TONE-PLACEHOLDER-V3")
 set_meta("layer_resolution","nearest ancestor art_layer")
 set_meta("final_tree_asset",false)
 set_meta("reason","visual coherence until realistic tree LOD family is validated")

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
