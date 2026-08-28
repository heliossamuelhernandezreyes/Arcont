extends SceneTree
func _init()->void:
 var failures:Array[String]=[]
 _check_scene("res://scenes/main.tscn",["PerformanceBudget","AwarenessDirector","NavigationGraph","CombatFeedback","UrbanDistrict","MissionDirector","ThrowableController","CompanionRobot","Player","Player/BodyVisual","Player/BodyVisual/OperatorModel","Player/BodyVisual/WeaponMount","Player/BodyVisual/WeaponMount/Gun","Player/BodyVisual/WeaponMount/MuzzleFlash","Player/CoverProbe","Player/CameraRig/SpringArm3D","Player/CameraRig/SpringArm3D/Camera3D","Player/Weapon","Player/Weapon/VisualAnimator","Player/ThirdPersonADS","Player/TacticalMobility","Player/MeleeCombat","Enemies","HUD/Objective","HUD/WeaponName","HUD/Throwable","HUD/MobileControls","MainMenu"],failures)
 _check_absent("res://scenes/main.tscn",["Player/CameraRig/Camera3D","Player/CameraRig/SpringArm3D/Camera3D/Gun","Player/CameraRig/SpringArm3D/Camera3D/Weapon","Player/CameraRig/SpringArm3D/Camera3D/MuzzleFlash"],failures)
 for scene_data in [["res://scenes/enemy.tscn",["Collision","Body","Head","ArmL","ArmR","MeleeAttack"]],["res://scenes/companion_robot.tscn",["Collision","Body","Turret","StatusLight"]],["res://scenes/ranged_enemy.tscn",["Collision","Body","Weapon","EyeLight","NavigationAgent3D"]],["res://scenes/xeno_lancer.tscn",["Collision","Body","Weapon","CoreLight","NavigationAgent3D"]],["res://scenes/xeno_stalker.tscn",["Collision","Body","Head","ArmL","ArmR","CoreLight"]]]:_check_scene(scene_data[0],scene_data[1],failures)
 for method in ["_try_fire","apply_damage","apply_suppression","get_weapon_spread_multiplier","get_recoil_multiplier","get_reload_time_multiplier","request_crouch","request_dodge","_leg_injury_load","add_mobile_look","set_mobile_move","set_mobile_sprint","request_mobile_jump","request_reload","cycle_camera_mode","camera_mode_name","camera_distance_scale","set_mobile_look_sensitivity","_update_body_orientation","_apply_look"]:_check_script_method("res://scripts/player.gd",method,failures)
 for method in ["begin_guard","update_guard_drag","release_attack","quick_execute","receive_melee_attack","open_execution","_execute_target","_attack_line","is_guarding","current_guard"]:_check_script_method("res://scripts/melee_combat_controller.gd",method,failures)
 for method in ["receive_melee_attack","force_knockdown","melee_execute","apply_hit","_sever_limb","_enter_crawl","_spawn_physics_parts","set_performance_profile"]:_check_script_method("res://scripts/enemy.gd",method,failures)
 for method in ["set_trigger","set_ads","cycle_weapon","switch_weapon","try_fire","_report_weapon_sound","_fire_weapon","_trace_round","request_reload","active_reload_tap","_advance_missed_windows","get_active_reload_state","add_ammo","_player_controller","_build_weapon_visual"]:_check_script_method("res://scripts/weapon.gd",method,failures)
 for method in ["_bind_visual","_capture_detail_bases","_on_shot","_on_reload_state","_on_active_reload_feedback","_animate_m90","_animate_m90_reload","_apply_detail_offset","_restore_detail_bases","_ensure_round_visual"]:_check_script_method("res://scripts/weapon_visual_animator.gd",method,failures)
 for method in ["_camera_target","is_aiming"]:_check_script_method("res://scripts/third_person_ads.gd",method,failures)
 for method in ["toggle_crouch","request_crouch_or_slide","request_slide","try_contextual_jump","try_vault","try_mantle","request_dodge","_try_cover_transfer","record_vertical_speed","handle_landing","movement_speed_multiplier","apply_motion_override","blocks_normal_movement","blocks_jump","_update_traverse","_can_stand","_leg_load"]:_check_script_method("res://scripts/tactical_mobility.gd",method,failures)
 for method in ["report_sound","sustain_lure","_lure_infected","recent_sound_for","report_contact","shared_intel_for"]:_check_script_method("res://scripts/awareness_director.gd",method,failures)
 for method in ["configure","_trigger","_activate_decoy","_detonate_grenade","_detonate_emp","_apply_radial_damage","_apply_cover_blast"]:_check_script_method("res://scripts/throwable.gd",method,failures)
 for method in ["cycle_throwable","throw_selected","mobile_throw","mobile_cycle","_bind_hud","_update_hud"]:_check_script_method("res://scripts/throwable_controller.gd",method,failures)
 for method in ["_build_graph","_segment_walkable","build_route","next_waypoint"]:_check_script_method("res://scripts/navigation_graph.gd",method,failures)
 for method in ["resistance_for","energy_resistance_for","energy_after_surface","xeno_energy_after_surface","apply_surface_damage","apply_energy_surface_damage","damage_scale"]:_check_script_method("res://scripts/ballistics.gd",method,failures)
 for method in ["apply_ballistic_hit","apply_energy_hit","_update_visual_stage","_break_apart"]:_check_script_method("res://scripts/destructible_cover.gd",method,failures)
 for method in ["has_line_of_sight","_report_contact_throttled","point_has_cover","cover_exposure_score","best_cover","best_cover_near","flank_point","squad_role"]:_check_script_method("res://scripts/tactical_ai.gd",method,failures)
 for method in ["_update_awareness","_choose_tactic","_choose_anchor_tactic","_movement_velocity","_velocity_to","_next_navigation_point","_try_fire","_trace_round","_apply_near_miss_suppression","apply_hit"]:_check_script_method("res://scripts/ranged_enemy.gd",method,failures)
 for method in ["apply_emp","_update_awareness","_choose_tactic","_movement_velocity","_velocity_to","_next_navigation_point","_begin_charge","_fire_lance","_trace_energy","_apply_energy_suppression","_spawn_lance_visual","apply_hit"]:_check_script_method("res://scripts/xeno_lancer.gd",method,failures)
 for method in ["_configure_personality","_begin_engagement","_choose_sequence","_begin_sequence","_commit_feint","_begin_combo_strike","_update_sidestep","_telegraph_pose","_resolve_attack","receive_melee_attack","melee_execute","apply_hit","apply_emp"]:_check_script_method("res://scripts/xeno_stalker.gd",method,failures)
 for method in ["_build_ground","_build_city","_build_checkpoint","_build_vehicles","_build_props","_build_boundary","_build_points","_spawn_asset","_vehicle","_collision_box","_apply_visibility_range","_bind_performance_budget","_on_visual_budget_changed","_apply_runtime_visibility"]:_check_script_method("res://scripts/urban_environment.gd",method,failures)
 for method in ["activate_unit","set_command","cycle_command","apply_emp","_update_follow","_nearest_enemy","_fire_at","apply_damage"]:_check_script_method("res://scripts/companion_robot.gd",method,failures)
 for method in ["_ads_center","_weapon_center","_crouch_center","_dodge_center","_melee_center","_melee_label","_command_center","_throw_center","_camera_center","_menu_center","_claim_touch","_action_at","_handle_drag","_release_touch","_bind_weapon_feedback","_draw_active_reload","_on_active_reload_feedback"]:_check_script_method("res://scripts/mobile_controls.gd",method,failures)
 for method in ["_update_generator","_update_defense","_trigger_defense_events","_spawn_brute_event","_request_reinforcements","_request_ranged","_request_xeno","_request_stalker","_collect_supplies","_complete_mission","_objective_world_position","_objective_distance"]:_check_script_method("res://scripts/mission_director.gd",method,failures)
 for method in ["_start_next_wave","spawn_reinforcements","spawn_ranged_enemies","spawn_xeno_lancers","spawn_xeno_stalkers","spawn_brute","_spawn_position_for","_on_weapon_changed"]:_check_script_method("res://scripts/main.gd",method,failures)
 for method in ["get_animation_quality","get_animation_update_interval","get_visibility_scale","get_prop_scale","get_enemy_detail_scale","_apply_tier"]:_check_script_method("res://scripts/performance_budget.gd",method,failures)
 for method in ["_apply_skin_recursive","_update_procedural","_update_locomotion_input","_update_tactical_pose","get_locomotion_input","get_ads_weight","_quality_interval","_setup_animation_player","_setup_animation_tree","_configure_ads_filter","_animation_node","_connect_state","_import_clip","_play_state","_bind_weapon_to_hand","_find_skeleton"]:_check_script_method("res://scripts/provisional_character_visual.gd",method,failures)
 for method in ["show_pause","toggle_pause","_sensitivity_changed"]:_check_script_method("res://scripts/main_menu.gd",method,failures)
 _check_text("res://scripts/weapon.gd","CameraRig/SpringArm3D/Camera3D",failures);_check_text("res://scripts/weapon.gd","if DisplayServer.is_touchscreen_available():return",failures)
 _check_text("res://scripts/mobile_controls.gd","get_viewport().set_input_as_handled()",failures);_check_text("res://scripts/mobile_controls.gd","\"camera\":if player.has_method(\"cycle_camera_mode\")",failures);_check_text("res://scripts/mobile_controls.gd","\"menu\":if menu and menu.has_method(\"toggle_pause\")",failures)
 _check_text("res://project.godot","pointing/emulate_mouse_from_touch=false",failures);_check_text("res://project.godot","pointing/emulate_touch_from_mouse=false",failures);_check_text("res://project.godot","buffering/agile_event_flushing=true",failures)
 _check_text("res://scripts/urban_environment.gd","district_size:=Vector2(170.0,220.0)",failures);_check_text("res://scripts/urban_environment.gd","building_A.fbx",failures);_check_text("res://scripts/urban_environment.gd","car_police.fbx",failures);_check_text("res://scripts/urban_environment.gd","VISIBILITY_RANGE_FADE_DISABLED",failures)
 _check_text("res://scripts/third_person_ads.gd","spring_arm.add_excluded_object(player.get_rid())",failures)
 _check_text("res://scripts/provisional_character_visual.gd","BoneAttachment3D.new()",failures);_check_text("res://scripts/provisional_character_visual.gd","AnimationNodeStateMachine.new()",failures);_check_text("res://scripts/provisional_character_visual.gd","parameters/locomotion/run/run_speed/scale",failures);_check_text("res://scripts/provisional_character_visual.gd","parameters/ads_layer/blend_amount",failures);_check_text("res://scripts/provisional_character_visual.gd","Root|0_Targeting Pose",failures);_check_text("res://scripts/provisional_character_visual.gd","filter_enabled=true",failures)
 _check_text("res://scripts/performance_budget.gd","signal visual_budget_changed",failures)
 if failures.is_empty():print("ARCONT CI: smoke test OK");quit(0);return
 for failure in failures:push_error("ARCONT CI: "+failure)
 quit(1)
