extends Node3D

# ART-PASS-10: temporary art-direction override for the current low-poly forest
# prototypes. It removes the cyan source-material read while the final realistic
# tree/LOD family is still being acquired and validated.

func _ready() -> void:
 call_deferred("_apply")

func _apply() -> void:
 var scatter: Node = get_parent().get_node_or_null("EnvironmentScatter")
 var polish: Node = get_parent().get_node_or_null("ForestVillagePolish")
 var tree_mat := _material(Color(0.060,0.095,0.045),0.96)
 var shrub_mat := _material(Color(0.075,0.120,0.050),0.97)
 var grass_mat := _material(Color(0.105,0.135,0.055),0.99)
 var stone_mat := _material(Color(0.205,0.215,0.195),1.0)
 var toned_cells: int = 0
 var toned_polish: int = 0
 if scatter != null:
  for node: Node in _all_nodes(scatter):
   if not node is MultiMeshInstance3D: continue
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
   if not node is GeometryInstance3D: continue
   var layer := String(node.get_meta("art_layer", ""))
   if layer == "canopy_frame_polish":
    (node as GeometryInstance3D).material_override = tree_mat
    toned_polish += 1
   elif layer == "understory_polish":
    (node as GeometryInstance3D).material_override = shrub_mat
    toned_polish += 1
   elif layer == "ground_polish":
    (node as GeometryInstance3D).material_override = grass_mat
    toned_polish += 1
 set_meta("art_status","ART-PASS-10-FOREST-TONE")
 set_meta("toned_cells",toned_cells)
 set_meta("toned_polish_geometry",toned_polish)
 set_meta("forest_tone_contract","FOREST-TONE-PLACEHOLDER-V2")
 set_meta("final_tree_asset",false)
 set_meta("reason","visual coherence until realistic tree LOD family is validated")

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
  for child: Node in current.get_children(): result.append(child)
  index += 1
 return result
