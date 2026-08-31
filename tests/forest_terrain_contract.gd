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
	await process_frame
	var terrain := map_root.get_node_or_null("Terrain") as ForestTerrain
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
	if terrain.route_mask.size() != terrain.heights.size() or terrain.clearing_mask.size() != terrain.heights.size():
		_fail("composition mask size mismatch")
		return
	if terrain.get_node_or_null("TerrainBody/TerrainCollision") == null:
		_fail("terrain collision missing")
		return

	var hydrology := map_root.get_node_or_null("Hydrology") as ForestHydrology
	if hydrology == null or hydrology.mesh == null:
		_fail("hydrology mesh missing")
		return
	if hydrology.centerline.size() < 64 or hydrology.widths.size() != hydrology.centerline.size():
		_fail("stream centerline is incomplete")
		return
	var banks := hydrology.get_node_or_null("Banks") as MeshInstance3D
	if banks == null or banks.mesh == null:
		_fail("stream banks missing")
		return

	var min_h: float = INF
	var max_h: float = -INF
	var channel_count: int = 0
	var wet_count: int = 0
	var steep_count: int = 0
	var route_count: int = 0
	var clearing_count: int = 0
	var max_flow: float = 0.0
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
		if terrain.route_mask[i] > 0.55:
			route_count += 1
		if terrain.clearing_mask[i] > 0.55:
			clearing_count += 1

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
	if route_count <= 80:
		_fail("natural route corridor must occupy meaningful terrain")
		return
	if clearing_count <= 120:
		_fail("clearings must occupy meaningful terrain")
		return
	var center_h: float = terrain.sample_height(0.0, 0.0)
	if not is_finite(center_h):
		_fail("height sampling must be finite")
		return
	print("FOREST_TERRAIN_OK relief=", max_h - min_h, " channels=", channel_count, " wet=", wet_count, " steep=", steep_count, " route=", route_count, " clearings=", clearing_count, " stream_points=", hydrology.centerline.size())
	map_root.queue_free()
	await process_frame
	quit(0)

func _fail(message: String) -> void:
	push_error("FOREST_TERRAIN_FAIL: " + message)
	quit(1)
