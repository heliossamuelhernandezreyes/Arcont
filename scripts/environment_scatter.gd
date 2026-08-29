extends Node3D

# Mobile-first ecological forest dressing. The heightmap drives elevation and
# slope; authored masks preserve roads, village combat cells and landmarks.
# Repeated vegetation is chunked into MultiMeshes for Mobile renderer budgets.
@export var seed := 73191
@export var cell_size := 36.0
@export var grass_per_cell := 30
@export var stone_per_cell := 9
@export var shrub_per_cell := 10
@export var tree_per_cell := 8
@export var visibility_end := 78.0
@export var max_grass_slope := 0.34
@export var max_tree_slope := 0.48
@export var min_stone_slope := 0.12

var rng := RandomNumberGenerator.new()
var terrain: Node
var grass_mesh: QuadMesh
var stone_mesh: SphereMesh
var shrub_mesh: SphereMesh
var tree_mesh: CylinderMesh
var grass_material: StandardMaterial3D
var stone_material: StandardMaterial3D
var shrub_material: StandardMaterial3D
var tree_material: StandardMaterial3D

func _ready() -> void:
 rng.seed=seed
 terrain=get_parent().get_node_or_null("ForestTerrainRelief")
 _build_resources()
 _build_chunks()
 _add_authored_edge_dressing()
 set_meta("tool_role","EnvironmentScatter")
 set_meta("deterministic_seed",seed)
 set_meta("spatial_cell_m",cell_size)
 set_meta("art_status","ART-PASS-5-FOREST-BIOMES")
 set_meta("placement_rule","height+slope+biome+mission_clearance")
 set_meta("design_rule","dense edges + readable clearings + ridge silhouettes")

func _build_resources() -> void:
 grass_mesh=QuadMesh.new(); grass_mesh.size=Vector2(0.44,0.76)
 grass_material=_mat(Color(0.14,0.22,0.07),0.98); grass_material.cull_mode=BaseMaterial3D.CULL_DISABLED; grass_mesh.material=grass_material
 stone_mesh=SphereMesh.new(); stone_mesh.radius=0.34; stone_mesh.height=0.48; stone_mesh.radial_segments=8; stone_mesh.rings=4
 stone_material=_mat(Color(0.22,0.23,0.20),1.0); stone_mesh.material=stone_material
 shrub_mesh=SphereMesh.new(); shrub_mesh.radius=0.48; shrub_mesh.height=0.72; shrub_mesh.radial_segments=8; shrub_mesh.rings=4
 shrub_material=_mat(Color(0.085,0.16,0.045),0.96); shrub_mesh.material=shrub_material
 tree_mesh=CylinderMesh.new(); tree_mesh.top_radius=0.16; tree_mesh.bottom_radius=0.26; tree_mesh.height=4.8; tree_mesh.radial_segments=7
 tree_material=_mat(Color(0.105,0.072,0.042),0.97); tree_mesh.material=tree_material

func _mat(color:Color,roughness:float)->StandardMaterial3D:
 var m:=StandardMaterial3D.new(); m.albedo_color=color; m.roughness=roughness; return m

func _build_chunks() -> void:
 var centers := [Vector3(-54,0,-72),Vector3(54,0,-72),Vector3(-54,0,-28),Vector3(54,0,-28),Vector3(-54,0,24),Vector3(54,0,24),Vector3(-54,0,70),Vector3(54,0,70)]
 for index in range(centers.size()):
  var center:Vector3=centers[index]
  _make_cell("GrassCell_%02d"%index,center,grass_mesh,grass_per_cell,"grass")
  _make_cell("StoneCell_%02d"%index,center,stone_mesh,stone_per_cell,"stone")
  _make_cell("ShrubCell_%02d"%index,center,shrub_mesh,shrub_per_cell,"shrub")
  _make_cell("TreeCell_%02d"%index,center,tree_mesh,tree_per_cell,"tree")

