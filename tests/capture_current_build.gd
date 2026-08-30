extends SceneTree

# Visual evidence helper: starts the current playable mission, lets the live scene
# settle, then captures several real gameplay views from the player's camera.
# Observational only: no gameplay/resource files are mutated.
const MAIN := preload("res://scenes/main.tscn")
const OUTPUT_DIR := "res://build/gameplay-captures"

func _init() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var main := MAIN.instantiate()
	root.add_child(main)

	# main.tscn is direct-to-mission; the old MainMenu bootstrap no longer exists.
	for _i in range(90):
		await process_frame

	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	await _save_view("gameplay-start.png")

	var player := main.get_node_or_null("Player") as Node3D
	if player == null:
		push_error("ARCONT_GAMEPLAY_SCREENSHOT: Player unavailable")
		quit(1)
		return

	# Move through the authored village along the playable corridor. These are real
	# runtime camera views; we only reposition the player between observational shots.
	player.position = Vector3(0.0, 1.05, 28.0)
	for _i in range(20): await process_frame
	await _save_view("gameplay-village-approach.png")

	player.position = Vector3(-6.0, 1.05, 2.0)
	player.rotation.y = deg_to_rad(18.0)
	for _i in range(20): await process_frame
	await _save_view("gameplay-village-center.png")

	player.position = Vector3(5.0, 1.05, -28.0)
	player.rotation.y = deg_to_rad(170.0)
	for _i in range(20): await process_frame
	await _save_view("gameplay-north-lookback.png")

	main.queue_free()
	await process_frame
	quit(0)

func _save_view(file_name: String) -> void:
	RenderingServer.force_draw(false)
	await process_frame
	var image := root.get_viewport().get_texture().get_image()
	if image == null or image.is_empty():
		push_error("ARCONT_GAMEPLAY_SCREENSHOT: viewport image is empty for %s" % file_name)
		quit(1)
		return
	var output := OUTPUT_DIR + "/" + file_name
	var output_path := ProjectSettings.globalize_path(output)
	var err := image.save_png(output_path)
	if err != OK:
		push_error("ARCONT_GAMEPLAY_SCREENSHOT: save_png failed for %s with code %d" % [file_name, err])
		quit(1)
		return
	print("ARCONT_GAMEPLAY_SCREENSHOT|path=%s|width=%d|height=%d" % [output_path, image.get_width(), image.get_height()])
