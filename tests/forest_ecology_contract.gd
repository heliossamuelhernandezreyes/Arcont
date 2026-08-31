extends SceneTree

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var scene := load("res://scenes/world/forest_map_foundation.tscn") as PackedScene
	if scene == null:
		_fail("forest map scene must load")
		return
	var root := scene.instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame
	var terrain := root.get_node_or_null("Terrain") as ForestTerrain
	var ecology := root.get_node_or_null("Ecology") as ForestEcology
	if terrain == null or ecology == null:
		_fail("terrain/ecology missing")
		return
	if ecology.tree_positions.size() < 350:
		_fail("forest population too sparse: " + str(ecology.tree_positions.size()))
		return
	if ecology.chunk_tree_counts.size() < 16:
		_fail("forest must be spatially chunked")
		return
	var max_chunk: int = 0
	for count_variant: Variant in ecology.chunk_tree_counts.values():
		max_chunk = maxi(max_chunk, int(count_variant))
	if max_chunk > 90:
		_fail("chunk too dense for mobile-oriented culling: " + str(max_chunk))
		return
	var violations: int = 0
	for p: Vector3 in ecology.tree_positions:
		var route: float = ecology._sample_field(terrain, terrain.route_mask, p.x, p.z)
		var clearing: float = ecology._sample_field(terrain, terrain.clearing_mask, p.x, p.z)
		var flow: float = ecology._sample_field(terrain, terrain.flow, p.x, p.z)
		if route > ecology.route_exclusion or clearing > ecology.clearing_exclusion or flow > ecology.water_exclusion:
			violations += 1
	if violations > 0:
		_fail("tree exclusion violations: " + str(violations))
		return
	var original_count: int = ecology.tree_positions.size()
	ecology.generate()
	await process_frame
	if ecology.tree_positions.size() != original_count:
		_fail("scatter must be deterministic for fixed seed")
		return
	print("FOREST_ECOLOGY_OK trees=", original_count, " chunks=", ecology.chunk_tree_counts.size(), " max_chunk=", max_chunk, " rejected_route=", ecology.rejected_route, " rejected_clearing=", ecology.rejected_clearing, " rejected_water=", ecology.rejected_water)
	root.queue_free()
	quit(0)

func _fail(message: String) -> void:
	push_error("FOREST_ECOLOGY_FAIL: " + message)
	quit(1)
