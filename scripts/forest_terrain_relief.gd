extends Node3D

# Authored low-frequency terrain relief for the forest perimeter. The village and
# mission spine stay readable/mostly level while ridges, berms and drainage banks
# create real traversable height variation and occlusion.
@export var seed := 84721
@export var ridge_count := 18
@export var berm_count := 16

var rng := RandomNumberGenerator.new()
var ground_material: StandardMaterial3D
var rock_material: StandardMaterial3D

func _ready() -> void:
 rng.seed = seed
 ground_material = _material(Color(0.095,0.135,0.055),0.98)
 rock_material = _material(Color(0.19,0.20,0.17),0.99)
 _build_outer_ridges()
 _build_trail_berms()
 _build_stream_banks()
 set_meta("art_layer","physical_forest_relief")
 set_meta("art_status","ART-PASS-3-RELIEF")
 set_meta("design_rule","clearings=cells trails=corridors ridges=walls")

func _material(color: Color, roughness: float) -> StandardMaterial3D:
 var m := StandardMaterial3D.new()
 m.albedo_color = color
 m.roughness = roughness
 return m

func _build_outer_ridges() -> void:
 var anchors := [
  Vector3(-66,0,-82),Vector3(-70,0,-55),Vector3(-72,0,-22),Vector3(-69,0,20),Vector3(-66,0,58),Vector3(-58,0,88),
  Vector3(66,0,-84),Vector3(71,0,-54),Vector3(72,0,-18),Vector3(69,0,22),Vector3(66,0,59),Vector3(58,0,88),
  Vector3(-43,0,99),Vector3(-18,0,103),Vector3(18,0,103),Vector3(43,0,99),Vector3(-44,0,-102),Vector3(44,0,-102)
 ]
 for i in range(mini(ridge_count,anchors.size())):
  var p:Vector3=anchors[i]
  _landform("ForestRidge",p,Vector3(rng.randf_range(12,21),rng.randf_range(2.2,4.8),rng.randf_range(9,17)),ground_material,true)

func _build_trail_berms() -> void:
 # Berms frame side approaches but deliberately avoid the village square and main road.
 for i in range(berm_count):
  var side := -1.0 if i%2==0 else 1.0
  var x := rng.randf_range(38.0,56.0)*side
  var z := rng.randf_range(-78.0,76.0)
  _landform("TrailBerm",Vector3(x,0,z),Vector3(rng.randf_range(5.5,10.0),rng.randf_range(0.8,1.9),rng.randf_range(4.5,8.0)),ground_material,i%3==0)

func _build_stream_banks() -> void:
 for x in [-46.0,-30.0,-15.0,15.0,30.0,46.0]:
  _landform("StreamBank",Vector3(x,0,-43.5),Vector3(8.5,1.05,3.0),rock_material,false)

func _landform(node_name:String,pos:Vector3,size:Vector3,material:Material,cover_grade:bool) -> void:
 var body:=StaticBody3D.new()
 body.name=node_name
 body.position=pos+Vector3(0,-size.y*0.42,0)
 body.rotation_degrees.y=rng.randf_range(-28.0,28.0)
 body.set_meta("terrain_relief",true)
 body.set_meta("cover_grade",cover_grade)
 var mesh_instance:=MeshInstance3D.new()
 var sphere:=SphereMesh.new()
 sphere.radius=1.0
 sphere.height=2.0
 sphere.radial_segments=16
 sphere.rings=8
 mesh_instance.mesh=sphere
 mesh_instance.scale=size
 mesh_instance.material_override=material
 mesh_instance.visibility_range_end=125.0
 mesh_instance.visibility_range_end_margin=10.0
 mesh_instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON if cover_grade else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 body.add_child(mesh_instance)
 var collision:=CollisionShape3D.new()
 var shape:=SphereShape3D.new()
 shape.radius=1.0
 collision.shape=shape
 collision.scale=size
 body.add_child(collision)
 add_child(body)
