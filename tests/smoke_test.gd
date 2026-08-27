extends SceneTree

func _init() -> void:
	var failures: Array[String] = []
	_check_scene("res://scenes/main.tscn", ["Player", "Player/Head/Camera3D/Weapon", "Enemies", "HUD/Wave", "HUD/Alive", "HUD/Health", "HUD/Ammo", "HUD/Reload", "HUD/MobileControls"], failures)
	_check_scene("res://scenes/enemy.tscn", ["Collision", "Body", "Head"], failures)
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
	_check_script_method("res://scripts/mobile_controls.gd", "_handle_touch", failures)
	_check_script_method("res://scripts/mobile_controls.gd", "_handle_drag", failures)
	_check_script_method("res://scripts/enemy.gd", "apply_hit", failures)
	_check_script_method("res://scripts/main.gd", "_start_next_wave", failures)

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
