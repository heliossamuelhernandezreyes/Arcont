extends SceneTree

func _init() -> void:
	call_deferred("_run_contract")

func _run_contract() -> void:
	var scene := load("res://scenes/world/forest_map_foundation.tscn") as PackedScene
	if scene == null:
		_fail("forest map scene must load")
		return
	var map_root := scene.instantiate()
	get_root().add_child(map_root)
	await process_frame
	var terrain := map_root.get_node_or_null("Terrain")
	if terrain == null:
		_fail("Terrain node missing")
		return
	if terrain.mesh == null:
		_fail("Terrain mesh was not generated")
		return
	if terrain.heights.size() != 16641:
		_fail("128 resolution must produce 129x129 samples")
		return
	if terrain.slopes.size() != terrain.heights.size() or terrain.moisture.size() != terrain.heights.size() or terrain.flow.size() != terrain.heights.size():
		_fail("derived terrain field size mismatch")
		return
	if terrain.get_node_or_null("TerrainBody/TerrainCollision") == null:
		_fail("terrain collision missing")
		return

	var min_h := INF
	var max_h := -INF
	var channel_count := 0
	var wet_count := 0
	var steep_count := 0
	var max_flow := 0.0
	for i in range(terrain.heights.size()):
		min_h = minf(min_h, terrain.heights[i])
		max_h = maxf(max_h, terrain.heights[i])
		max_flow = maxf(max_flow, terrain.flow[i])
		if terrain.flow[i] > 0.62: channel_count += 1
		if terrain.moisture[i] > 0.55: wet_count += 1
		if terrain.slopes[i] > 0.35: steep_count += 1

	if max_h - min_h <= 12.0:
		_fail("terrain needs meaningful vertical relief")
		return
	if max_flow <= 0.95:
		_fail("flow accumulation must normalize into a strong drainage network")
		return
	if channel_count <= 20:
		_fail("drainage network must have high-flow channel samples")
		return
	if wet_count <= channel_count:
		_fail("riparian moisture field must extend beyond the channel")
		return
	if steep_count <= 50:
		_fail("terrain needs meaningful slopes for ridges and rock masks")
		return
	var center_h: float = terrain.sample_height(0.0, 0.0)
	if not is_finite(center_h):
		_fail("height sampling must be finite")
		return
	print("FOREST_TERRAIN_OK relief=", max_h - min_h, " channels=", channel_count, " wet=", wet_count, " steep=", steep_count)
	map_root.queue_free()
	await process_frame
	quit(0)

func _fail(message: String) -> void:
	push_error("FOREST_TERRAIN_FAIL: " + message)
	quit(1)
