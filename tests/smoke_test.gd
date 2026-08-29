extends SceneTree
func _init()->void:
 var failures:Array[String]=[]
 _check_scene("res://scenes/main.tscn",["ForestVillage","ForestVillagePolish","TerrainSurfacePass","ForestTerrainRelief","EnvironmentScatter","MissionDirector","Player","Player/CameraRig/SpringArm3D","Player/CameraRig/SpringArm3D/Camera3D","Enemies","HUD/MobileControls"],failures)
 _check_scene("res://scenes/enemy.tscn",["Collision","Body","Head","ArmL","ArmR","MeleeAttack"],failures)
 _check_methods("res://scripts/forest_terrain_relief.gd",["_build_height_field","_build_render_mesh","_build_collision","get_height_at","get_slope_at"],failures)
 _check_methods("res://scripts/environment_scatter.gd",["_build_chunks","_make_cell","_placement_allowed","_in_authored_clearance","_add_authored_edge_dressing","_terrain_height","_terrain_slope"],failures)
 _check_methods("res://scripts/terrain_surface_pass.gd",["_build_materials","_apply_existing_surface_materials","_add_ground_breakup","_add_mounds","_configure_sky"],failures)
 _check_methods("res://scripts/zombie_cc0_visual.gd",["_build_shell","_activate_segmented_fallback","get_source_asset","get_shell_extent"],failures)
 _check_methods("res://scripts/third_person_ads.gd",["_camera_target","_update_near_camera_visibility","get_camera_distance"],failures)
 _check_text("res://scripts/forest_terrain_relief.gd","ART-PASS-4-HEIGHTMAP",failures)
 _check_text("res://scripts/forest_terrain_relief.gd","HeightMapShape3D",failures)
 _check_text("res://scripts/environment_scatter.gd","ART-PASS-5-FOREST-BIOMES",failures)
 _check_text("res://scripts/environment_scatter.gd","height+slope+biome+mission_clearance",failures)
 _check_text("res://scripts/environment_scatter.gd","dense edges + readable clearings + ridge silhouettes",failures)
 _check_text("res://scripts/environment_scatter.gd","TreeCell_",failures)
 _check_text("res://scripts/environment_scatter.gd","ShrubCell_",failures)
 _check_text("res://scripts/environment_scatter.gd","FallenLog_",failures)
 _check_text("res://scripts/environment_scatter.gd","MultiMeshInstance3D.new()",failures)
 _check_text("res://scripts/zombie_cc0_visual.gd","realistic_city_candidate/InfectedCityMan.fbx",failures)
 _check_text("res://scripts/zombie_cc0_visual.gd","CC0-HUMANOID-INFECTED",failures)
 _check_text("res://scenes/main.tscn","ForestTerrainRelief",failures)
 _check_text("res://scenes/main.tscn","EnvironmentScatter",failures)
 _check_text("res://scripts/third_person_ads.gd","spring_arm.add_excluded_object(player.get_rid())",failures)
 if failures.is_empty():
  print("ARCONT CI: heightmap + forest biomes + edge dressing + humanoid infected + TPS OK");quit(0);return
 for failure in failures:push_error("ARCONT CI: "+failure)
 quit(1)
func _check_scene(path:String,required_nodes:Array,failures:Array[String])->void:
 var packed:=load(path) as PackedScene
 if packed==null:failures.append("No se pudo cargar "+path);return
 var instance:=packed.instantiate()
 if instance==null:failures.append("No se pudo instanciar "+path);return
 for node_path in required_nodes:
  if instance.get_node_or_null(String(node_path))==null:failures.append(path+" no contiene nodo requerido: "+String(node_path))
 instance.free()
func _check_methods(path:String,methods:Array,failures:Array[String])->void:
 for method_name in methods:_check_script_method(path,String(method_name),failures)
func _check_script_method(path:String,method_name:String,failures:Array[String])->void:
 var script:=load(path) as Script
 if script==null:failures.append("No se pudo cargar script "+path);return
 for method in script.get_script_method_list():
  if String(method.get("name",""))==method_name:return
 failures.append(path+" no contiene método requerido: "+method_name)
func _check_text(path:String,needle:String,failures:Array[String])->void:
 var file:=FileAccess.open(path,FileAccess.READ)
 if file==null:failures.append("No se pudo leer "+path);return
 if file.get_as_text().find(needle)<0:failures.append(path+" no contiene contrato requerido: "+needle)
