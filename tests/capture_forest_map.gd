extends SceneTree

func _init() -> void:
	var scene := load("res://scenes/world/forest_map_foundation.tscn") as PackedScene
	assert(scene != null, "forest map scene must load")
	var root := scene.instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame

	var terrain := root.get_node("Terrain") as ForestTerrain
	var ecology := root.get_node("Ecology") as ForestEcology
	var overview := root.get_node("OverviewCamera") as Camera3D
	var ground := root.get_node("GroundPreviewCamera") as Camera3D
	var topdown := root.get_node("TopDownCamera") as Camera3D

	# Evidence cameras intentionally disable distance culling so macro captures can verify
	# the ecological distribution. Runtime visibility ranges remain unchanged in the scene.
	_set_ecology_culling(ecology, 0.0)
	var center_h: float = terrain.sample_height(0.0, 0.0)
	overview.global_position = Vector3(0.0, 210.0, 285.0)
	overview.look_at(Vector3(0.0, center_h, -10.0), Vector3.UP)
	overview.current = true
	await _capture("forest_overview.png")

	# Ground evidence restores the intended mobile visibility range.
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

	_set_ecology_culling(ecology, 0.0)
	topdown.global_position = Vector3(0.0, 360.0, 0.0)
	topdown.rotation_degrees = Vector3(-90.0, 0.0, 0.0)
	topdown.current = true
	await _capture("forest_topdown.png")

	print("FOREST_CAPTURE_OK trees=", ecology.tree_positions.size(), " chunks=", ecology.chunk_tree_counts.size())
	root.queue_free()
	quit(0)

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
