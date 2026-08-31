extends SceneTree

func _init() -> void:
	var scene := load("res://scenes/world/forest_map_foundation.tscn") as PackedScene
	assert(scene != null, "forest map scene must load")
	var root := scene.instantiate()
	get_root().add_child(root)
	await process_frame
	var terrain := root.get_node_or_null("Terrain")
	assert(terrain != null, "Terrain node missing")
	assert(terrain.mesh != null, "Terrain mesh was not generated")
	assert(terrain.heights.size() == 16641, "128 resolution must produce 129x129 samples")
	assert(terrain.slopes.size() == terrain.heights.size(), "slope field mismatch")
	assert(terrain.moisture.size() == terrain.heights.size(), "moisture field mismatch")
	assert(terrain.flow.size() == terrain.heights.size(), "flow field mismatch")
	assert(terrain.get_node_or_null("TerrainBody/TerrainCollision") != null, "terrain collision missing")

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
		if terrain.flow[i] > 0.62:
			channel_count += 1
		if terrain.moisture[i] > 0.55:
			wet_count += 1
		if terrain.slopes[i] > 0.35:
			steep_count += 1

	assert(max_h - min_h > 12.0, "terrain needs meaningful vertical relief")
	assert(max_flow > 0.95, "flow accumulation must normalize into a strong drainage network")
	assert(channel_count > 20, "drainage network must have high-flow channel samples")
	assert(wet_count > channel_count, "riparian moisture field must extend beyond the channel")
	assert(steep_count > 50, "terrain needs meaningful slopes for ridges and rock masks")
	var center_h: float = terrain.sample_height(0.0, 0.0)
	assert(is_finite(center_h), "height sampling must be finite")
	print("FOREST_TERRAIN_OK relief=", max_h - min_h, " channels=", channel_count, " wet=", wet_count, " steep=", steep_count)
	root.queue_free()
	quit(0)
