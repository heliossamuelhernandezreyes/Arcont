extends SceneTree

func _init() -> void:
 var failures:Array[String]=[]
 _check_scene("res://scenes/main.tscn",[
  "PerformanceBudget","AwarenessDirector","NavigationGraph","CombatFeedback",
  "ForestVillage","ForestVillagePolish","MissionDirector","ThrowableController",
  "CompanionRobot","Player","Player/BodyVisual","Player/BodyVisual/OperatorModel",
  "Player/BodyVisual/WeaponMount","Player/BodyVisual/WeaponMount/Gun",
  "Player/BodyVisual/WeaponMount/MuzzleFlash","Player/CoverProbe",
  "Player/CameraRig/SpringArm3D","Player/CameraRig/SpringArm3D/Camera3D",
  "Player/Weapon","Player/Weapon/VisualAnimator","Player/ThirdPersonADS",
  "Player/TacticalMobility","Player/MeleeCombat","Enemies","HUD/Objective",
  "HUD/WeaponName","HUD/Throwable","HUD/MobileControls","MainMenu"
 ],failures)
 _check_absent("res://scenes/main.tscn",[
  "UrbanDistrict","Player/CameraRig/Camera3D","Player/CameraRig/SpringArm3D/Camera3D/Gun",
  "Player/CameraRig/SpringArm3D/Camera3D/Weapon","Player/CameraRig/SpringArm3D/Camera3D/MuzzleFlash"
 ],failures)

 for scene_data in [
  ["res://scenes/enemy.tscn",["Collision","Body","Head","ArmL","ArmR","MeleeAttack"]],
  ["res://scenes/companion_robot.tscn",["Collision","Body","Turret","StatusLight"]],
  ["res://scenes/ranged_enemy.tscn",["Collision","Body","Weapon","EyeLight","NavigationAgent3D"]],
  ["res://scenes/xeno_lancer.tscn",["Collision","Body","Weapon","CoreLight","NavigationAgent3D"]],
  ["res://scenes/xeno_stalker.tscn",["Collision","Body","Head","ArmL","ArmR","CoreLight"]]
 ]:
  _check_scene(scene_data[0],scene_data[1],failures)

 _check_methods("res://scripts/player.gd",["_try_fire","apply_damage","apply_suppression","request_crouch","request_dodge","add_mobile_look","set_mobile_move","request_reload","cycle_camera_mode","camera_mode_name","_update_body_orientation","_apply_look"],failures)
 _check_methods("res://scripts/melee_combat_controller.gd",["begin_guard","update_guard_drag","release_attack","quick_execute","receive_melee_attack","open_execution","_execute_target","is_guarding","current_guard"],failures)
 _check_methods("res://scripts/enemy.gd",["receive_melee_attack","force_knockdown","melee_execute","apply_hit","_sever_limb","_enter_crawl","_spawn_physics_parts","set_performance_profile"],failures)
 _check_methods("res://scripts/weapon.gd",["set_trigger","set_ads","cycle_weapon","switch_weapon","try_fire","_fire_weapon","_trace_round","request_reload","active_reload_tap","add_ammo","_build_weapon_visual"],failures)
 _check_methods("res://scripts/weapon_visual_animator.gd",["_bind_visual","_capture_detail_bases","_on_shot","_on_reload_state","_animate_m90","_animate_m90_reload","_ensure_round_visual"],failures)
 _check_methods("res://scripts/third_person_ads.gd",["_camera_target","is_aiming"],failures)
 _check_methods("res://scripts/tactical_mobility.gd",["toggle_crouch","request_slide","try_contextual_jump","try_vault","try_mantle","request_dodge","movement_speed_multiplier","blocks_normal_movement"],failures)
 _check_methods("res://scripts/awareness_director.gd",["report_sound","sustain_lure","recent_sound_for","report_contact","shared_intel_for"],failures)
 _check_methods("res://scripts/throwable_controller.gd",["cycle_throwable","throw_selected","mobile_throw","mobile_cycle","_bind_hud","_update_hud"],failures)
 _check_methods("res://scripts/navigation_graph.gd",["_build_graph","_segment_walkable","build_route","next_waypoint"],failures)
 _check_methods("res://scripts/tactical_ai.gd",["has_line_of_sight","point_has_cover","cover_exposure_score","best_cover","best_cover_near","flank_point","squad_role"],failures)
 _check_methods("res://scripts/companion_robot.gd",["activate_unit","set_command","cycle_command","apply_emp","_update_follow","_nearest_enemy","_fire_at","apply_damage"],failures)
 _check_methods("res://scripts/mission_director.gd",["_update_generator","_update_defense","_trigger_defense_events","_request_reinforcements","_request_ranged","_request_xeno","_request_stalker","_collect_supplies","_complete_mission","_objective_distance"],failures)
 _check_methods("res://scripts/main.gd",["_start_next_wave","spawn_reinforcements","spawn_ranged_enemies","spawn_xeno_lancers","spawn_xeno_stalkers","spawn_brute","_spawn_position_for","_apply_enemy_visual_budget","_on_weapon_changed"],failures)
 _check_methods("res://scripts/performance_budget.gd",["get_animation_quality","get_animation_update_interval","get_visibility_scale","get_prop_scale","get_enemy_detail_scale","_apply_tier"],failures)
 _check_methods("res://scripts/provisional_character_visual.gd",["_update_procedural","_update_locomotion_input","_update_tactical_pose","get_ads_weight","_setup_animation_tree","_configure_ads_filter","_bind_weapon_to_hand","_find_skeleton"],failures)
 _check_methods("res://scripts/forest_village_environment.gd",["_ground_and_paths","_village","_tactical_routes","_forest_mass","_forest_detail","_story_props","_boundaries","_spawn_points","_spawn_asset","_bind_budget"],failures)
 _check_methods("res://scripts/forest_village_polish.gd",["_macro_composition","_entrance_identities","_village_depth","_mission_landmarks","_forest_frames","_storytelling_pass","_lighting_pass","_bind_budget","_apply_budget"],failures)

 _check_text("res://scripts/weapon.gd","CameraRig/SpringArm3D/Camera3D",failures)
 _check_text("res://scripts/mobile_controls.gd","get_viewport().set_input_as_handled()",failures)
 _check_text("res://project.godot","pointing/emulate_mouse_from_touch=false",failures)
 _check_text("res://project.godot","pointing/emulate_touch_from_mouse=false",failures)
 _check_text("res://scripts/third_person_ads.gd","spring_arm.add_excluded_object(player.get_rid())",failures)
 _check_text("res://scripts/provisional_character_visual.gd","AnimationNodeStateMachine.new()",failures)
 _check_text("res://scripts/provisional_character_visual.gd","parameters/ads_layer/blend_amount",failures)
 _check_text("res://scripts/performance_budget.gd","signal visual_budget_changed",failures)
 _check_text("res://scripts/main.gd","budget.visual_budget_changed.connect(_on_visual_budget_changed)",failures)
 _check_text("res://scripts/forest_village_environment.gd","@export var world_size := Vector2(170.0, 220.0)",failures)
 _check_text("res://scripts/forest_village_environment.gd","tree_blocks.fbx",failures)
 _check_text("res://scripts/forest_village_environment.gd","bridge_center_stone.fbx",failures)
 _check_text("res://scripts/forest_village_environment.gd","ForestChunk_",failures)
 _check_text("res://scripts/forest_village_polish.gd","ART-PASS-2-POLISHED",failures)
 _check_text("res://scripts/forest_village_polish.gd","macro>meso>micro",failures)

 if failures.is_empty():
  print("ARCONT CI: forest village smoke test OK")
  quit(0)
  return
 for failure in failures:
  push_error("ARCONT CI: "+failure)
 quit(1)

