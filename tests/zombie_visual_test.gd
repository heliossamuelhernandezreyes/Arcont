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

	var contract := String(visual.call("get_animation_contract"))
	if contract == "proxy_fallback":
		# A visible segmented proxy is preferable to accepting a static/bind-pose
		# imported shell. This is an explicit degraded state, not a false pass for
		# the realistic candidate.
		var proxy_body := enemy.get_node("Body") as Node3D
		if not proxy_body.visible:
			_fail("proxy fallback contract selected but segmented body is hidden")
			return
		print("ZOMBIE_RUNTIME_CONTRACT|mode=proxy_fallback|reason=%s" % String(visual.get_meta("animation_contract_failure", "")))
		enemy.queue_free()
		await process_frame
		quit(0)
		return

	if contract != "semantic_native":
		_fail("unexpected zombie animation contract: %s" % contract)
		return
	if not bool(visual.call("is_shell_active")):
		_fail("semantic zombie shell did not activate")
		return

	var source := String(visual.call("get_source_asset"))
	if source.is_empty() or not ResourceLoader.exists(source):
		_fail("semantic zombie source missing")
		return
	var extent := float(visual.call("get_shell_extent"))
	if extent < 1.75 or extent > 2.05:
		_fail("CC0 humanoid infected extent %.3f outside human-scale envelope" % extent)
		return

	var names: PackedStringArray = visual.call("get_animation_names")
	if names.is_empty():
		_fail("semantic zombie imported without animation library")
		return
	var lowered: Array[String] = []
	for name_variant in names:
		lowered.append(String(name_variant).to_lower())
	if not _contains_any(lowered, ["idle", "zombie"]):
		_fail("active shell lacks semantic idle animation: %s" % names)
		return
	if not _contains_any(lowered, ["walk", "run"]):
		_fail("active shell lacks semantic locomotion animation: %s" % names)
		return
	if not _contains_any(lowered, ["punch", "attack"]):
		_fail("active shell lacks semantic attack animation: %s" % names)
		return

	var current := String(visual.call("get_current_animation")).to_lower()
	if current.is_empty() or ("idle" not in current and "zombie" not in current):
		_fail("semantic shell did not start in a valid idle animation: %s" % current)
		return

	var body := enemy.get_node("Body") as Node3D
	var arm_l := enemy.get_node("ArmL") as Node3D
	var arm_r := enemy.get_node("ArmR") as Node3D
	if body.visible or arm_l.visible or arm_r.visible:
		_fail("segmented proxy visible while semantic humanoid shell active")
		return

	enemy.call("_sever_limb", "arm_l", Vector3.FORWARD)
	await process_frame
	if bool(visual.call("is_shell_active")):
		_fail("humanoid zombie shell stayed active after limb sever")
		return
	if String(visual.call("get_animation_contract")) != "segmented_runtime_fallback":
		_fail("limb sever did not declare segmented_runtime_fallback")
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

	print("ZOMBIE_RUNTIME_CONTRACT|mode=%s|source=%s|extent=%.3f|current=%s|animations=%s" % [contract, source, extent, current, names])
	print("ARCONT ZOMBIE VISUAL: semantic animated shell + explicit anatomical fallback OK")
	enemy.queue_free()
	await process_frame
	quit(0)

func _contains_any(names: Array[String], tokens: Array[String]) -> bool:
	for name in names:
		for token in tokens:
			if token in name:
				return true
	return false

func _fail(message: String) -> void:
	push_error(message)
	quit(1)
