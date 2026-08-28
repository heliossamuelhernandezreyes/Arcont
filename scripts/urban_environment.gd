extends Node3D
@export var district_size:=Vector2(170.0,220.0)
@export var road_width:=14.0
@export var sidewalk_height:=0.16
@export var building_visibility_range:=205.0
@export var vehicle_visibility_range:=110.0
@export var prop_visibility_range:=78.0
const CAR_MODELS:=["res://assets/provisional/city/car_hatchback.fbx","res://assets/provisional/city/car_police.fbx","res://assets/provisional/city/car_sedan.fbx","res://assets/provisional/city/car_stationwagon.fbx"]
const BUILDINGS:=["res://assets/provisional/city/building_A.fbx","res://assets/provisional/city/building_B.fbx","res://assets/provisional/city/building_C.fbx","res://assets/provisional/city/building_D.fbx"]
const PROP_MODELS:={"bench":"res://assets/provisional/city/bench.fbx","box_a":"res://assets/provisional/city/box_A.fbx","box_b":"res://assets/provisional/city/box_B.fbx","bush":"res://assets/provisional/city/bush.fbx"}
const CC0_STREET_CLUSTER:="res://assets/provisional/cc0_runtime/street_clutter/GLTF/LampPostTrachCanBench.gltf"
const CC0_FACTORY_BASE:="res://assets/provisional/cc0_runtime/factory/"
const CC0_CONE:=CC0_FACTORY_BASE+"cone.glb"
const CC0_BOX_SMALL:=CC0_FACTORY_BASE+"box-small.glb"
const METRIC_TARGETS:={"building":16.0,"vehicle":4.5,"bench":2.0,"box":1.0,"bush":1.5,"street_cluster":5.0,"cone":0.75,"factory_box":1.0}
var mat_asphalt:StandardMaterial3D;var mat_concrete:StandardMaterial3D;var mat_building:StandardMaterial3D;var mat_military:StandardMaterial3D;var mat_boundary:StandardMaterial3D
var mat_patch:StandardMaterial3D;var mat_grime:StandardMaterial3D;var mat_blood:StandardMaterial3D;var mat_warning:StandardMaterial3D;var mat_rubble:StandardMaterial3D;var mat_paper:StandardMaterial3D;var mat_dark_metal:StandardMaterial3D
var vehicle_index:=0
var performance_budget:Node
func _ready()->void:
 _make_materials();_build_ground();_build_city();_build_checkpoint();_build_vehicles();_build_props();_build_cc0_clutter();_build_surface_story();_build_debris();_build_hero_composition();_build_boundary();_build_points();_bind_performance_budget()
func _make_materials()->void:
 mat_asphalt=_mat(Color(0.075,0.082,0.095),0.94);mat_concrete=_mat(Color(0.31,0.32,0.34),0.93);mat_building=_mat(Color(0.27,0.29,0.33),0.84);mat_military=_mat(Color(0.17,0.22,0.15),0.86);mat_boundary=_mat(Color(0.17,0.20,0.24),0.88)
 mat_patch=_mat(Color(0.035,0.039,0.046),0.98);mat_grime=_mat(Color(0.085,0.075,0.065),0.98);mat_blood=_mat(Color(0.19,0.028,0.024),0.82);mat_warning=_mat(Color(0.82,0.47,0.055),0.76);mat_rubble=_mat(Color(0.22,0.225,0.23),0.97);mat_paper=_mat(Color(0.52,0.49,0.42),0.96);mat_dark_metal=_mat(Color(0.055,0.065,0.075),0.72)
func _mat(c:Color,r:float)->StandardMaterial3D:var m:=StandardMaterial3D.new();m.albedo_color=c;m.roughness=r;return m
func _build_ground()->void:
 _box("Ground",Vector3(0,-0.18,0),Vector3(district_size.x,0.35,district_size.y),mat_asphalt,true)
 for x in [-road_width*0.5-4.0,road_width*0.5+4.0]:_box("Sidewalk",Vector3(x,0.08,0),Vector3(7.5,0.16,district_size.y-6.0),mat_concrete,true)
 for x in [-18.6,18.6]:_box("Frontage",Vector3(x,0.045,0),Vector3(7.3,0.09,district_size.y-6.0),mat_concrete,true)
 for z in range(-100,101,12):_detail_box("LaneMark",Vector3(0,0.012,float(z)),Vector3(0.16,0.018,5.0),mat_concrete,90.0)
