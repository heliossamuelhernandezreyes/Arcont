extends Node3D

# ART-PASS-18: forest-dominant village composition.
# The road is a tactical clearing inside the forest, not the dominant visual mass.

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
 if terrain == null or not terrain.has_method("get_height_at"): return
 rng.seed = 180829
 trunk_mat = _mat(Color(0.035,0.022,0.012),1.0)
 canopy_mat = _mat(Color(0.014,0.036,0.013),0.98)
 canopy_alt_mat = _mat(Color(0.025,0.052,0.019),0.99)
 understory_mat = _mat(Color(0.030,0.064,0.023),0.99)
 ground_mat = _mat(Color(0.034,0.046,0.019),1.0)
 _build_forest_cells()
 _build_street_walls()
 _build_roadside_saplings()
 _build_ground_invasion()
 set_meta("art_status","ART-PASS-18-FOREST-DOMINANT")
 set_meta("forest_contract","CANOPY-SUBCANOPY-UNDERSTORY-GROUND-V4")
 set_meta("representation","spatial opaque forest cells framing a narrow tactical clearing")
 set_meta("final_tree_asset",false)
 set_meta("visual_acceptance","PENDING_CAPTURE_REVIEW")
 set_meta("mobile_validation","PENDING")

func _build_forest_cells() -> void:
 var index := 0
 for z: int in range(-82,99,14):
  for x: int in range(-70,71,14):
   var c := Vector3(float(x),0,float(z))
   if _in_primary_clearance(c,8.5): continue
   _forest_cell(c,index); index += 1

func _forest_cell(center: Vector3,index: int) -> void:
 var root := Node3D.new(); root.name="ForestCell_%02d"%index; root.set_meta("art_layer","forest_strata_cell"); add_child(root)
 for i: int in range(rng.randi_range(8,12)):
  var p := center+Vector3(rng.randf_range(-6.2,6.2),0,rng.randf_range(-6.2,6.2))
  if _in_primary_clearance(p,6.0): continue
  _tree(root,p,rng.randf_range(8.0,17.0),rng.randf_range(0.70,1.34),i+index)
  if i%2==0: _understory_cluster(root,p,rng.randf_range(1.5,3.0),rng.randi_range(4,6))

func _build_street_walls() -> void:
 var index := 0
 for z: int in range(-62,77,7):
  var road_x := sin(float(z)*0.018)*2.5
  for side: float in [-1.0,1.0]:
   var root:=Node3D.new(); root.name="ForestEdge_%02d"%index; root.set_meta("art_layer","forest_street_edge"); add_child(root)
   var p:=Vector3(road_x+side*rng.randf_range(6.3,8.6),0,float(z)+rng.randf_range(-2.5,2.5))
   _understory_cluster(root,p,rng.randf_range(1.9,3.3),rng.randi_range(6,9))
   if index%4!=1: _tree(root,p+Vector3(side*rng.randf_range(1.0,3.2),0,rng.randf_range(-2.6,2.6)),rng.randf_range(7.0,13.5),rng.randf_range(0.72,1.18),index)
   index+=1

func _build_roadside_saplings() -> void:
 # Small irregular vegetation reaches toward the road without entering the core combat lane.
 var index := 0
 for z: int in range(-56,70,6):
  var road_x := sin(float(z)*0.018)*2.5
  for side: float in [-1.0,1.0]:
   if (index+int(z))%3==0:
    index+=1; continue
   var root:=Node3D.new(); root.name="RoadsideGrowth_%02d"%index; root.set_meta("art_layer","forest_roadside_growth"); add_child(root)
   var p:=Vector3(road_x+side*rng.randf_range(5.1,6.4),0,float(z)+rng.randf_range(-1.8,1.8))
   _understory_cluster(root,p,rng.randf_range(1.0,1.8),rng.randi_range(3,5))
   if index%5==0: _tree(root,p+Vector3(side*1.0,0,rng.randf_range(-1.2,1.2)),rng.randf_range(5.5,8.0),rng.randf_range(0.55,0.82),index+200)
   index+=1

