extends Node3D

# ART-PASS-20: batched forest with less blob-like silhouettes and readable edge depth.
# The road remains a tactical clearing, but canopy and understory no longer form giant opaque balls.

var terrain: Node
var rng := RandomNumberGenerator.new()
var trunk_mat: StandardMaterial3D
var canopy_mat: StandardMaterial3D
var canopy_alt_mat: StandardMaterial3D
var understory_mat: StandardMaterial3D
var ground_mat: StandardMaterial3D
var trunk_mesh: CylinderMesh
var crown_mesh: SphereMesh
var bush_mesh: SphereMesh

func _ready() -> void:
 call_deferred("_build")

func _build() -> void:
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 if terrain == null or not terrain.has_method("get_height_at"):
  return
 rng.seed = 200829
 trunk_mat = _mat(Color(0.075,0.047,0.025),1.0)
 canopy_mat = _mat(Color(0.030,0.090,0.032),0.96)
 canopy_alt_mat = _mat(Color(0.055,0.125,0.045),0.97)
 understory_mat = _mat(Color(0.055,0.120,0.038),0.98)
 ground_mat = _mat(Color(0.060,0.078,0.030),1.0)
 trunk_mesh = CylinderMesh.new(); trunk_mesh.top_radius=0.13; trunk_mesh.bottom_radius=0.24; trunk_mesh.height=1.0; trunk_mesh.radial_segments=7
 crown_mesh = SphereMesh.new(); crown_mesh.radius=0.5; crown_mesh.height=1.0; crown_mesh.radial_segments=8; crown_mesh.rings=5
 bush_mesh = SphereMesh.new(); bush_mesh.radius=0.5; bush_mesh.height=1.0; bush_mesh.radial_segments=7; bush_mesh.rings=4
 _build_forest_cells()
 _build_street_edge_cells()
 _build_ground_invasion()
 set_meta("art_status","ART-PASS-20-READABLE-BATCHED-FOREST")
 set_meta("forest_contract","CANOPY-SUBCANOPY-UNDERSTORY-GROUND-V6")
 set_meta("representation","spatial MultiMesh forest cells with narrow tactical clearing and tapered canopy silhouettes")
 set_meta("final_tree_asset",false)
 set_meta("visual_acceptance","PENDING_CAPTURE_REVIEW")
 set_meta("mobile_validation","PENDING")

func _build_forest_cells() -> void:
 var index := 0
 for z: int in range(-84,101,16):
  for x: int in range(-72,73,16):
   var c := Vector3(float(x),0,float(z))
   if _in_primary_clearance(c,8.0):
    continue
   _forest_cell(c,index)
   index += 1

func _forest_cell(center: Vector3,index: int) -> void:
 var trunks: Array[Transform3D] = []
 var crowns_a: Array[Transform3D] = []
 var crowns_b: Array[Transform3D] = []
 var bushes: Array[Transform3D] = []
 for i: int in range(rng.randi_range(7,10)):
  var p := center + Vector3(rng.randf_range(-6.8,6.8),0,rng.randf_range(-6.8,6.8))
  if _in_primary_clearance(p,5.4):
   continue
  var y := _height(p.x,p.z)
  var h := rng.randf_range(9.0,18.0)
  var w := rng.randf_range(0.78,1.18)
  trunks.append(_xf(Vector3(p.x,y+h*0.31,p.z),Vector3(0.22*w,h*0.62,0.22*w),rng.randf_range(-3.0,3.0)))
  var crown_count := 2 if (i+index)%4 != 0 else 3
  for j: int in range(crown_count):
   var cp := Vector3(p.x+rng.randf_range(-h*0.08,h*0.08),y+h*rng.randf_range(0.68,0.84),p.z+rng.randf_range(-h*0.08,h*0.08))
   var cs := Vector3(h*rng.randf_range(0.17,0.25)*w,h*rng.randf_range(0.26,0.38),h*rng.randf_range(0.17,0.25)*w)
   if (i+j+index)%2 == 0:
    crowns_a.append(_xf(cp,cs,rng.randf_range(0,180)))
   else:
    crowns_b.append(_xf(cp,cs,rng.randf_range(0,180)))
  if i%2 == 0:
   for j: int in range(rng.randi_range(2,4)):
    var s := rng.randf_range(0.75,1.65)
    var bp := Vector3(p.x+rng.randf_range(-2.8,2.8),y+s*0.25,p.z+rng.randf_range(-2.8,2.8))
    bushes.append(_xf(bp,Vector3(s*rng.randf_range(0.70,1.15),s*rng.randf_range(0.38,0.68),s*rng.randf_range(0.70,1.15)),rng.randf_range(0,180)))
 var root := Node3D.new()
 root.name = "ForestCell_%02d" % index
 root.set_meta("art_layer","forest_strata_cell")
 add_child(root)
 _multimesh(root,"Trunks",trunk_mesh,trunk_mat,trunks,105.0)
 _multimesh(root,"CanopyA",crown_mesh,canopy_mat,crowns_a,125.0)
 _multimesh(root,"CanopyB",crown_mesh,canopy_alt_mat,crowns_b,110.0)
 _multimesh(root,"Understory",bush_mesh,understory_mat,bushes,62.0)

