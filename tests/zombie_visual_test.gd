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
	if absf(extent - 1.90) > 0.05:
		_fail("CC0 zombie metric extent %.3f target 1.900" % extent)
		return
	var names: PackedStringArray = visual.call("get_animation_names")
	if names.is_empty():
		_fail("CC0 zombie imported without animation library")
		return
	visual.call("_on_staggered", enemy, 0.25)
	await process_frame
	if "recievehit" not in String(visual.call("get_current_animation")).to_lower():
		_fail("hit reaction animation not mapped: %s" % String(visual.call("get_current_animation")))
		return
	visual.set("action_lock", 0.0)
	visual.call("_on_knocked_down", enemy, 0.60)
	await process_frame
	var down_anim := String(visual.call("get_current_animation")).to_lower()
	if "sitdown" not in down_anim and "defeat" not in down_anim:
		_fail("knockdown animation not mapped: %s" % down_anim)
		return
	visual.set("action_lock", 0.0)
	visual.call("_play_best", ["punch"], false, true)
	await process_frame
	if "punch" not in String(visual.call("get_current_animation")).to_lower():
		_fail("punch animation not mapped")
		return
	var body := enemy.get_node("Body") as Node3D
	var arm_l := enemy.get_node("ArmL") as Node3D
	var arm_r := enemy.get_node("ArmR") as Node3D
	if body.visible or arm_l.visible or arm_r.visible:
		_fail("segmented proxy visible while intact shell active")
		return
	enemy.call("_sever_limb", "arm_l", Vector3.FORWARD)
	await process_frame
	if bool(visual.call("is_shell_active")):
		_fail("CC0 zombie shell stayed active after limb sever")
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
	print("CC0 ZOMBIE source=%s extent=%.3f animations=%s" % [source, extent, names])
	print("ARCONT CC0 ZOMBIE: combat animations + intact shell + anatomical fallback OK")
	enemy.queue_free()
	await process_frame
	quit(0)

func _fail(message: String) -> void:
	push_error(message)
	quit(1)
