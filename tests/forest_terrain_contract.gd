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
	var min_h := INF
	var max_h := -INF
	var wet_count := 0
	for i in range(terrain.heights.size()):
		min_h = minf(min_h, terrain.heights[i])
		max_h = maxf(max_h, terrain.heights[i])
		if terrain.flow[i] > 0.55:
			wet_count += 1
	assert(max_h - min_h > 12.0, "terrain needs meaningful vertical relief")
	assert(wet_count > 100, "drainage corridor must be represented")
	print("FOREST_TERRAIN_OK relief=", max_h - min_h, " drainage_samples=", wet_count)
	root.queue_free()
	quit(0)