func _build_city()->void:
 var placements:=[[-24.0,-96.0,0],[-23.0,-76.0,2],[-22.0,-54.0,0],[-22.0,-34.0,1],[-23.0,-12.0,2],[-22.0,16.0,3],[-22.0,42.0,0],[-22.0,66.0,2],[-23.0,90.0,1],[24.0,-96.0,3],[22.0,-76.0,0],[22.0,-55.0,1],[23.0,-31.0,3],[22.0,-7.0,0],[22.0,20.0,2],[23.0,45.0,1],[22.0,68.0,3],[24.0,92.0,2]]
 for d in placements:
  var pos:=Vector3(float(d[0]),0.15,float(d[1]));var asset:=_spawn_asset(BUILDINGS[int(d[2])],pos,Vector3(0,90 if pos.x<0 else -90,0),building_visibility_range,"building",float(METRIC_TARGETS["building"]))
  _collision_box("BuildingCollision",pos+Vector3(0,4.5,0),Vector3(15.0,9.0,16.0))
  if asset:asset.position.y=0.15
func _build_checkpoint()->void:
 _box("Checkpoint",Vector3(0,0.55,5),Vector3(5.5,1.1,0.75),mat_military,true);_box("CheckpointL",Vector3(-4.5,0.55,7),Vector3(3.0,1.1,0.7),mat_military,true,Vector3(0,20,0));_box("CheckpointR",Vector3(4.5,0.55,3),Vector3(3.0,1.1,0.7),mat_military,true,Vector3(0,-20,0))
 for x in [-2.0,-1.0,0.0,1.0,2.0]:_detail_box("HazardBand",Vector3(float(x),1.115,5.0),Vector3(0.32,0.018,0.78),mat_warning,55.0,Vector3(0,0,18))
func _build_vehicles()->void:
 for data in [[Vector3(-3.0,0.18,-72),Vector3(0,12,0)],[Vector3(4.0,0.18,-44),Vector3(0,-8,0)],[Vector3(-3.0,0.18,-20),Vector3(0,12,0)],[Vector3(3.0,0.18,28),Vector3(0,-18,0)],[Vector3(-12.0,0.18,54),Vector3(0,82,0)],[Vector3(11.0,0.18,82),Vector3(0,96,0)]]:_vehicle(data[0],data[1])
func _vehicle(pos:Vector3,rot:Vector3)->void:
 _collision_box("VehicleCollision",pos+Vector3(0,0.65,0),Vector3(2.0,1.3,4.2),rot);_spawn_asset(CAR_MODELS[vehicle_index%CAR_MODELS.size()],pos,rot,vehicle_visibility_range,"vehicle",float(METRIC_TARGETS["vehicle"]));vehicle_index+=1
func _build_props()->void:
 for data in [[Vector3(-10.2,0.15,-83),78.0],[Vector3(10.0,0.15,-57),-92.0],[Vector3(-9.4,0.15,-7),103.0],[Vector3(9.8,0.15,20),-76.0],[Vector3(-10.4,0.15,49),95.0],[Vector3(9.1,0.15,77),-88.0]]:_spawn_asset(PROP_MODELS["bench"],data[0],Vector3(0,float(data[1]),0),prop_visibility_range,"prop",float(METRIC_TARGETS["bench"]))
 for data in [[Vector3(6.1,0.15,-69),14.0],[Vector3(-7.4,0.15,-35),-23.0],[Vector3(6.5,0.15,9),31.0],[Vector3(-7.2,0.15,30),-17.0],[Vector3(8.1,0.15,65),46.0]]:_spawn_asset(PROP_MODELS["box_a"],data[0],Vector3(0,float(data[1]),0),prop_visibility_range,"prop",float(METRIC_TARGETS["box"]))
