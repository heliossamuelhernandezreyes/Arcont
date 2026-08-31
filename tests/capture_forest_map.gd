extends SceneTree

const LOD_CAPTURE_DISTANCES := [3.0, 9.0, 20.0, 35.0, 80.0]
const LOD_CAPTURE_NAMES := ["forest_lod_03m.png", "forest_lod_09m.png", "forest_lod_20m.png", "forest_lod_35m.png", "forest_lod_80m.png"]

func _init() -> void:
	var scene := load("res://scenes/world/forest_map_foundation.tscn") as PackedScene
	assert(scene != null, "forest map scene must load")
	var root := scene.instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame
	await process_frame

	var terrain := root.get_node("Terrain") as ForestTerrain
	var ecology := root.get_node("Ecology") as ForestEcology
	var overview := root.get_node("OverviewCamera") as Camera3D
	var ground := root.get_node("GroundPreviewCamera") as Camera3D
	var topdown := root.get_node("TopDownCamera") as Camera3D

	_set_ecology_culling(ecology, 0.0)
	var center_h: float = terrain.sample_height(0.0, 0.0)
	overview.global_position = Vector3(0.0, 210.0, 285.0)
	overview.look_at(Vector3(0.0, center_h, -10.0), Vector3.UP)
	overview.current = true
	await _capture("forest_overview.png")

	_set_ecology_culling(ecology, 165.0)
	var gx: float = 0.0
	var gz: float = 218.0
	var gh: float = terrain.sample_height(gx, gz)
	var target_x: float = 0.0
	var target_z: float = 45.0
	var target_h: float = terrain.sample_height(target_x, target_z)
	ground.global_position = Vector3(gx, gh + 15.0, gz)
	ground.look_at(Vector3(target_x, target_h + 2.5, target_z), Vector3.UP)
	ground.current = true
	print("FOREST_GROUND_CAMERA pos=", ground.global_position, " target_h=", target_h)
	await _capture("forest_ground.png")

	await _capture_lod_distances(root, ecology)

	_set_ecology_culling(ecology, 0.0)
	topdown.global_position = Vector3(0.0, 360.0, 0.0)
	topdown.rotation_degrees = Vector3(-90.0, 0.0, 0.0)
	topdown.current = true
	await _capture("forest_topdown.png")

	print("FOREST_CAPTURE_OK trees=", ecology.tree_positions.size(), " chunks=", ecology.chunk_tree_counts.size(), " lod_views=", LOD_CAPTURE_DISTANCES.size())
	root.queue_free()
	quit(0)

func _capture_lod_distances(root: Node3D, ecology: ForestEcology) -> void:
	if ecology.tree_positions.is_empty():
		return
	var target_i := _central_tree_index(ecology.tree_positions)
	var tree_pos: Vector3 = ecology.tree_positions[target_i]
	var tree_scale: float = ecology.tree_scales[target_i]
	var camera := Camera3D.new()
	camera.name = "LODEvidenceCamera"
	camera.fov = 55.0
	camera.near = 0.08
	camera.far = 500.0
	root.add_child(camera)
	var view_dir := Vector3(0.82, 0.0, 0.57).normalized()
	var target := tree_pos + Vector3.UP * (5.5 * tree_scale)
	for i in range(LOD_CAPTURE_DISTANCES.size()):
		var distance: float = LOD_CAPTURE_DISTANCES[i]
		camera.global_position = tree_pos + view_dir * distance + Vector3.UP * (2.2 + minf(distance * 0.045, 3.0))
		camera.look_at(target, Vector3.UP)
		camera.current = true
		print("FOREST_LOD_CAMERA distance=", distance, " tree=", target_i, " pos=", camera.global_position)
		await _capture(LOD_CAPTURE_NAMES[i])
	camera.queue_free()

func _central_tree_index(positions: Array[Vector3]) -> int:
	var best_i := 0
	var best_score := INF
	for i in range(positions.size()):
		var p: Vector3 = positions[i]
		var score := Vector2(p.x, p.z).length_squared()
		if score < best_score:
			best_score = score
			best_i = i
	return best_i

func _set_ecology_culling(ecology: ForestEcology, range_end: float) -> void:
	for chunk: Node in ecology.get_children():
		for child: Node in chunk.get_children():
			var instance := child as MultiMeshInstance3D
			if instance != null:
				instance.visibility_range_end = range_end

func _capture(file_name: String) -> void:
	for _i in range(4):
		await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	var out_dir := ProjectSettings.globalize_path("res://build/forest-evidence")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var err := image.save_png(out_dir.path_join(file_name))
	assert(err == OK, "failed to save capture: " + file_name)
