extends SceneTree

func _init() -> void:
	var scene := load("res://scenes/world/forest_map_foundation.tscn") as PackedScene
	assert(scene != null, "forest map scene must load")
	var root := scene.instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame

	var terrain := root.get_node("Terrain")
	var overview := root.get_node("OverviewCamera") as Camera3D
	var ground := root.get_node("GroundPreviewCamera") as Camera3D

	overview.global_position = Vector3(0.0, 175.0, 245.0)
	overview.look_at(Vector3(0.0, terrain.sample_height(0.0, 0.0), 0.0), Vector3.UP)
	overview.current = true
	await _capture("forest_overview.png")

	var gx := -92.0
	var gz := 112.0
	ground.global_position = Vector3(gx, terrain.sample_height(gx, gz) + 4.0, gz)
	ground.look_at(Vector3(24.0, terrain.sample_height(24.0, -18.0) + 8.0, -18.0), Vector3.UP)
	ground.current = true
	await _capture("forest_ground.png")

	print("FOREST_CAPTURE_OK")
	root.queue_free()
	quit(0)

func _capture(file_name: String) -> void:
	for _i in range(4):
		await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	var out_dir := ProjectSettings.globalize_path("res://build/forest-evidence")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var err := image.save_png(out_dir.path_join(file_name))
	assert(err == OK, "failed to save capture: " + file_name)
