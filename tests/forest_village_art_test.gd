extends SceneTree

# Forest composition regression contract extended for CC0 MultiMesh canopy and
# ART-PASS-8 terrain grounding.
const MAIN := preload("res://scenes/main.tscn")

func _init() -> void:
 call_deferred("_run")

func _run() -> void:
 var main := MAIN.instantiate()
 root.add_child(main)
 await process_frame
 await process_frame
 var env := main.get_node_or_null("ForestVillage")
 var polish := main.get_node_or_null("ForestVillagePolish")
 var scatter := main.get_node_or_null("EnvironmentScatter")
 if env == null: return _fail("ForestVillage missing")
 if polish == null: return _fail("ForestVillagePolish missing")
 if scatter == null: return _fail("EnvironmentScatter missing")
 var chunks := 0
 var village := 0
 var legacy_canopy := 0
 var canopy_instances := 0
 var cc0_tree_cells := 0
 var landmarks := 0
 var story := 0
 var terrain_paths := 0
 var terrain_grounded := 0
 var path_segments := 0
 var macro_occluders := 0
 var transitions := 0
 var mission_landmarks := 0
 var story_chain := 0
 var canopy_frames := 0
 var entrance_layers := 0
 var accent_lights := 0
 var shadowed_omni := 0
 var budgeted := 0
 for node in _all_nodes(env):
  if String(node.name).begins_with("ForestChunk_"): chunks += 1
  if bool(node.get_meta("terrain_following_path",false)):
   terrain_paths += 1
   path_segments += int(node.get_meta("segment_count",0))
  if bool(node.get_meta("terrain_grounded",false)): terrain_grounded += 1
  if node.has_meta("art_layer"):
   match String(node.get_meta("art_layer")):
    "village": village += 1
    "canopy": legacy_canopy += 1
    "landmark", "landform": landmarks += 1
    "story_prop": story += 1
 for node in _all_nodes(scatter):
  if not node.has_meta("biome_kind") or String(node.get_meta("biome_kind","")) != "tree": continue
  if not node.has_meta("accepted_instances"): continue
  canopy_instances += int(node.get_meta("accepted_instances",0))
  if bool(node.get_meta("cc0_runtime",false)):
   cc0_tree_cells += 1
 for node in _all_nodes(polish):
  if node.has_meta("art_layer"):
   var layer := String(node.get_meta("art_layer"))
   match layer:
    "macro_occluder": macro_occluders += 1
    "macro_transition": transitions += 1
    "mission_landmark": mission_landmarks += 1
    "story_chain": story_chain += 1
    "canopy_frame_polish": canopy_frames += 1
    "accent_light": accent_lights += 1
   if layer.begins_with("entrance_"): entrance_layers += 1
  if node.has_meta("base_visibility_end"): budgeted += 1
  if node is OmniLight3D and (node as OmniLight3D).shadow_enabled: shadowed_omni += 1
 var spawns := get_nodes_in_group("enemy_spawn").size()
 if chunks < 4: return _fail("forest needs spatial chunks: %d" % chunks)
 if village < 8: return _fail("village massing incomplete: %d" % village)
 if canopy_instances < 20: return _fail("consolidated forest canopy too sparse: %d" % canopy_instances)
 if cc0_tree_cells < 4: return _fail("CC0 tree scatter cells missing: %d" % cc0_tree_cells)
 if legacy_canopy != 0: return _fail("legacy individual canopy duplicates remain: %d" % legacy_canopy)
 if landmarks < 5: return _fail("landmark/landform hierarchy incomplete: %d" % landmarks)
 if story < 2: return _fail("base environmental storytelling missing")
 if terrain_paths < 12: return _fail("terrain-following route coverage incomplete: %d" % terrain_paths)
 if path_segments < 70: return _fail("terrain route segmentation too coarse/missing: %d" % path_segments)
 if terrain_grounded < 45: return _fail("too few grounded village/route nodes: %d" % terrain_grounded)
 if env.get_node_or_null("ForestGroundCollision") != null: return _fail("legacy flat ForestGroundCollision must stay removed")
 if String(env.get_meta("art_status","")) != "ART-PASS-8-TERRAIN-GROUNDING": return _fail("terrain grounding art status missing")
 if spawns < 8: return _fail("forest enemy approach lanes missing: %d" % spawns)
 if macro_occluders < 8: return _fail("macro occlusion hierarchy incomplete: %d" % macro_occluders)
 if transitions < 4: return _fail("forest-to-village transition bands incomplete: %d" % transitions)
 if mission_landmarks < 10: return _fail("mission landmarks are not visually anchored: %d" % mission_landmarks)
 if story_chain < 8: return _fail("retreat story chain too weak: %d" % story_chain)
 if canopy_frames < 10: return _fail("entrance framing canopy incomplete: %d" % canopy_frames)
 if entrance_layers < 12: return _fail("four entrance identities incomplete: %d" % entrance_layers)
 if accent_lights != 3: return _fail("polish lighting budget changed: %d" % accent_lights)
 if shadowed_omni != 0: return _fail("polish OmniLights must remain unshadowed")
 if budgeted < 45: return _fail("polish layer lacks visibility budgeting: %d" % budgeted)
 if String(polish.get_meta("art_status","")) != "ART-PASS-2-POLISHED": return _fail("polish art status missing")
 if String(scatter.get_meta("art_status","")) != "ART-PASS-7-CC0-SCATTER": return _fail("CC0 scatter art status missing")
 var moon := main.get_node_or_null("MoonLight") as DirectionalLight3D
 if moon == null or not moon.shadow_enabled: return _fail("moon must remain the primary shadowed key")
 print("FOREST_VILLAGE_ART|chunks=%d|village=%d|canopy_instances=%d|cc0_tree_cells=%d|terrain_paths=%d|path_segments=%d|grounded=%d|landmarks=%d|spawns=%d|macro=%d|transitions=%d|mission=%d|story_chain=%d|frames=%d|entrances=%d|budgeted=%d" % [chunks,village,canopy_instances,cc0_tree_cells,terrain_paths,path_segments,terrain_grounded,landmarks,spawns,macro_occluders,transitions,mission_landmarks,story_chain,canopy_frames,entrance_layers,budgeted])
 print("ARCONT FOREST VILLAGE: terrain grounding + polished composition + CC0 MultiMesh canopy OK")
 main.queue_free()
 await process_frame
 quit(0)

func _all_nodes(node: Node) -> Array[Node]:
 var result: Array[Node] = [node]
 for child in node.get_children(): result.append_array(_all_nodes(child))
 return result

func _fail(message: String) -> void:
 push_error(message)
 quit(1)
