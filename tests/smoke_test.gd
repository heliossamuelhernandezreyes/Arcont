extends SceneTree
func _init() -> void:
	var failures: Array[String] = []
	_check_scene("res://scenes/main.tscn",["PerformanceBudget","CombatFeedback","UrbanDistrict","MissionDirector","CompanionRobot","Player","Player/BodyVisual","Player/CoverProbe","Player/CameraRig/Camera3D/Weapon","Enemies","HUD/Objective"],failures)
	_check_scene("res://scenes/enemy.tscn",["Collision","Body","Head","ArmL","ArmR"],failures)
	_check_scene("res://scenes/companion_robot.tscn",["Collision","Body","Turret","StatusLight"],failures)
	_check_scene("res://scenes/ranged_enemy.tscn",["Collision","Body","Weapon","EyeLight"],failures)
	for method in ["_try_fire","apply_damage","_toggle_cover","_update_cover_state","_switch_shoulder","_update_camera_collision"]:_check_script_method("res://scripts/player.gd",method,failures)
	for method in ["try_fire","_fire_shotgun","_trace_pellet","request_reload","add_ammo"]:_check_script_method("res://scripts/weapon.gd",method,failures)
	for method in ["resistance_for","thickness_for","energy_after_surface","damage_scale"]:_check_script_method("res://scripts/ballistics.gd",method,failures)
	for method in ["_try_fire","_trace_round","_pick_hit_zone","apply_hit"]:_check_script_method("res://scripts/ranged_enemy.gd",method,failures)
	for method in ["activate_unit","_nearest_enemy","_fire_at","apply_damage"]:_check_script_method("res://scripts/companion_robot.gd",method,failures)
	for method in ["_update_generator","_update_defense","_request_ranged","_trigger_blackout","_spawn_brute_event","_trigger_xeno_pulse"]:_check_script_method("res://scripts/mission_director.gd",method,failures)
	for method in ["_start_next_wave","spawn_reinforcements","spawn_ranged_enemies","spawn_brute","_spawn_position_for"]:_check_script_method("res://scripts/main.gd",method,failures)
	if failures.is_empty():
		print("ARCONT CI: smoke test OK")
		quit(0)
		return
	for failure in failures:
		push_error("ARCONT CI: "+failure)
	quit(1)
func _check_scene(path:String,required_nodes:Array[String],failures:Array[String])->void:
	var packed:=load(path) as PackedScene
	if packed==null:failures.append("No se pudo cargar "+path);return
	var instance:=packed.instantiate()
	if instance==null:failures.append("No se pudo instanciar "+path);return
	for node_path in required_nodes:
		if instance.get_node_or_null(node_path)==null:failures.append(path+" no contiene nodo requerido: "+node_path)
	instance.free()
func _check_script_method(path:String,method_name:String,failures:Array[String])->void:
	var script:=load(path) as Script
	if script==null:failures.append("No se pudo cargar script "+path);return
	var found:=false
	for method in script.get_script_method_list():
		if String(method.get("name",""))==method_name:found=true;break
	if not found:failures.append(path+" no contiene método requerido: "+method_name)
