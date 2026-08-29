extends SceneTree

# Visual evidence helper: renders the current playable scene and writes a PNG.
# This is observational only; it does not mutate gameplay state or assert art quality.
const MAIN := preload("res://scenes/main.tscn")
const OUTPUT := "res://build/arcont-current-build.png"

func _init() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var main := MAIN.instantiate()
	root.add_child(main)

	# Give imports, camera, procedural environment and first-frame lighting time to settle.
	for _i in range(20):
		await process_frame

	RenderingServer.force_draw(false)
	await process_frame

	var viewport := root.get_viewport()
	var image := viewport.get_texture().get_image()
	if image == null or image.is_empty():
		push_error("ARCONT_SCREENSHOT: viewport image is empty")
		quit(1)
		return

	var output_path := ProjectSettings.globalize_path(OUTPUT)
	var err := image.save_png(output_path)
	if err != OK:
		push_error("ARCONT_SCREENSHOT: save_png failed with code %d" % err)
		quit(1)
		return

	print("ARCONT_SCREENSHOT|path=%s|width=%d|height=%d" % [output_path, image.get_width(), image.get_height()])
	main.queue_free()
	await process_frame
	quit(0)