func _build_cc0_clutter()->void:
 var clusters:=[Vector3(-10,0.15,-46),Vector3(10,0.15,35),Vector3(-10,0.15,70)]
 for i in range(clusters.size()):_spawn_asset(CC0_STREET_CLUSTER,clusters[i],Vector3(0,90.0*float(i%2),0),72.0,"prop",float(METRIC_TARGETS["street_cluster"]))
 for p in [Vector3(-5.7,0.15,3.0),Vector3(-4.9,0.15,4.2),Vector3(4.9,0.15,6.2),Vector3(5.8,0.15,7.0),Vector3(-6.2,0.15,-68.0),Vector3(5.9,0.15,29.0)]:_spawn_asset(CC0_CONE,p,Vector3.ZERO,52.0,"prop",float(METRIC_TARGETS["cone"]))
 for p in [Vector3(-8.0,0.15,-34),Vector3(7.8,0.15,12),Vector3(-8.2,0.15,60),Vector3(7.5,0.15,86)]:_spawn_asset(CC0_BOX_SMALL,p,Vector3(0,20,0),58.0,"prop",float(METRIC_TARGETS["factory_box"]))
func _build_surface_story()->void:
 var patches:=[ [Vector3(-2.8,0.014,-58),Vector3(3.8,0.018,7.0),-7.0], [Vector3(2.0,0.014,-15),Vector3(5.2,0.018,8.0),11.0], [Vector3(-1.5,0.014,43),Vector3(4.0,0.018,6.0),-14.0], [Vector3(2.8,0.014,78),Vector3(3.3,0.018,5.2),8.0] ]
 for d in patches:_detail_box("RoadPatch",d[0],d[1],mat_patch,72.0,Vector3(0,float(d[2]),0))
 var skid_lines:=[[-2.0,-31.0,-7.0],[-1.45,-31.5,-7.0],[1.8,17.0,9.0],[2.35,17.4,9.0]]
 for d in skid_lines:_detail_box("Skid",Vector3(float(d[0]),0.021,float(d[1])),Vector3(0.16,0.018,8.5),mat_grime,58.0,Vector3(0,float(d[2]),0))
 var blood_marks:=[ [Vector3(-1.1,0.027,-6.0),Vector3(0.9,0.018,1.9),22.0], [Vector3(3.3,0.027,32.0),Vector3(0.55,0.018,2.8),-18.0], [Vector3(-4.4,0.027,64.0),Vector3(1.1,0.018,1.4),41.0] ]
 for d in blood_marks:_detail_box("BloodMark",d[0],d[1],mat_blood,42.0,Vector3(0,float(d[2]),0))
func _build_debris()->void:
 var rubble:=[Vector3(-5.8,0.12,-14),Vector3(-6.4,0.09,-13.2),Vector3(-5.2,0.08,-12.8),Vector3(6.0,0.11,39),Vector3(6.6,0.08,39.7),Vector3(5.3,0.07,40.0),Vector3(-8.4,0.10,73),Vector3(-7.7,0.07,72.4)]
 for i in range(rubble.size()):
  var s:=Vector3(0.34+0.09*float(i%3),0.18+0.05*float(i%2),0.28+0.07*float((i+1)%3));_detail_box("Rubble",rubble[i],s,mat_rubble,48.0,Vector3(float(i*13%24),float(i*31%180),float(i*7%18)))
 var papers:=[Vector3(-3.7,0.028,-26),Vector3(-2.9,0.028,-25.1),Vector3(4.1,0.028,11.5),Vector3(3.5,0.028,12.3),Vector3(-4.8,0.028,52.0),Vector3(5.2,0.028,74.0),Vector3(4.5,0.028,75.0)]
 for i in range(papers.size()):_detail_box("Paper",papers[i],Vector3(0.34+0.05*float(i%2),0.012,0.24),mat_paper,38.0,Vector3(0,float((i*47)%180),0))
 for d in [[Vector3(-3.5,0.16,8.6),Vector3(0.16,0.14,1.4),33.0],[Vector3(4.0,0.12,0.2),Vector3(0.18,0.12,1.0),-26.0],[Vector3(-1.8,0.10,10.2),Vector3(0.12,0.10,0.8),68.0]]:_detail_box("MetalDebris",d[0],d[1],mat_dark_metal,48.0,Vector3(0,float(d[2]),12.0))
