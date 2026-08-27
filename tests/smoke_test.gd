extends SceneTree

func _init() -> void:
	var failures: Array[String] = []
	_check_scene("res://scenes/main.tscn", ["PerformanceBudget", "CombatFeedback", "UrbanDistrict", "MissionDirector", "CompanionRobot", "Player", "Player/Head/Camera3D/Weapon", "Player/Head/Camera3D/MuzzleFlash", "Enemies", "HUD/Wave", "HUD/Alive", "HUD/Health", "HUD/Ammo", "HUD/Reload", "HUD/HitMarker", "HUD/Objective", "HUD/MobileControls"], failures)
	_check_scene("res://scenes/enemy.tscn", ["Collision", "Body", "Head", "ArmL", "ArmR"], failures)
	_check_scene("res://scenes/companion_robot.tscn", ["Collision", "Body", "Turret", "StatusLight"], failures)
	_check_script_method("res://scripts/player.gd", "_try_fire", failures)
	_check_script_method("res://scripts/player.gd", "apply_damage", failures)
	_check_script_method("res://scripts/player.gd", "request_reload", failures)
	_check_script_method("res://scripts/player.gd", "set_mobile_move", failures)
	_check_script_method("res://scripts/player.gd", "add_mobile_look", failures)
	_check_script_method("res://scripts/player.gd", "set_mobile_fire", failures)
	_check_script_method("res://scripts/player.gd", "request_mobile_jump", failures)
	_check_script_method("res://scripts/player.gd", "set_mobile_sprint", failures)
	_check_script_method("res://scripts/weapon.gd", "try_fire", failures)
	_check_script_method("res://scripts/weapon.gd", "request_reload", failures)
	_check_script_method("res://scripts/weapon.gd", "add_ammo", failures)
	_check_script_method("res://scripts/weapon.gd", "_fire_shotgun", failures)
	_check_script_method("res://scripts/combat_feedback.gd", "on_shot_fired", failures)
	_check_script_method("res://scripts/combat_feedback.gd", "on_hit_feedback", failures)
	_check_script_method("res://scripts/combat_feedback.gd", "_play_placeholder_shot", failures)
	_check_script_method("res://scripts/mobile_controls.gd", "_handle_touch", failures)
	_check_script_method("res://scripts/mobile_controls.gd", "_handle_drag", failures)
	_check_script_method("res://scripts/enemy.gd", "apply_hit", failures)
	_check_script_method("res://scripts/enemy.gd", "_apply_impact_reaction", failures)
	_check_script_method("res://scripts/enemy.gd", "_knock_down", failures)
	_check_script_method("res://scripts/enemy.gd", "_damage_limb", failures)
	_check_script_method("res://scripts/enemy.gd", "_sever_limb", failures)
	_check_script_method("res://scripts/enemy.gd", "_enter_crawl", failures)
	_check_script_method("res://scripts/enemy.gd", "_set_crawl_visual", failures)
	_check_script_method("res://scripts/enemy.gd", "_current_move_speed", failures)
	_check_script_method("res://scripts/enemy.gd", "activate", failures)
	_check_script_method("res://scripts/enemy.gd", "deactivate", failures)
	_check_script_method("res://scripts/enemy.gd", "set_performance_profile", failures)
	_check_script_method("res://scripts/companion_robot.gd", "activate_unit", failures)
	_check_script_method("res://scripts/companion_robot.gd", "_nearest_enemy", failures)
	_check_script_method("res://scripts/companion_robot.gd", "_fire_at", failures)
	_check_script_method("res://scripts/companion_robot.gd", "apply_damage", failures)
	_check_script_method("res://scripts/performance_budget.gd", "_apply_tier", failures)
	_check_script_method("res://scripts/urban_environment.gd", "_build_city_blocks", failures)
	_check_script_method("res://scripts/urban_environment.gd", "_build_alien_incursion", failures)
	_check_script_method("res://scripts/urban_environment.gd", "_build_spawn_points", failures)
	_check_script_method("res://scripts/mission_director.gd", "_update_generator", failures)
	_check_script_method("res://scripts/mission_director.gd", "_update_defense", failures)
	_check_script_method("res://scripts/mission_director.gd", "_trigger_blackout", failures)
	_check_script_method("res://scripts/mission_director.gd", "_spawn_brute_event", failures)
	_check_script_method("res://scripts/mission_director.gd", "_trigger_xeno_pulse", failures)
	_check_script_method("res://scripts/mission_director.gd", "_collect_supplies", failures)
	_check_script_method("res://scripts/mission_director.gd", "_complete_mission", failures)
	_check_script_method("res://scripts/main.gd", "_start_next_wave", failures)
	_check_script_method("res://scripts/main.gd", "spawn_reinforcements", failures)
	_check_script_method("res://scripts/main.gd", "spawn_brute", failures)
	_check_script_method("res://scripts/main.gd", "_collect_spawn_points", failures)
	_check_script_method("res://scripts/main.gd", "_spawn_position_for", failures)
	_check_script_method("res://scripts/main.gd", "_on_performance_profile_changed", failures)

	if failures.is_empty():
		print("ARCONT CI: smoke test OK")
		quit(0)
	else:
		for failure in failures:
			push_error("ARCONT CI: " + failure)
		quit(1)

func _check_scene(path: String, required_nodes: Array[String], failures: Array[String]) -> void:
	var packed := load(path) as PackedScene
	if packed == null:
		failures.append("No se pudo cargar " + path)
		return
	var instance := packed.instantiate()
	if instance == null:
		failures.append("No se pudo instanciar " + path)
		return
	for node_path in required_nodes:
		if instance.get_node_or_null(node_path) == null:
			failures.append(path + " no contiene nodo requerido: " + node_path)
	instance.free()

func _check_script_method(path: String, method_name: String, failures: Array[String]) -> void:
	var script := load(path) as Script
	if script == null:
		failures.append("No se pudo cargar script " + path)
		return
	var found := false
	for method in script.get_script_method_list():
		if String(method.get("name", "")) == method_name:
			found = true
			break
	if not found:
		failures.append(path + " no contiene método requerido: " + method_name)
