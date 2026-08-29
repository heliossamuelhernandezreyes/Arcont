extends Node3D

# ART-PASS-19: forest-dominant composition with batched spatial strata.
# The village road is a tactical clearing inside a continuous forest wall.

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
 if terrain == null or not terrain.has_method("get_height_at"): return
 rng.seed = 190829
 trunk_mat = _mat(Color(0.048,0.031,0.017),1.0)
 canopy_mat = _mat(Color(0.020,0.052,0.019),0.98)
 canopy_alt_mat = _mat(Color(0.034,0.072,0.026),0.99)
 understory_mat = _mat(Color(0.038,0.082,0.029),0.99)
 ground_mat = _mat(Color(0.045,0.060,0.024),1.0)
 trunk_mesh = CylinderMesh.new(); trunk_mesh.top_radius=0.14; trunk_mesh.bottom_radius=0.27; trunk_mesh.height=1.0; trunk_mesh.radial_segments=6
 crown_mesh = SphereMesh.new(); crown_mesh.radius=0.5; crown_mesh.height=1.0; crown_mesh.radial_segments=7; crown_mesh.rings=4
 bush_mesh = SphereMesh.new(); bush_mesh.radius=0.5; bush_mesh.height=1.0; bush_mesh.radial_segments=6; bush_mesh.rings=3
 _build_forest_cells()
 _build_street_edge_cells()
 _build_ground_invasion()
 set_meta("art_status","ART-PASS-19-BATCHED-FOREST")
 set_meta("forest_contract","CANOPY-SUBCANOPY-UNDERSTORY-GROUND-V5")
 set_meta("representation","spatial MultiMesh forest cells with narrow tactical clearing")
 set_meta("final_tree_asset",false)
 set_meta("visual_acceptance","PENDING_CAPTURE_REVIEW")
 set_meta("mobile_validation","PENDING")

func _build_forest_cells() -> void:
 var index:=0
 for z:int in range(-84,101,16):
  for x:int in range(-72,73,16):
   var c:=Vector3(float(x),0,float(z))
   if _in_primary_clearance(c,8.0): continue
   _forest_cell(c,index); index+=1

func _forest_cell(center:Vector3,index:int)->void:
 var trunks:Array[Transform3D]=[]; var crowns_a:Array[Transform3D]=[]; var crowns_b:Array[Transform3D]=[]; var bushes:Array[Transform3D]=[]
 for i:int in range(rng.randi_range(8,12)):
  var p:=center+Vector3(rng.randf_range(-6.8,6.8),0,rng.randf_range(-6.8,6.8))
  if _in_primary_clearance(p,5.7): continue
  var y:=_height(p.x,p.z); var h:=rng.randf_range(8.0,17.0); var w:=rng.randf_range(0.72,1.34)
  trunks.append(_xf(Vector3(p.x,y+h*0.31,p.z),Vector3(0.26*w,h*0.62,0.26*w),rng.randf_range(-3.0,3.0)))
  var crown_count:=3 if (i+index)%3==0 else 2
  for j:int in range(crown_count):
   var cp:=Vector3(p.x+rng.randf_range(-h*0.13,h*0.13),y+h*rng.randf_range(0.63,0.82),p.z+rng.randf_range(-h*0.11,h*0.11))
   var cs:=Vector3(h*rng.randf_range(0.25,0.40)*w,h*rng.randf_range(0.30,0.46),h*rng.randf_range(0.25,0.40)*w)
   if (i+j+index)%2==0: crowns_a.append(_xf(cp,cs,rng.randf_range(0,180)))
   else: crowns_b.append(_xf(cp,cs,rng.randf_range(0,180)))
  if i%2==0:
   for j:int in range(rng.randi_range(4,7)):
    var s:=rng.randf_range(1.1,2.5); var bp:=Vector3(p.x+rng.randf_range(-2.6,2.6),y+s*0.28,p.z+rng.randf_range(-2.6,2.6)); bushes.append(_xf(bp,Vector3(s*rng.randf_range(0.7,1.4),s*rng.randf_range(0.45,0.9),s*rng.randf_range(0.7,1.4)),rng.randf_range(0,180)))
 var root:=Node3D.new(); root.name="ForestCell_%02d"%index; root.set_meta("art_layer","forest_strata_cell"); add_child(root)
 _multimesh(root,"Trunks",trunk_mesh,trunk_mat,trunks,105.0)
 _multimesh(root,"CanopyA",crown_mesh,canopy_mat,crowns_a,125.0)
 _multimesh(root,"CanopyB",crown_mesh,canopy_alt_mat,crowns_b,110.0)
 _multimesh(root,"Understory",bush_mesh,understory_mat,bushes,72.0)