func _make_cell(node_name:String,center:Vector3,mesh:Mesh,count:int,kind:String)->void:
 var accepted:Array[Transform3D]=[]
 var attempts:=0
 while accepted.size()<count and attempts<count*16:
  attempts+=1
  var wx:=center.x+rng.randf_range(-cell_size*0.46,cell_size*0.46)
  var wz:=center.z+rng.randf_range(-cell_size*0.46,cell_size*0.46)
  if not _placement_allowed(wx,wz,kind): continue
  var wy:=_terrain_height(wx,wz)
  var yaw:=rng.randf_range(-PI,PI)
  var scale_value:=_scale_for(kind)
  var basis:=Basis(Vector3.UP,yaw).scaled(Vector3(scale_value,scale_value,scale_value))
  var lift:=0.04
  if kind=="stone": lift=0.10
  elif kind=="tree": lift=2.35*scale_value
  elif kind=="shrub": lift=0.24*scale_value
  accepted.append(Transform3D(basis,Vector3(wx-center.x,wy+lift,wz-center.z)))
 if accepted.is_empty(): return
 var node:=MultiMeshInstance3D.new(); node.name=node_name; node.position=Vector3(center.x,0,center.z)
 node.visibility_range_end=_visibility_for(kind); node.visibility_range_end_margin=9.0
 node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON if kind=="tree" else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 var mm:=MultiMesh.new(); mm.transform_format=MultiMesh.TRANSFORM_3D; mm.mesh=mesh; mm.instance_count=accepted.size()
 for i in range(accepted.size()): mm.set_instance_transform(i,accepted[i])
 node.multimesh=mm; node.set_meta("scatter_cell",true); node.set_meta("biome_kind",kind); node.set_meta("accepted_instances",accepted.size()); add_child(node)

func _scale_for(kind:String)->float:
 match kind:
  "tree": return rng.randf_range(0.78,1.35)
  "shrub": return rng.randf_range(0.70,1.55)
  "stone": return rng.randf_range(0.55,1.55)
  _: return rng.randf_range(0.72,1.30)

func _visibility_for(kind:String)->float:
 if kind=="grass": return visibility_end
 if kind=="shrub": return visibility_end+22.0
 return visibility_end+48.0

func _placement_allowed(x:float,z:float,kind:String)->bool:
 if _in_authored_clearance(x,z): return false
 var slope:=_terrain_slope(x,z)
 var height:=_terrain_height(x,z)
 var edge_factor: float = clampf((absf(x)-34.0)/28.0,0.0,1.0)
 var ridge_factor: float = clampf((height-1.2)/3.8,0.0,1.0)
 match kind:
  "grass": return slope<=max_grass_slope and height<5.8
  "shrub": return slope<0.42 and (edge_factor>0.16 or ridge_factor>0.15)
  "tree": return slope<=max_tree_slope and (edge_factor>0.34 or ridge_factor>0.34)
  "stone": return slope>=min_stone_slope or height>2.4
 return false

func _in_authored_clearance(x:float,z:float)->bool:
 var road_center:=sin(z*0.018)*2.5
 if absf(x-road_center)<10.5: return true
 if Vector2(x,z-18.0).length()<31.0: return true
 var stream_center:=-40.0-sin(x*0.035)*2.4
 if absf(z-stream_center)<4.2: return true
 var exclusions := [Vector3(-22,0,-20),Vector3(20,0,-23),Vector3(-25,0,8),Vector3(24,0,9),Vector3(-20,0,35),Vector3(20,0,34),Vector3(-37,0,25),Vector3(37,0,-2),Vector3(-9,0,22),Vector3(7.5,0,23.5),Vector3(0,0,52)]
 for p in exclusions:
  if Vector2(x-p.x,z-p.z).length()<9.0: return true
 return false

func _add_authored_edge_dressing()->void:
 var anchors := [Vector3(-35,0,-67),Vector3(37,0,-61),Vector3(-43,0,-12),Vector3(42,0,18),Vector3(-39,0,53),Vector3(38,0,61)]
 for i in range(anchors.size()):
  var p:Vector3=anchors[i]; p.y=_terrain_height(p.x,p.z)+0.22
  var log:=MeshInstance3D.new(); log.name="FallenLog_%02d"%i
  var mesh:=CylinderMesh.new(); mesh.top_radius=0.22; mesh.bottom_radius=0.28; mesh.height=rng.randf_range(3.4,5.6); mesh.radial_segments=7; mesh.material=tree_material
  log.mesh=mesh; log.position=p; log.rotation_degrees=Vector3(90,rng.randf_range(-35,35),0); log.visibility_range_end=112.0; log.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON; log.set_meta("forest_edge_dressing",true); add_child(log)

func _terrain_height(x:float,z:float)->float:
 if terrain!=null and terrain.has_method("get_height_at"): return float(terrain.call("get_height_at",x,z))
 return 0.0

func _terrain_slope(x:float,z:float)->float:
 if terrain!=null and terrain.has_method("get_slope_at"): return float(terrain.call("get_slope_at",x,z))
 return 0.0