func _check_scene(path:String,required_nodes:Array,failures:Array[String])->void:
 var packed:=load(path) as PackedScene;if packed==null:failures.append("No se pudo cargar "+path);return
 var instance:=packed.instantiate();if instance==null:failures.append("No se pudo instanciar "+path);return
 for node_path in required_nodes:
  if instance.get_node_or_null(String(node_path))==null:failures.append(path+" no contiene nodo requerido: "+String(node_path))
 instance.free()
func _check_absent(path:String,forbidden_nodes:Array,failures:Array[String])->void:
 var packed:=load(path) as PackedScene;if packed==null:return
 var instance:=packed.instantiate()
 for node_path in forbidden_nodes:
  if instance.get_node_or_null(String(node_path))!=null:failures.append(path+" conserva nodo FPS prohibido: "+String(node_path))
 instance.free()
func _check_script_method(path:String,method_name:String,failures:Array[String])->void:
 var script:=load(path) as Script;if script==null:failures.append("No se pudo cargar script "+path);return
 var found:=false
 for method in script.get_script_method_list():
  if String(method.get("name",""))==method_name:found=true;break
 if not found:failures.append(path+" no contiene método requerido: "+method_name)
func _check_text(path:String,needle:String,failures:Array[String])->void:
 var file:=FileAccess.open(path,FileAccess.READ);if file==null:failures.append("No se pudo leer "+path);return
 var text:=file.get_as_text();if text.find(needle)<0:failures.append(path+" no contiene contrato requerido: "+needle)