func _check_scene(path:String,required_nodes:Array,failures:Array[String])->void:
 var packed:=load(path) as PackedScene
 if packed==null:
  failures.append("No se pudo cargar "+path)
  return
 var instance:=packed.instantiate()
 if instance==null:
  failures.append("No se pudo instanciar "+path)
  return
 for node_path in required_nodes:
  if instance.get_node_or_null(String(node_path))==null:
   failures.append(path+" no contiene nodo requerido: "+String(node_path))
 instance.free()

func _check_absent(path:String,forbidden_nodes:Array,failures:Array[String])->void:
 var packed:=load(path) as PackedScene
 if packed==null:return
 var instance:=packed.instantiate()
 for node_path in forbidden_nodes:
  if instance.get_node_or_null(String(node_path))!=null:
   failures.append(path+" conserva nodo prohibido: "+String(node_path))
 instance.free()

func _check_methods(path:String,methods:Array,failures:Array[String])->void:
 for method_name in methods:
  _check_script_method(path,String(method_name),failures)

func _check_script_method(path:String,method_name:String,failures:Array[String])->void:
 var script:=load(path) as Script
 if script==null:
  failures.append("No se pudo cargar script "+path)
  return
 var found:=false
 for method in script.get_script_method_list():
  if String(method.get("name",""))==method_name:
   found=true
   break
 if not found:
  failures.append(path+" no contiene método requerido: "+method_name)

func _check_text(path:String,needle:String,failures:Array[String])->void:
 var file:=FileAccess.open(path,FileAccess.READ)
 if file==null:
  failures.append("No se pudo leer "+path)
  return
 var text:=file.get_as_text()
 if text.find(needle)<0:
  failures.append(path+" no contiene contrato requerido: "+needle)
