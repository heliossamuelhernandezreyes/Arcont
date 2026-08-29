extends Node3D

# ART-PASS-14: forest strata for gameplay composition.
# Opaque procedural silhouettes intentionally replace node-heavy scatter for the
# mid/far forest. They are grouped in spatial cells so visibility can cull them.

var terrain: Node
var rng := RandomNumberGenerator.new()
var trunk_mat: StandardMaterial3D
var canopy_mat: StandardMaterial3D
var understory_mat: StandardMaterial3D
var ground_mat: StandardMaterial3D

func _ready() -> void:
 call_deferred("_build")

func _build() -> void:
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 if terrain == null or not terrain.has_method("get_height_at"):
  return
 rng.seed = 140829
 trunk_mat = _mat(Color(0.040,0.026,0.015),1.0)
 canopy_mat = _mat(Color(0.018,0.042,0.017),0.98)
 understory_mat = _mat(Color(0.027,0.058,0.021),0.99)
 ground_mat = _mat(Color(0.038,0.049,0.022),1.0)
 _build_forest_cells()
 _build_ground_invasion()
 set_meta("art_status","ART-PASS-14-LAYERED-FOREST")
 set_meta("forest_contract","CANOPY-SUBCANOPY-UNDERSTORY-GROUND-V1")
 set_meta("representation","spatially_culled opaque forest clusters")
 set_meta("final_tree_asset",false)
 set_meta("mobile_validation","PENDING")

func _build_forest_cells() -> void:
 var centers := []
 for z: int in range(-72,89,20):
  for x: int in range(-64,65,20):
   var c := Vector3(float(x),0,float(z))
   # Keep the authored village spine and immediate house fronts readable.
   if absf(c.x-sin(c.z*0.018)*2.5) < 13.0 and c.z > -58.0 and c.z < 72.0:
    continue
   centers.append(c)
 for i: int in range(centers.size()):
  _forest_cell(centers[i],i)

func _forest_cell(center: Vector3,index: int) -> void:
 var root := Node3D.new()
 root.name = "ForestCell_%02d" % index
 root.set_meta("art_layer","forest_strata_cell")
 add_child(root)
 var count := rng.randi_range(5,8)
 for i: int in range(count):
  var p := center + Vector3(rng.randf_range(-8.0,8.0),0,rng.randf_range(-8.0,8.0))
  if absf(p.x-sin(p.z*0.018)*2.5) < 9.0 and p.z > -58.0 and p.z < 72.0:
   continue
  var h := rng.randf_range(9.0,15.5)
  var y := _height(p.x,p.z)
  _tree(root,Vector3(p.x,y,p.z),h,rng.randf_range(0.75,1.25))
  if i % 2 == 0:
   _understory(root,p,rng.randf_range(1.3,2.5))

func _tree(parent: Node3D,p: Vector3,height: float,width_scale: float) -> void:
 var trunk := MeshInstance3D.new()
 var trunk_mesh := CylinderMesh.new()
 trunk_mesh.top_radius = 0.14*width_scale
 trunk_mesh.bottom_radius = 0.25*width_scale
 trunk_mesh.height = height*0.60
 trunk_mesh.radial_segments = 6
 trunk.mesh = trunk_mesh
 trunk.material_override = trunk_mat
 trunk.position = p + Vector3(0,height*0.30,0)
 trunk.visibility_range_end = 105.0
 trunk.visibility_range_end_margin = 5.0
 parent.add_child(trunk)
 var crown := MeshInstance3D.new()
 var crown_mesh := SphereMesh.new()
 crown_mesh.radius = height*0.18*width_scale
 crown_mesh.height = height*0.46
 crown_mesh.radial_segments = 7
 crown_mesh.rings = 4
 crown.mesh = crown_mesh
 crown.material_override = canopy_mat
 crown.position = p + Vector3(0,height*0.72,0)
 crown.scale = Vector3(1.15,1.0,0.95)
 crown.visibility_range_end = 125.0
 crown.visibility_range_end_margin = 7.0
 parent.add_child(crown)
 # A second offset crown prevents isolated lollipop silhouettes while staying opaque.
 var crown2 := MeshInstance3D.new()
 crown2.mesh = crown_mesh
 crown2.material_override = canopy_mat
 crown2.position = p + Vector3(height*0.11*width_scale,height*0.66,-height*0.06*width_scale)
 crown2.scale = Vector3(0.82,0.78,0.88)
 crown2.visibility_range_end = 105.0
 parent.add_child(crown2)

func _understory(parent: Node3D,p: Vector3,size: float) -> void:
 var y := _height(p.x,p.z)
 for j: int in range(3):
  var b := MeshInstance3D.new()
  var mesh := SphereMesh.new()
  mesh.radius = size*rng.randf_range(0.35,0.55)
  mesh.height = size*rng.randf_range(0.65,1.0)
  mesh.radial_segments = 6
  mesh.rings = 3
  b.mesh = mesh
  b.material_override = understory_mat
  b.position = Vector3(p.x+rng.randf_range(-1.4,1.4),y+size*0.30,p.z+rng.randf_range(-1.4,1.4))
  b.scale = Vector3(rng.randf_range(0.8,1.35),rng.randf_range(0.7,1.1),rng.randf_range(0.8,1.35))
  b.visibility_range_end = 72.0
  b.visibility_range_end_margin = 5.0
  parent.add_child(b)

func _build_ground_invasion() -> void:
 # Dark irregular ground islands visually break the broad civic/road surfaces.
 var patches := [Vector3(-11,0,60),Vector3(13,0,53),Vector3(-14,0,42),Vector3(15,0,31),Vector3(-13,0,19),Vector3(14,0,7),Vector3(-15,0,-8),Vector3(13,0,-22),Vector3(-14,0,-37),Vector3(15,0,-48)]
 for i: int in range(patches.size()):
  var p: Vector3 = patches[i]
  var node := MeshInstance3D.new()
  var mesh := CylinderMesh.new()
  mesh.top_radius = rng.randf_range(2.0,3.8)
  mesh.bottom_radius = mesh.top_radius*1.05
  mesh.height = 0.035
  mesh.radial_segments = rng.randi_range(7,10)
  node.mesh = mesh
  node.material_override = ground_mat
  node.position = Vector3(p.x,_height(p.x,p.z)+0.035,p.z)
  node.scale = Vector3(rng.randf_range(1.1,1.8),1,rng.randf_range(0.55,1.0))
  node.rotation_degrees.y = rng.randf_range(0,180)
  node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  node.visibility_range_end = 75.0
  node.set_meta("art_layer","forest_ground_invasion")
  add_child(node)

func _height(x: float,z: float) -> float:
 return float(terrain.call("get_height_at",x,z))

func _mat(color: Color,roughness: float) -> StandardMaterial3D:
 var m := StandardMaterial3D.new()
 m.albedo_color = color
 m.roughness = roughness
 return m
