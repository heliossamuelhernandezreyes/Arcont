extends SceneTree

const MAIN := preload("res://scenes/main.tscn")

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var main := MAIN.instantiate()
	root.add_child(main)
	await process_frame
	await process_frame
	var district := main.get_node_or_null("UrbanDistrict")
	if district == null:
		_fail("UrbanDistrict missing")
		return
	var counts := {"RoadPatch":0,"Skid":0,"BloodMark":0,"Rubble":0,"HeroRubble":0,"Paper":0,"MetalDebris":0,"HazardBand":0,"HeroWarningL":0,"HeroWarningR":0}
	var budgeted_details := 0
	for child in district.get_children():
		if child.has_meta("art_layer"):
			var layer := String(child.get_meta("art_layer"))
			if counts.has(layer): counts[layer] = int(counts[layer]) + 1
		if child.has_meta("budget_class") and String(child.get_meta("budget_class")) == "prop" and child.has_meta("base_visibility_end"):
			budgeted_details += 1
	if int(counts["RoadPatch"]) < 4:
		_fail("hero street missing road patches: %s" % counts)
		return
	if int(counts["Skid"]) < 4 or int(counts["BloodMark"]) < 3:
		_fail("hero street missing surface storytelling: %s" % counts)
		return
	if int(counts["Rubble"]) + int(counts["HeroRubble"]) < 10:
		_fail("hero street rubble density too low: %s" % counts)
		return
	if int(counts["Paper"]) < 7 or int(counts["MetalDebris"]) < 3:
		_fail("hero street debris layers incomplete: %s" % counts)
		return
	if int(counts["HazardBand"]) < 5 or int(counts["HeroWarningL"]) != 1 or int(counts["HeroWarningR"]) != 1:
		_fail("checkpoint focal hierarchy missing: %s" % counts)
		return
	if budgeted_details < 45:
		_fail("too few mobile-budgeted street details: %d" % budgeted_details)
		return
	var env_node := main.get_node_or_null("WorldEnvironment") as WorldEnvironment
	if env_node == null or env_node.environment == null:
		_fail("WorldEnvironment missing")
		return
	if env_node.environment.ambient_light_energy > 1.0:
		_fail("ambient light became too flat: %.2f" % env_node.environment.ambient_light_energy)
		return
	var moon := main.get_node_or_null("MoonLight") as DirectionalLight3D
	var warm := main.get_node_or_null("EmergencyLight") as OmniLight3D
	var cool := main.get_node_or_null("EmergencyLightFar") as OmniLight3D
	if moon == null or warm == null or cool == null:
		_fail("hero lighting hierarchy incomplete")
		return
	if not moon.shadow_enabled:
		_fail("primary moon key must keep shadows")
		return
	if warm.shadow_enabled or cool.shadow_enabled:
		_fail("mobile accent lights must remain unshadowed")
		return
	print("HERO STREET ART counts=%s budgeted_details=%d ambient=%.2f" % [counts, budgeted_details, env_node.environment.ambient_light_energy])
	print("ARCONT HERO STREET: composition + damage layers + mobile lighting contract OK")
	main.queue_free()
	await process_frame
	quit(0)

func _fail(message: String) -> void:
	push_error(message)
	quit(1)
