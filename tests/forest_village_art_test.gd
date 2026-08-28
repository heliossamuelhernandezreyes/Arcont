extends SceneTree

const ENV_SCRIPT := preload("res://scripts/forest_village_environment.gd")

func _init() -> void:
 call_deferred("_run")

func _run() -> void:
 var root3d := Node3D.new()
 root.add_child(root3d)
 var budget_script := load("res://scripts/performance_budget.gd")
 var budget := Node.new()
 budget.name = "PerformanceBudget"
 budget.set_script(budget_script)
 root3d.add_child(budget)
 var env := Node3D.new()
 env.name = "ForestVillage"
 env.set_script(ENV_SCRIPT)
 root3d.add_child(env)
 await process_frame
 await process_frame
 var chunks := 0
 var village := 0
 var canopy := 0
 var landmarks := 0
 var story := 0
 var spawns := get_nodes_in_group("enemy_spawn").size()
 for node in _all_nodes(env):
  if String(node.name).begins_with("ForestChunk_"): chunks += 1
  if node.has_meta("art_layer"):
   match String(node.get_meta("art_layer")):
    "village": village += 1
    "canopy": canopy += 1
    "landmark", "landform": landmarks += 1
    "story_prop": story += 1
 if chunks < 4: return _fail("forest needs spatial chunks: %d" % chunks)
 if village < 8: return _fail("village massing incomplete: %d" % village)
 if canopy < 20: return _fail("forest canopy too sparse: %d" % canopy)
 if landmarks < 5: return _fail("landmark/landform hierarchy incomplete: %d" % landmarks)
 if story < 2: return _fail("environmental storytelling missing")
 if spawns < 8: return _fail("forest enemy approach lanes missing: %d" % spawns)
 print("FOREST_VILLAGE_ART|chunks=%d|village=%d|canopy=%d|landmarks=%d|story=%d|spawns=%d" % [chunks,village,canopy,landmarks,story,spawns])
 print("ARCONT FOREST VILLAGE: ART-PASS-1 contract OK")
 root3d.queue_free()
 await process_frame
 quit(0)

func _all_nodes(node: Node) -> Array[Node]:
 var result: Array[Node] = [node]
 for child in node.get_children(): result.append_array(_all_nodes(child))
 return result

func _fail(message: String) -> void:
 push_error(message)
 quit(1)