func _build_hero_composition()->void:
 _box("HeroBarrierL",Vector3(-5.4,0.42,-1.8),Vector3(2.4,0.84,0.55),mat_military,true,Vector3(0,31,0))
 _box("HeroBarrierR",Vector3(5.2,0.42,10.2),Vector3(2.7,0.84,0.55),mat_military,true,Vector3(0,-37,0))
 _detail_box("HeroWarningL",Vector3(-5.4,0.85,-1.8),Vector3(1.9,0.035,0.58),mat_warning,60.0,Vector3(0,31,0))
 _detail_box("HeroWarningR",Vector3(5.2,0.85,10.2),Vector3(2.1,0.035,0.58),mat_warning,60.0,Vector3(0,-37,0))
 var hero_rubble:=[Vector3(-6.4,0.08,1.0),Vector3(-5.9,0.10,1.6),Vector3(6.1,0.09,8.0),Vector3(5.7,0.07,8.7)]
 for i in range(hero_rubble.size()):_detail_box("HeroRubble",hero_rubble[i],Vector3(0.42,0.18,0.35),mat_rubble,55.0,Vector3(0,float(-31+i*23),0))
func _build_boundary()->void:
 var hx:=district_size.x*0.5;var hz:=district_size.y*0.5
 _collision_box("BoundaryN",Vector3(0,1.5,-hz),Vector3(district_size.x,3.0,0.6));_collision_box("BoundaryS",Vector3(0,1.5,hz),Vector3(district_size.x,3.0,0.6));_collision_box("BoundaryW",Vector3(-hx,1.5,0),Vector3(0.6,3.0,district_size.y));_collision_box("BoundaryE",Vector3(hx,1.5,0),Vector3(0.6,3.0,district_size.y))
func _build_points()->void:
 var points:=[Vector3(-5,0.2,-98),Vector3(5,0.2,-92),Vector3(-5,0.2,-68),Vector3(5,0.2,68),Vector3(-5,0.2,94),Vector3(5,0.2,100),Vector3(-62,0.2,0),Vector3(62,0.2,0),Vector3(-58,0.2,58),Vector3(58,0.2,-58),Vector3(-52,0.2,-72),Vector3(52,0.2,72)]
 for i in points.size():var marker:=Marker3D.new();marker.name="EnemySpawn%02d"%i;marker.position=points[i];marker.add_to_group("enemy_spawn");add_child(marker)
 var cover_points:Array[Vector3]=[]
 for i in range(-8,9):cover_points.append(Vector3(-5 if i%2==0 else 5,0.2,float(i)*11.0))
 cover_points.append_array([Vector3(-2.8,0.2,4.0),Vector3(2.8,0.2,6.0),Vector3(-5.4,0.2,8.2),Vector3(5.4,0.2,1.8),Vector3(-4.6,0.2,-72.0),Vector3(-1.4,0.2,-72.0),Vector3(2.4,0.2,-44.0),Vector3(5.7,0.2,-44.0),Vector3(-4.5,0.2,-20.0),Vector3(-1.3,0.2,-20.0),Vector3(1.4,0.2,28.0),Vector3(4.8,0.2,28.0),Vector3(-12.0,0.2,51.5),Vector3(-12.0,0.2,56.5),Vector3(11.0,0.2,79.5),Vector3(11.0,0.2,84.5),Vector3(-13.5,0.2,-54.0),Vector3(13.5,0.2,-55.0),Vector3(-13.5,0.2,42.0),Vector3(13.5,0.2,45.0),Vector3(-5.4,0.2,-1.8),Vector3(5.2,0.2,10.2)])
 for i in cover_points.size():_add_cover_marker(cover_points[i],i)
func _add_cover_marker(pos:Vector3,index:int)->void:
 var marker:=Marker3D.new();marker.name="TacticalCover%02d"%index;marker.position=pos;marker.add_to_group("tactical_cover");add_child(marker)
