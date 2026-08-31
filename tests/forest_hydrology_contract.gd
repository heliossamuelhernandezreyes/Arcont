extends SceneTree

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var scene := load("res://scenes/world/forest_map_foundation.tscn") as PackedScene
	assert(scene != null, "forest map scene must load")
	var root := scene.instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame
	var terrain := root.get_node("Terrain") as ForestTerrain
	var hydrology := root.get_node("Hydrology") as ForestHydrology
	assert(terrain != null, "terrain missing")
	assert(hydrology != null, "hydrology missing")
	assert(hydrology.mesh != null, "stream mesh missing")
	assert(hydrology.centerline.size() == hydrology.longitudinal_samples + 1, "stream centerline sampling mismatch")
	assert(hydrology.widths.size() == hydrology.centerline.size(), "stream width field mismatch")
	var downhill_or_flat := 0
	var rises := 0
	for i in range(1, hydrology.centerline.size()):
		var delta_y := hydrology.centerline[i].y - hydrology.centerline[i - 1].y
		if delta_y <= 0.35:
			downhill_or_flat += 1
		else:
			rises += 1
	assert(downhill_or_flat > rises * 2, "stream must mostly follow descending/flat terrain")
	var min_width := INF
	var max_width := -INF
	for width: float in hydrology.widths:
		min_width = minf(min_width, width)
		max_width = maxf(max_width, width)
	assert(min_width >= 2.0, "stream too narrow")
	assert(max_width <= 18.0, "stream too wide")
	print("FOREST_HYDROLOGY_OK samples=", hydrology.centerline.size(), " width=", min_width, "..", max_width, " rises=", rises)
	root.queue_free()
	quit(0)