func _tree(parent:Node3D,p:Vector3,height:float,width_scale:float,variant:int)->void:
 var y:=_height(p.x,p.z)
 var trunk:=MeshInstance3D.new(); var tm:=CylinderMesh.new(); tm.top_radius=0.13*width_scale; tm.bottom_radius=0.27*width_scale; tm.height=height*0.62; tm.radial_segments=6
 trunk.mesh=tm; trunk.material_override=trunk_mat; trunk.position=Vector3(p.x,y+height*0.31,p.z); trunk.rotation_degrees.z=rng.randf_range(-4.0,4.0); trunk.visibility_range_end=100.0; parent.add_child(trunk)
 var crown_count:=3 if variant%3==0 else 2
 for j:int in range(crown_count):
  var crown:=MeshInstance3D.new(); var mesh:=SphereMesh.new(); mesh.radius=height*rng.randf_range(0.14,0.21)*width_scale; mesh.height=height*rng.randf_range(0.32,0.50); mesh.radial_segments=7; mesh.rings=4
  crown.mesh=mesh; crown.material_override=canopy_mat if (variant+j)%2==0 else canopy_alt_mat; crown.position=Vector3(p.x+rng.randf_range(-height*0.14,height*0.14),y+height*rng.randf_range(0.62,0.83),p.z+rng.randf_range(-height*0.12,height*0.12)); crown.scale=Vector3(rng.randf_range(0.70,1.32),rng.randf_range(0.70,1.16),rng.randf_range(0.70,1.34)); crown.visibility_range_end=120.0 if j==0 else 95.0; parent.add_child(crown)

func _understory_cluster(parent:Node3D,p:Vector3,size:float,count:int)->void:
 var y:=_height(p.x,p.z)
 for j:int in range(count):
  var b:=MeshInstance3D.new(); var mesh:=SphereMesh.new(); mesh.radius=size*rng.randf_range(0.25,0.54); mesh.height=size*rng.randf_range(0.45,0.98); mesh.radial_segments=6; mesh.rings=3
  b.mesh=mesh; b.material_override=understory_mat; b.position=Vector3(p.x+rng.randf_range(-2.3,2.3),y+size*rng.randf_range(0.18,0.34),p.z+rng.randf_range(-2.3,2.3)); b.scale=Vector3(rng.randf_range(0.62,1.55),rng.randf_range(0.62,1.18),rng.randf_range(0.62,1.55)); b.visibility_range_end=68.0; parent.add_child(b)

func _build_ground_invasion()->void:
 for z:int in range(-62,77,6):
  var road_x:=sin(float(z)*0.018)*2.5
  for side:float in [-1.0,1.0]:
   var p:=Vector3(road_x+side*rng.randf_range(5.4,7.4),0,float(z)+rng.randf_range(-1.8,1.8))
   var node:=MeshInstance3D.new(); var mesh:=CylinderMesh.new(); mesh.top_radius=rng.randf_range(2.2,4.2); mesh.bottom_radius=mesh.top_radius*rng.randf_range(0.92,1.12); mesh.height=0.032; mesh.radial_segments=rng.randi_range(7,11)
   node.mesh=mesh; node.material_override=ground_mat; node.position=Vector3(p.x,_height(p.x,p.z)+0.032,p.z); node.scale=Vector3(rng.randf_range(1.0,1.8),1,rng.randf_range(0.55,1.15)); node.rotation_degrees.y=rng.randf_range(0,180); node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; node.visibility_range_end=72.0; node.set_meta("art_layer","forest_ground_invasion"); add_child(node)

func _in_primary_clearance(p:Vector3,clearance:float)->bool:
 if p.z < -64.0 or p.z > 78.0: return false
 return absf(p.x-sin(p.z*0.018)*2.5)<clearance

func _height(x:float,z:float)->float: return float(terrain.call("get_height_at",x,z))
func _mat(color:Color,roughness:float)->StandardMaterial3D:
 var m:=StandardMaterial3D.new(); m.albedo_color=color; m.roughness=roughness; return m
