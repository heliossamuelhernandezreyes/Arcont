extends SceneTree

const MAIN := preload("res://scenes/main.tscn")
const OUTPUT_DIR := "res://build/character-contract-captures"

func _init() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var main := MAIN.instantiate()
	root.add_child(main)
	for _i in range(8): await process_frame
	var menu := main.get_node_or_null("MainMenu")
	if menu == null or not menu.has_method("_start"):
		push_error("ARCONT_CHARACTER_CAPTURE: MainMenu start path unavailable")
		quit(1)
		return
	menu.call("_start")
	for _i in range(75): await process_frame

	var player := main.get_node_or_null("Player") as CharacterBody3D
	var weapon := main.get_node_or_null("Player/Weapon")
	var tps := main.get_node_or_null("Player/ThirdPersonADS")
	var spring_arm := main.get_node_or_null("Player/CameraRig/SpringArm3D") as SpringArm3D
	if player == null or weapon == null or not weapon.has_method("set_ads") or tps == null or spring_arm == null:
		push_error("ARCONT_CHARACTER_CAPTURE: player/weapon/TPS contract unavailable")
		quit(1)
		return

	# Controlled but real mission view: keep the live player, renderer, environment,
	# camera, animation tree and weapon stack. Reposition only to make the operator
	# readable rather than judging TPS through a random occluding tree.
	player.global_position = Vector3(0.0, 2.2, 28.0)
	player.velocity = Vector3.ZERO
	player.set("camera_yaw", 0.0)
	player.set("pitch", -0.12)
	var rig := player.get_node_or_null("CameraRig") as Node3D
	if rig != null: rig.rotation = Vector3(-0.12, 0.0, 0.0)
	weapon.call("set_ads", false)
	for _i in range(35): await process_frame
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	await _save("player-hip-tps.png")

	weapon.call("set_ads", true)
	for _i in range(35): await process_frame
	await _save("player-ads.png")

	weapon.call("set_ads", false)
	player.velocity = Vector3(4.2, 0.0, -4.2)
	for _i in range(18): await process_frame
	await _save("player-moving.png")

	# Controlled SpringArm-compression stress capture. This reproduces the old
	# disappearance condition without depending on random world geometry: freeze
	# the TPS controller for one evidence frame, shorten the live SpringArm to the
	# exact safety distance, and verify the body render contract before capture.
	player.velocity = Vector3.ZERO
	weapon.call("set_ads", false)
	tps.process_mode = Node.PROCESS_MODE_DISABLED
	spring_arm.spring_length = float(tps.get("minimum_safe_distance"))
	for _i in range(3): await process_frame
	if tps.has_method("_enforce_tps_body_visibility"):
		tps.call("_enforce_tps_body_visibility")
	if not bool(tps.call("is_body_render_contract_satisfied")):
		push_error("ARCONT_CHARACTER_CAPTURE: TPS body hidden under SpringArm compression")
		quit(1)
		return
	await _save("player-near-camera.png")
	tps.process_mode = Node.PROCESS_MODE_INHERIT

	main.queue_free()
	await process_frame
	quit(0)

func _save(file_name: String) -> void:
	RenderingServer.force_draw(false)
	await process_frame
	var image := root.get_viewport().get_texture().get_image()
	if image == null or image.is_empty():
		push_error("ARCONT_CHARACTER_CAPTURE: empty image for %s" % file_name)
		quit(1)
		return
	var path := ProjectSettings.globalize_path(OUTPUT_DIR + "/" + file_name)
	var err := image.save_png(path)
	if err != OK:
		push_error("ARCONT_CHARACTER_CAPTURE: save failed for %s: %d" % [file_name, err])
		quit(1)
		return
	print("ARCONT_CHARACTER_CAPTURE|path=%s|width=%d|height=%d" % [path,image.get_width(),image.get_height()])
