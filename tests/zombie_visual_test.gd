extends SceneTree

const ENEMY := preload("res://scenes/enemy.tscn")

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var enemy := ENEMY.instantiate()
	root.add_child(enemy)
	await process_frame
	await process_frame
	await process_frame
	var visual := enemy.get_node_or_null("CC0Visual")
	if visual == null:
		_fail("CC0 zombie visual adapter missing")
		return
	if not bool(visual.call("is_shell_active")):
		_fail("CC0 zombie shell did not activate")
		return
	var source := String(visual.call("get_source_asset"))
	if source.is_empty() or not ResourceLoader.exists(source):
		_fail("CC0 zombie source missing")
		return
	var extent := float(visual.call("get_shell_extent"))
	# Imported humanoid rigs can be Z-up before the adapter's 180-degree facing
	# correction. Validate a human-scale shell instead of assuming the longest
	# imported AABB axis is the final standing Y height.
	if extent < 1.75 or extent > 2.05:
		_fail("CC0 humanoid infected extent %.3f outside human-scale envelope" % extent)
		return
	if "realistic_city_candidate/InfectedCityMan.fbx" not in source:
		_fail("humanoid infected candidate is not primary runtime shell: %s" % source)
		return
	var names: PackedStringArray = visual.call("get_animation_names")
	if names.is_empty():
		_fail("CC0 zombie imported without animation library")
		return
	# The realistic city shell currently ships its own base clip. Detailed
	# combat clips are promoted separately; the anatomical fallback remains the
	# gameplay truth for sever/crawl states.
	var body := enemy.get_node("Body") as Node3D
	var arm_l := enemy.get_node("ArmL") as Node3D
	var arm_r := enemy.get_node("ArmR") as Node3D
	if body.visible or arm_l.visible or arm_r.visible:
		_fail("segmented proxy visible while intact humanoid shell active")
		return
	enemy.call("_sever_limb", "arm_l", Vector3.FORWARD)
	await process_frame
	if bool(visual.call("is_shell_active")):
		_fail("humanoid zombie shell stayed active after limb sever")
		return
	if not body.visible:
		_fail("segmented fallback body not visible after sever")
		return
	if arm_l.visible:
		_fail("severed left arm became visible in fallback")
		return
	if not arm_r.visible:
		_fail("intact right arm missing in fallback")
		return
	print("HUMANOID INFECTED source=%s extent=%.3f animations=%s" % [source, extent, names])
	print("ARCONT HUMANOID INFECTED: primary realistic shell + anatomical fallback OK")
	enemy.queue_free()
	await process_frame
	quit(0)

func _fail(message: String) -> void:
	push_error(message)
	quit(1)