func _build_street_edge_cells()->void:
 var index:=0
 for z:int in range(-64,79,12):
  for side:float in [-1.0,1.0]:
   var road_x:=sin(float(z)*0.018)*2.5
   var bushes:Array[Transform3D]=[]; var crowns:Array[Transform3D]=[]; var trunks:Array[Transform3D]=[]
   for j:int in range(12):
    var p:=Vector3(road_x+side*rng.randf_range(5.0,8.4),0,float(z)+rng.randf_range(-5.2,5.2)); var y:=_height(p.x,p.z); var s:=rng.randf_range(0.9,2.3)
    bushes.append(_xf(Vector3(p.x,y+s*0.28,p.z),Vector3(s*rng.randf_range(0.7,1.5),s*rng.randf_range(0.5,0.95),s*rng.randf_range(0.7,1.5)),rng.randf_range(0,180)))
    if j%4==0:
     var h:=rng.randf_range(5.5,10.0); trunks.append(_xf(Vector3(p.x+side*1.0,y+h*0.31,p.z),Vector3(0.20,h*0.62,0.20),rng.randf_range(-4,4))); crowns.append(_xf(Vector3(p.x+side*1.0,y+h*0.72,p.z),Vector3(h*0.30,h*0.38,h*0.30),rng.randf_range(0,180)))
   var root:=Node3D.new(); root.name="ForestEdgeCell_%02d"%index; root.set_meta("art_layer","forest_street_edge"); add_child(root)
   _multimesh(root,"EdgeBushes",bush_mesh,understory_mat,bushes,68.0); _multimesh(root,"EdgeTrunks",trunk_mesh,trunk_mat,trunks,90.0); _multimesh(root,"EdgeCrowns",crown_mesh,canopy_alt_mat,crowns,95.0); index+=1

func _build_ground_invasion()->void:
 for z:int in range(-62,77,8):
  var road_x:=sin(float(z)*0.018)*2.5
  for side:float in [-1.0,1.0]:
   var p:=Vector3(road_x+side*rng.randf_range(5.0,7.0),0,float(z)+rng.randf_range(-2.2,2.2)); var node:=MeshInstance3D.new(); var mesh:=CylinderMesh.new(); mesh.top_radius=rng.randf_range(1.4,2.8); mesh.bottom_radius=mesh.top_radius*rng.randf_range(0.92,1.10); mesh.height=0.025; mesh.radial_segments=rng.randi_range(7,10)
   node.mesh=mesh; node.material_override=ground_mat; node.position=Vector3(p.x,_height(p.x,p.z)+0.025,p.z); node.scale=Vector3(rng.randf_range(1.0,1.55),1,rng.randf_range(0.55,1.0)); node.rotation_degrees.y=rng.randf_range(0,180); node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; node.visibility_range_end=65.0; node.set_meta("art_layer","forest_ground_invasion"); add_child(node)

func _multimesh(parent:Node3D,name_:String,mesh:Mesh,material:Material,transforms:Array[Transform3D],range_end:float)->void:
 if transforms.is_empty(): return
 var mm:=MultiMesh.new(); mm.transform_format=MultiMesh.TRANSFORM_3D; mm.mesh=mesh; mm.instance_count=transforms.size()
 for i:int in range(transforms.size()): mm.set_instance_transform(i,transforms[i])
 var node:=MultiMeshInstance3D.new(); node.name=name_; node.multimesh=mm; node.material_override=material; node.visibility_range_end=range_end; node.visibility_range_end_margin=5.0; parent.add_child(node)

func _xf(pos:Vector3,scale_:Vector3,yaw:float)->Transform3D:
 var basis:=Basis(Vector3.UP,deg_to_rad(yaw)).scaled(scale_); return Transform3D(basis,pos)

func _in_primary_clearance(p:Vector3,clearance:float)->bool:
 if p.z < -66.0 or p.z > 80.0: return false
 return absf(p.x-sin(p.z*0.018)*2.5)<clearance

func _height(x:float,z:float)->float: return float(terrain.call("get_height_at",x,z))
func _mat(color:Color,roughness:float)->StandardMaterial3D:
 var m:=StandardMaterial3D.new(); m.albedo_color=color; m.roughness=roughness; return m
