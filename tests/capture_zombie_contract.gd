extends SceneTree

# Rendered P0 evidence for the infected animation contract. This intentionally
# drives the same runtime visual adapter used by enemy.tscn and captures three
# semantic poses so CI cannot confuse animation-name presence with deformation.
const ENEMY := preload("res://scenes/enemy.tscn")
const OUTPUT_DIR := "res://build/zombie-contract-captures"

func _init() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var stage := Node3D.new()
	stage.name = "ZombieVisualEvidenceStage"
	root.add_child(stage)

	var environment_node := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.055, 0.065, 0.075)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.82, 0.86, 0.92)
	environment.ambient_light_energy = 1.35
	environment_node.environment = environment
	stage.add_child(environment_node)

	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-38.0, -32.0, 0.0)
	key.light_energy = 1.8
	key.shadow_enabled = true
	stage.add_child(key)

	var floor_mesh := MeshInstance3D.new()
	var floor_box := BoxMesh.new()
	floor_box.size = Vector3(7.0, 0.12, 7.0)
	floor_mesh.mesh = floor_box
	floor_mesh.position = Vector3(0.0, -0.08, 0.0)
	stage.add_child(floor_mesh)

	var enemy := ENEMY.instantiate() as CharacterBody3D
	if enemy == null:
		_fail("enemy scene did not instantiate")
		return
	stage.add_child(enemy)
	enemy.global_position = Vector3.ZERO

	var camera := Camera3D.new()
	stage.add_child(camera)
	camera.global_position = Vector3(0.0, 1.18, 4.15)
	camera.look_at(Vector3(0.0, 1.02, 0.0), Vector3.UP)
	camera.fov = 48.0
	camera.current = true

	for _i in range(20): await process_frame
	var visual := enemy.get_node_or_null("CC0Visual")
	if visual == null:
		_fail("CC0Visual adapter unavailable")
		return
	if String(visual.call("get_animation_contract")) != "semantic_native":
		_fail("infected visual is not semantic_native: %s" % String(visual.call("get_animation_contract")))
		return
	if not bool(visual.call("is_shell_active")):
		_fail("infected semantic shell is inactive")
		return

	# The host AI normally selects idle/move every frame. Disable only the adapter's
	# automatic selector while preserving its AnimationPlayer child, then drive the
	# semantic clips explicitly so each screenshot is an unambiguous deformation test.
	visual.set_process(false)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))

	visual.call("_play_best", ["idle", "zombie"], false, true)
	for _i in range(12): await process_frame
	await _save("zombie-idle.png", visual, ["idle", "zombie"])

	visual.call("_play_best", ["walk", "run"], true, true)
	for _i in range(12): await process_frame
	await _save("zombie-move.png", visual, ["walk", "run"])

	visual.call("_play_best", ["punch", "attack"], false, true)
	for _i in range(9): await process_frame
	await _save("zombie-attack.png", visual, ["punch", "attack"])

	stage.queue_free()
	await process_frame
	quit(0)

func _save(file_name: String, visual: Node, expected_tokens: Array) -> void:
	var current := String(visual.call("get_current_animation"))
	var lowered := current.to_lower()
	var semantic_ok := false
	for token_variant in expected_tokens:
		if String(token_variant).to_lower() in lowered:
			semantic_ok = true
			break
	if not semantic_ok:
		_fail("%s selected wrong semantic animation: %s" % [file_name, current])
		return
	RenderingServer.force_draw(false)
	await process_frame
	var image := root.get_viewport().get_texture().get_image()
	if image == null or image.is_empty():
		_fail("empty viewport image for %s" % file_name)
		return
	var path := ProjectSettings.globalize_path(OUTPUT_DIR + "/" + file_name)
	var err := image.save_png(path)
	if err != OK:
		_fail("save_png failed for %s with code %d" % [file_name, err])
		return
	print("ARCONT_ZOMBIE_CAPTURE|path=%s|animation=%s|source=%s|width=%d|height=%d" % [path, current, String(visual.call("get_source_asset")), image.get_width(), image.get_height()])

func _fail(message: String) -> void:
	push_error("ARCONT_ZOMBIE_CAPTURE: %s" % message)
	quit(1)
