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
	var hydrology := root.get_node_or_null("Hydrology") as ForestHydrology
	if terrain == null:
		_fail("terrain missing")
		return
	if hydrology == null:
		_fail("hydrology missing")
		return
	if hydrology.mesh == null:
		_fail("stream mesh missing")
		return
	if hydrology.centerline.size() != hydrology.longitudinal_samples + 1:
		_fail("stream centerline sampling mismatch")
		return
	if hydrology.widths.size() != hydrology.centerline.size():
		_fail("stream width field mismatch")
		return
	var downhill_or_flat: int = 0
	var rises: int = 0
	for i in range(1, hydrology.centerline.size()):
		var delta_y: float = hydrology.centerline[i].y - hydrology.centerline[i - 1].y
		if delta_y <= 0.35:
			downhill_or_flat += 1
		else:
			rises += 1
	if downhill_or_flat <= rises * 2:
		_fail("stream must mostly follow descending/flat terrain; rises=" + str(rises))
		return
	var min_width: float = INF
	var max_width: float = -INF
	for width: float in hydrology.widths:
		min_width = minf(min_width, width)
		max_width = maxf(max_width, width)
	if min_width < 2.0:
		_fail("stream too narrow: " + str(min_width))
		return
	if max_width > 18.0:
		_fail("stream too wide: " + str(max_width))
		return
	print("FOREST_HYDROLOGY_OK samples=", hydrology.centerline.size(), " width=", min_width, "..", max_width, " rises=", rises)
	root.queue_free()
	quit(0)

func _fail(message: String) -> void:
	push_error("FOREST_HYDROLOGY_FAIL: " + message)
	quit(1)
