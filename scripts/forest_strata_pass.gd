extends Node3D

# ART-PASS-17: dense forest readability pass.
# Village reads as clearings cut into forest; authored road keeps a narrow combat corridor.

var terrain: Node
var rng := RandomNumberGenerator.new()
var trunk_mat: StandardMaterial3D
var canopy_mat: StandardMaterial3D
var canopy_alt_mat: StandardMaterial3D
var understory_mat: StandardMaterial3D
var ground_mat: StandardMaterial3D

func _ready() -> void:
 call_deferred("_build")

func _build() -> void:
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 if terrain == null or not terrain.has_method("get_height_at"):
  return
 rng.seed = 170829
 trunk_mat = _mat(Color(0.035,0.022,0.012),1.0)
 canopy_mat = _mat(Color(0.014,0.036,0.013),0.98)
 canopy_alt_mat = _mat(Color(0.025,0.052,0.019),0.99)
 understory_mat = _mat(Color(0.030,0.064,0.023),0.99)
 ground_mat = _mat(Color(0.034,0.046,0.019),1.0)
 _build_forest_cells()
 _build_street_walls()
 _build_ground_invasion()
 set_meta("art_status","ART-PASS-17-DENSE-FOREST")
 set_meta("forest_contract","CANOPY-SUBCANOPY-UNDERSTORY-GROUND-V3")
 set_meta("representation","spatial opaque forest cells with narrow authored clearing")
 set_meta("final_tree_asset",false)
 set_meta("visual_acceptance","PENDING_CAPTURE_REVIEW")
 set_meta("mobile_validation","PENDING")

func _build_forest_cells() -> void:
 var index := 0
 for z: int in range(-78,95,16):
  for x: int in range(-68,69,16):
   var c := Vector3(float(x),0,float(z))
   if _in_primary_clearance(c,10.0): continue
   _forest_cell(c,index)
   index += 1

func _forest_cell(center: Vector3,index: int) -> void:
 var root := Node3D.new(); root.name = "ForestCell_%02d" % index; root.set_meta("art_layer","forest_strata_cell"); add_child(root)
 var count := rng.randi_range(7,11)
 for i: int in range(count):
  var p := center + Vector3(rng.randf_range(-7.0,7.0),0,rng.randf_range(-7.0,7.0))
  if _in_primary_clearance(p,7.2): continue
  _tree(root,p,rng.randf_range(8.5,16.5),rng.randf_range(0.72,1.32),i)
  if i % 2 == 0: _understory_cluster(root,p,rng.randf_range(1.4,2.8),rng.randi_range(3,5))

func _build_street_walls() -> void:
 var index := 0
 for z: int in range(-58,73,9):
  var road_x: float = sin(float(z)*0.018)*2.5
  for side: float in [-1.0,1.0]:
   var root := Node3D.new(); root.name = "ForestEdge_%02d" % index; root.set_meta("art_layer","forest_street_edge"); add_child(root)
   var p := Vector3(road_x+side*rng.randf_range(8.0,11.8),0,float(z)+rng.randf_range(-2.8,2.8))
   _understory_cluster(root,p,rng.randf_range(1.8,3.1),rng.randi_range(5,8))
   if index % 3 != 1: _tree(root,p+Vector3(side*rng.randf_range(1.5,4.0),0,rng.randf_range(-3.0,3.0)),rng.randf_range(7.0,12.5),rng.randf_range(0.7,1.15),index)
   index += 1

func _tree(parent: Node3D,p: Vector3,height: float,width_scale: float,variant: int) -> void:
 var y := _height(p.x,p.z)
 var trunk := MeshInstance3D.new(); var tm := CylinderMesh.new(); tm.top_radius=0.13*width_scale; tm.bottom_radius=0.27*width_scale; tm.height=height*0.62; tm.radial_segments=6
 trunk.mesh=tm; trunk.material_override=trunk_mat; trunk.position=Vector3(p.x,y+height*0.31,p.z); trunk.rotation_degrees.z=rng.randf_range(-3.5,3.5); trunk.visibility_range_end=100.0; parent.add_child(trunk)
 var crown_count := 3 if variant % 3 == 0 else 2
 for j: int in range(crown_count):
  var crown := MeshInstance3D.new(); var mesh := SphereMesh.new(); mesh.radius=height*rng.randf_range(0.14,0.20)*width_scale; mesh.height=height*rng.randf_range(0.32,0.48); mesh.radial_segments=7; mesh.rings=4
  crown.mesh=mesh; crown.material_override=canopy_mat if (variant+j)%2==0 else canopy_alt_mat
  crown.position=Vector3(p.x+rng.randf_range(-height*0.12,height*0.12),y+height*rng.randf_range(0.64,0.82),p.z+rng.randf_range(-height*0.10,height*0.10)); crown.scale=Vector3(rng.randf_range(0.72,1.28),rng.randf_range(0.72,1.15),rng.randf_range(0.72,1.30)); crown.visibility_range_end=120.0 if j==0 else 95.0; parent.add_child(crown)

func _understory_cluster(parent: Node3D,p: Vector3,size: float,count: int) -> void:
 var y := _height(p.x,p.z)
 for j: int in range(count):
  var b := MeshInstance3D.new(); var mesh := SphereMesh.new(); mesh.radius=size*rng.randf_range(0.25,0.52); mesh.height=size*rng.randf_range(0.45,0.95); mesh.radial_segments=6; mesh.rings=3
  b.mesh=mesh; b.material_override=understory_mat; b.position=Vector3(p.x+rng.randf_range(-2.4,2.4),y+size*rng.randf_range(0.18,0.34),p.z+rng.randf_range(-2.4,2.4)); b.scale=Vector3(rng.randf_range(0.65,1.5),rng.randf_range(0.65,1.15),rng.randf_range(0.65,1.5)); b.visibility_range_end=68.0; parent.add_child(b)

func _build_ground_invasion() -> void:
 for z: int in range(-60,75,8):
  var road_x: float = sin(float(z)*0.018)*2.5
  for side: float in [-1.0,1.0]:
   var p := Vector3(road_x+side*rng.randf_range(7.2,10.5),0,float(z)+rng.randf_range(-2.0,2.0))
   var node := MeshInstance3D.new(); var mesh := CylinderMesh.new(); mesh.top_radius=rng.randf_range(2.4,4.6); mesh.bottom_radius=mesh.top_radius*rng.randf_range(0.92,1.12); mesh.height=0.032; mesh.radial_segments=rng.randi_range(7,11)
   node.mesh=mesh; node.material_override=ground_mat; node.position=Vector3(p.x,_height(p.x,p.z)+0.032,p.z); node.scale=Vector3(rng.randf_range(1.0,1.9),1,rng.randf_range(0.55,1.15)); node.rotation_degrees.y=rng.randf_range(0,180); node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; node.visibility_range_end=72.0; node.set_meta("art_layer","forest_ground_invasion"); add_child(node)

func _in_primary_clearance(p: Vector3,clearance: float) -> bool:
 if p.z < -62.0 or p.z > 76.0: return false
 return absf(p.x-sin(p.z*0.018)*2.5) < clearance

func _height(x: float,z: float) -> float:
 return float(terrain.call("get_height_at",x,z))

func _mat(color: Color,roughness: float) -> StandardMaterial3D:
 var m := StandardMaterial3D.new(); m.albedo_color=color; m.roughness=roughness; return m
