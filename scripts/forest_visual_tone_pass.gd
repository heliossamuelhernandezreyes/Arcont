extends Node3D

# ART-PASS-10: temporary art-direction override for the current low-poly CC0
# forest prototypes. This removes the cyan source-material read while the final
# realistic tree/LOD family is still being acquired and validated.

func _ready() -> void:
 call_deferred("_apply")

func _apply() -> void:
 var scatter := get_parent().get_node_or_null("EnvironmentScatter")
 if scatter == null:
  return
 var tree_mat := _material(Color(0.075, 0.115, 0.060), 0.94)
 var shrub_mat := _material(Color(0.095, 0.145, 0.065), 0.96)
 var grass_mat := _material(Color(0.125, 0.155, 0.070), 0.98)
 var stone_mat := _material(Color(0.205, 0.215, 0.195), 1.0)
 var toned := 0
 for node in _all_nodes(scatter):
  if not node is MultiMeshInstance3D:
   continue
  var kind := String(node.get_meta("biome_kind", ""))
  match kind:
   "tree": (node as MultiMeshInstance3D).material_override = tree_mat
   "shrub": (node as MultiMeshInstance3D).material_override = shrub_mat
   "grass": (node as MultiMeshInstance3D).material_override = grass_mat
   "stone": (node as MultiMeshInstance3D).material_override = stone_mat
   _: continue
  toned += 1
 set_meta("art_status", "ART-PASS-10-FOREST-TONE")
 set_meta("toned_cells", toned)
 set_meta("forest_tone_contract", "FOREST-TONE-PLACEHOLDER-V1")
 set_meta("final_tree_asset", false)
 set_meta("reason", "visual coherence until realistic tree LOD family is validated")

func _material(color: Color, roughness: float) -> StandardMaterial3D:
 var mat := StandardMaterial3D.new()
 mat.albedo_color = color
 mat.roughness = roughness
 mat.metallic = 0.0
 return mat

func _all_nodes(root: Node) -> Array[Node]:
 var result: Array[Node] = [root]
 var index := 0
 while index < result.size():
  var current := result[index]
  for child in current.get_children():
   result.append(child)
  index += 1
 return result
