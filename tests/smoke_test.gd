extends SceneTree
func _init()->void:
 var failures:Array[String]=[]
 _check_scene("res://scenes/main.tscn",["PerformanceBudget","AwarenessDirector","NavigationGraph","CombatFeedback","UrbanDistrict","MissionDirector","ThrowableController","CompanionRobot","Player","Player/BodyVisual","Player/BodyVisual/OperatorModel","Player/BodyVisual/WeaponMount","Player/CameraRig/SpringArm3D","Player/CameraRig/SpringArm3D/Camera3D","Player/Weapon","Player/ThirdPersonADS","Player/TacticalMobility","Player/MeleeCombat","HUD/MobileControls","MainMenu"],failures)
 for method in ["_try_fire","apply_damage","apply_suppression","request_crouch","request_dodge","add_mobile_look","set_mobile_move","cycle_camera_mode","camera_distance_scale","_update_body_orientation","_apply_look"]:_check_script_method("res://scripts/player.gd",method,failures)
 for method in ["set_trigger","set_ads","switch_weapon","try_fire","request_reload","active_reload_tap","get_active_reload_state","_build_weapon_visual"]:_check_script_method("res://scripts/weapon.gd",method,failures)
 for method in ["has_line_of_sight","point_has_cover","cover_exposure_score","best_cover","best_cover_near","flank_point","squad_role"]:_check_script_method("res://scripts/tactical_ai.gd",method,failures)
 for method in ["_apply_skin_recursive","_update_procedural","_update_locomotion_input","_update_tactical_pose","get_locomotion_input","get_ads_weight","_setup_animation_player","_setup_animation_tree","_animation_node","_connect_state","_import_clip","_play_state","_bind_weapon_to_hand","_find_skeleton"]:_check_script_method("res://scripts/provisional_character_visual.gd",method,failures)
 for method in ["_build_ground","_build_city","_build_checkpoint","_build_vehicles","_build_props","_build_boundary","_build_points","_spawn_asset","_vehicle","_collision_box","_apply_visibility_range"]:_check_script_method("res://scripts/urban_environment.gd",method,failures)
 _check_text("res://project.godot","pointing/emulate_mouse_from_touch=false",failures);_check_text("res://scripts/third_person_ads.gd","spring_arm.add_excluded_object(player.get_rid())",failures)
 _check_text("res://scripts/provisional_character_visual.gd","BoneAttachment3D.new()",failures);_check_text("res://scripts/provisional_character_visual.gd","AnimationNodeStateMachine.new()",failures);_check_text("res://scripts/provisional_character_visual.gd","parameters/run/run_speed/scale",failures)
 _check_text("res://scripts/urban_environment.gd","district_size:=Vector2(170.0,220.0)",failures);_check_text("res://scripts/urban_environment.gd","building_A.fbx",failures);_check_text("res://scripts/urban_environment.gd","car_police.fbx",failures)
 if failures.is_empty():print("ARCONT CI: smoke test OK");quit(0);return
 for failure in failures:push_error("ARCONT CI: "+failure)
 quit(1)
func _check_scene(path:String,required_nodes:Array,failures:Array[String])->void:
 var packed:=load(path) as PackedScene;if packed==null:failures.append("No se pudo cargar "+path);return
 var instance:=packed.instantiate();if instance==null:failures.append("No se pudo instanciar "+path);return
 for node_path in required_nodes:
  if instance.get_node_or_null(String(node_path))==null:failures.append(path+" no contiene nodo requerido: "+String(node_path))
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