func _build_street_edge_cells() -> void:
 var index := 0
 for z: int in range(-64,79,12):
  for side: float in [-1.0,1.0]:
   var road_x := sin(float(z)*0.018)*2.5
   var bushes: Array[Transform3D] = []
   var crowns: Array[Transform3D] = []
   var trunks: Array[Transform3D] = []
   for j: int in range(8):
    var p := Vector3(road_x+side*rng.randf_range(5.8,8.8),0,float(z)+rng.randf_range(-5.0,5.0))
    var y := _height(p.x,p.z)
    var s := rng.randf_range(0.65,1.45)
    bushes.append(_xf(Vector3(p.x,y+s*0.24,p.z),Vector3(s*rng.randf_range(0.65,1.10),s*rng.randf_range(0.35,0.62),s*rng.randf_range(0.65,1.10)),rng.randf_range(0,180)))
    if j%4 == 0:
     var h := rng.randf_range(6.5,11.0)
     trunks.append(_xf(Vector3(p.x+side*0.8,y+h*0.31,p.z),Vector3(0.18,h*0.62,0.18),rng.randf_range(-3,3)))
     crowns.append(_xf(Vector3(p.x+side*0.8,y+h*0.75,p.z),Vector3(h*0.20,h*0.32,h*0.20),rng.randf_range(0,180)))
   var root := Node3D.new()
   root.name = "ForestEdgeCell_%02d" % index
   root.set_meta("art_layer","forest_street_edge")
   add_child(root)
   _multimesh(root,"EdgeBushes",bush_mesh,understory_mat,bushes,58.0)
   _multimesh(root,"EdgeTrunks",trunk_mesh,trunk_mat,trunks,90.0)
   _multimesh(root,"EdgeCrowns",crown_mesh,canopy_alt_mat,crowns,95.0)
   index += 1

func _build_ground_invasion() -> void:
 for z: int in range(-62,77,10):
  var road_x := sin(float(z)*0.018)*2.5
  for side: float in [-1.0,1.0]:
   var p := Vector3(road_x+side*rng.randf_range(5.8,7.6),0,float(z)+rng.randf_range(-2.0,2.0))
   var node := MeshInstance3D.new()
   var mesh := CylinderMesh.new()
   mesh.top_radius = rng.randf_range(0.85,1.60)
   mesh.bottom_radius = mesh.top_radius*rng.randf_range(0.94,1.06)
   mesh.height = 0.018
   mesh.radial_segments = rng.randi_range(7,9)
   node.mesh = mesh
   node.material_override = ground_mat
   node.position = Vector3(p.x,_height(p.x,p.z)+0.018,p.z)
   node.scale = Vector3(rng.randf_range(1.0,1.35),1,rng.randf_range(0.55,0.90))
   node.rotation_degrees.y = rng.randf_range(0,180)
   node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
   node.visibility_range_end = 52.0
   node.set_meta("art_layer","forest_ground_invasion")
   add_child(node)

func _multimesh(parent: Node3D,name_: String,mesh: Mesh,material: Material,transforms: Array[Transform3D],range_end: float) -> void:
 if transforms.is_empty():
  return
 var mm := MultiMesh.new()
 mm.transform_format = MultiMesh.TRANSFORM_3D
 mm.mesh = mesh
 mm.instance_count = transforms.size()
 for i: int in range(transforms.size()):
  mm.set_instance_transform(i,transforms[i])
 var node := MultiMeshInstance3D.new()
 node.name = name_
 node.multimesh = mm
 node.material_override = material
 node.visibility_range_end = range_end
 node.visibility_range_end_margin = 3.0
 parent.add_child(node)

func _xf(pos: Vector3,scale_: Vector3,yaw: float) -> Transform3D:
 var basis := Basis(Vector3.UP,deg_to_rad(yaw)).scaled(scale_)
 return Transform3D(basis,pos)

func _in_primary_clearance(p: Vector3,clearance: float) -> bool:
 if p.z < -66.0 or p.z > 80.0:
  return false
 return absf(p.x-sin(p.z*0.018)*2.5) < clearance

func _height(x: float,z: float) -> float:
 return float(terrain.call("get_height_at",x,z))

func _mat(color: Color,roughness: float) -> StandardMaterial3D:
 var m := StandardMaterial3D.new()
 m.albedo_color = color
 m.roughness = roughness
 return m
