extends Node3D
@export var district_size:=Vector2(120.0,150.0)
@export var road_width:=14.0
@export var sidewalk_height:=0.16
const CAR_MODELS:=["res://assets/provisional/city/car_hatchback.fbx","res://assets/provisional/city/car_police.fbx","res://assets/provisional/city/car_sedan.fbx","res://assets/provisional/city/car_stationwagon.fbx"]
const BUILDINGS:=["res://assets/provisional/city/building_A.fbx","res://assets/provisional/city/building_B.fbx","res://assets/provisional/city/building_C.fbx","res://assets/provisional/city/building_D.fbx"]
const PROP_MODELS:={"bench":"res://assets/provisional/city/bench.fbx","box_a":"res://assets/provisional/city/box_A.fbx","box_b":"res://assets/provisional/city/box_B.fbx","bush":"res://assets/provisional/city/bush.fbx"}
var mat_asphalt:StandardMaterial3D;var mat_concrete:StandardMaterial3D;var mat_building:StandardMaterial3D;var mat_military:StandardMaterial3D;var mat_boundary:StandardMaterial3D;var vehicle_index:=0
func _ready()->void:_make_materials();_build_ground();_build_city();_build_checkpoint();_build_vehicles();_build_props();_build_boundary();_build_points()
func _make_materials()->void:
 mat_asphalt=_mat(Color(0.12,0.135,0.155),0.92);mat_concrete=_mat(Color(0.38,0.39,0.41),0.90);mat_building=_mat(Color(0.27,0.29,0.33),0.84);mat_military=_mat(Color(0.22,0.28,0.19),0.82);mat_boundary=_mat(Color(0.20,0.25,0.31),0.86)
func _mat(c:Color,r:float)->StandardMaterial3D:var m:=StandardMaterial3D.new();m.albedo_color=c;m.roughness=r;return m
func _build_ground()->void:
 _box("Ground",Vector3(0,-0.18,0),Vector3(district_size.x,0.35,district_size.y),mat_asphalt,true)
 for x in [-road_width*0.5-4.0,road_width*0.5+4.0]:_box("Sidewalk",Vector3(x,0.08,0),Vector3(7.5,0.16,district_size.y-6.0),mat_concrete,true)
 for z in range(-65,66,12):_box("LaneMark",Vector3(0,0.012,float(z)),Vector3(0.18,0.025,5.0),mat_concrete,false)
func _build_city()->void:
 var placements:=[[-22.0,-54.0,0],[-22.0,-34.0,1],[-23.0,-12.0,2],[-22.0,16.0,3],[-22.0,42.0,0],[-22.0,62.0,2],[22.0,-55.0,1],[23.0,-31.0,3],[22.0,-7.0,0],[22.0,20.0,2],[23.0,45.0,1],[22.0,64.0,3]]
 for d in placements:
  var pos:=Vector3(float(d[0]),0.15,float(d[1]));var asset:=_spawn_asset(BUILDINGS[int(d[2])],pos,Vector3(0,90 if pos.x<0 else -90,0),Vector3.ONE*1.35)
  _box("BuildingCollision",pos+Vector3(0,4.5,0),Vector3(15.0,9.0,16.0),mat_building,true)
  if asset:asset.position.y=0.15
func _build_checkpoint()->void:
 _box("Checkpoint",Vector3(0,0.55,5),Vector3(5.5,1.1,0.75),mat_military,true);_box("CheckpointL",Vector3(-4.5,0.55,7),Vector3(3.0,1.1,0.7),mat_military,true,Vector3(0,20,0));_box("CheckpointR",Vector3(4.5,0.55,3),Vector3(3.0,1.1,0.7),mat_military,true,Vector3(0,-20,0))
func _build_vehicles()->void:
 _vehicle(Vector3(-3.0,0.18,-20),Vector3(0,12,0));_vehicle(Vector3(3.0,0.18,28),Vector3(0,-18,0));_vehicle(Vector3(-12.0,0.18,45),Vector3(0,82,0));_vehicle(Vector3(11.0,0.18,-48),Vector3(0,96,0))
func _vehicle(pos:Vector3,rot:Vector3)->void:
 var body:=StaticBody3D.new();body.position=pos+Vector3(0,0.65,0);body.rotation_degrees=rot;var cs:=CollisionShape3D.new();var sh:=BoxShape3D.new();sh.size=Vector3(2.0,1.3,4.2);cs.shape=sh;body.add_child(cs);add_child(body);_spawn_asset(CAR_MODELS[vehicle_index%CAR_MODELS.size()],pos,rot,Vector3.ONE*1.15);vehicle_index+=1
func _build_props()->void:
 for p in [Vector3(-9,0.15,-5),Vector3(9,0.15,18),Vector3(-9,0.15,38),Vector3(9,0.15,-37)]:_spawn_asset(PROP_MODELS["bench"],p,Vector3(0,90,0),Vector3.ONE*1.15)
 for p in [Vector3(6,0.15,8),Vector3(-7,0.15,31),Vector3(8,0.15,-28)]:_spawn_asset(PROP_MODELS["box_a"],p,Vector3.ZERO,Vector3.ONE*1.2)
func _build_boundary()->void:
 var hx:=district_size.x*0.5;var hz:=district_size.y*0.5
 _box("BoundaryN",Vector3(0,1.5,-hz),Vector3(district_size.x,3.0,0.6),mat_boundary,true);_box("BoundaryS",Vector3(0,1.5,hz),Vector3(district_size.x,3.0,0.6),mat_boundary,true);_box("BoundaryW",Vector3(-hx,1.5,0),Vector3(0.6,3.0,district_size.y),mat_boundary,true);_box("BoundaryE",Vector3(hx,1.5,0),Vector3(0.6,3.0,district_size.y),mat_boundary,true)
func _build_points()->void:
 var points:=[Vector3(-5,0.2,-68),Vector3(5,0.2,-68),Vector3(-5,0.2,68),Vector3(5,0.2,68),Vector3(-48,0.2,0),Vector3(48,0.2,0),Vector3(-42,0.2,45),Vector3(42,0.2,-45),Vector3(-36,0.2,-50),Vector3(36,0.2,50)]
 for i in points.size():var marker:=Marker3D.new();marker.name="EnemySpawn%02d"%i;marker.position=points[i];marker.add_to_group("enemy_spawn");add_child(marker)
 for i in range(-5,6):var marker:=Marker3D.new();marker.name="TacticalCover%02d"%(i+5);marker.position=Vector3(-5 if i%2==0 else 5,0.2,float(i)*11.0);marker.add_to_group("tactical_cover");add_child(marker)
func _spawn_asset(path:String,pos:Vector3,rot:=Vector3.ZERO,scale_value:=Vector3.ONE)->Node3D:
 var packed:=load(path) as PackedScene;if packed==null:return null
 var instance:=packed.instantiate() as Node3D;if instance==null:return null
 instance.position=pos;instance.rotation_degrees=rot;instance.scale=scale_value;add_child(instance);return instance
func _box(node_name:String,pos:Vector3,size:Vector3,material:Material,collision_enabled:bool,rotation_deg:=Vector3.ZERO)->StaticBody3D:
 var body:=StaticBody3D.new();body.name=node_name;body.position=pos;body.rotation_degrees=rotation_deg;var mi:=MeshInstance3D.new();var mesh:=BoxMesh.new();mesh.size=size;mi.mesh=mesh;mi.material_override=material;body.add_child(mi)
 if collision_enabled:var cs:=CollisionShape3D.new();var sh:=BoxShape3D.new();sh.size=size;cs.shape=sh;body.add_child(cs)
 add_child(body);return body