func _spawn_asset(path:String,pos:Vector3,rot:=Vector3.ZERO,visibility_end:=0.0,budget_class:="prop",target_extent_m:=0.0)->Node3D:
 var packed:=load(path) as PackedScene;if packed==null:return null
 var instance:=packed.instantiate() as Node3D;if instance==null:return null
 instance.position=pos;instance.rotation_degrees=rot;instance.scale=Vector3.ONE;instance.set_meta("budget_class",budget_class);instance.set_meta("base_visibility_end",visibility_end);instance.set_meta("asset_source",path);add_child(instance)
 if target_extent_m>0.0:AssetScaleNormalizer.normalize_longest_extent(instance,target_extent_m)
 if visibility_end>0.0:_apply_visibility_range(instance,visibility_end)
 return instance
func _detail_box(node_name:String,pos:Vector3,size:Vector3,material:Material,visibility_end:=48.0,rotation_deg:=Vector3.ZERO)->MeshInstance3D:
 var mi:=MeshInstance3D.new();mi.name=node_name;mi.position=pos;mi.rotation_degrees=rotation_deg;var mesh:=BoxMesh.new();mesh.size=size;mi.mesh=mesh;mi.material_override=material;mi.set_meta("art_layer",node_name);mi.set_meta("budget_class","prop");mi.set_meta("base_visibility_end",visibility_end);add_child(mi);_apply_visibility_range(mi,visibility_end);return mi
func _bind_performance_budget()->void:
 var scene:=get_tree().current_scene;if scene==null:return
 performance_budget=scene.get_node_or_null("PerformanceBudget")
 if performance_budget==null:return
 if performance_budget.has_signal("visual_budget_changed"):performance_budget.visual_budget_changed.connect(_on_visual_budget_changed)
 var visibility_scale:=1.0;var prop_scale:=1.0
 if performance_budget.has_method("get_visibility_scale"):visibility_scale=float(performance_budget.get_visibility_scale())
 if performance_budget.has_method("get_prop_scale"):prop_scale=float(performance_budget.get_prop_scale())
 _apply_runtime_visibility(visibility_scale,prop_scale)
func _on_visual_budget_changed(_tier:int,visibility_scale:float,prop_scale:float,_enemy_detail_scale:float)->void:_apply_runtime_visibility(visibility_scale,prop_scale)
func _apply_runtime_visibility(visibility_scale:float,prop_scale:=1.0)->void:
 for child in get_children():
  if not child.has_meta("base_visibility_end"):continue
  var base:=float(child.get_meta("base_visibility_end",0.0));if base<=0.0:continue
  var budget_class:=String(child.get_meta("budget_class","prop"));var class_scale:=prop_scale;var minimum:=18.0
  if budget_class=="building":class_scale=visibility_scale;minimum=80.0
  elif budget_class=="vehicle":class_scale=lerpf(visibility_scale,prop_scale,0.5);minimum=40.0
  _apply_visibility_range(child,maxf(minimum,base*class_scale))
func _apply_visibility_range(node:Node,end_distance:float)->void:
 if node is GeometryInstance3D:
  var geometry:=node as GeometryInstance3D;geometry.visibility_range_end=end_distance;geometry.visibility_range_end_margin=minf(10.0,end_distance*0.10);geometry.visibility_range_fade_mode=GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
 for child in node.get_children():_apply_visibility_range(child,end_distance)
func _collision_box(node_name:String,pos:Vector3,size:Vector3,rotation_deg:=Vector3.ZERO)->StaticBody3D:
 var body:=StaticBody3D.new();body.name=node_name;body.position=pos;body.rotation_degrees=rotation_deg;var cs:=CollisionShape3D.new();var sh:=BoxShape3D.new();sh.size=size;cs.shape=sh;body.add_child(cs);add_child(body);return body
func _box(node_name:String,pos:Vector3,size:Vector3,material:Material,collision_enabled:bool,rotation_deg:=Vector3.ZERO)->StaticBody3D:
 var body:=StaticBody3D.new();body.name=node_name;body.position=pos;body.rotation_degrees=rotation_deg;var mi:=MeshInstance3D.new();var mesh:=BoxMesh.new();mesh.size=size;mi.mesh=mesh;mi.material_override=material;body.add_child(mi)
 if collision_enabled:var cs:=CollisionShape3D.new();var sh:=BoxShape3D.new();sh.size=size;cs.shape=sh;body.add_child(cs)
 add_child(body);return body