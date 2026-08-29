extends Node3D

# Deterministic mobile-first ecological scatter. Every placement samples the
# continuous terrain, rejects mission/road/building clearances, and uses slope
# and elevation to create readable forest bands instead of uniform decoration.
@export var seed := 73191
@export var cell_size := 36.0
@export var grass_per_cell := 28
@export var stone_per_cell := 8
@export var visibility_end := 78.0
@export var max_grass_slope := 0.34
@export var min_stone_slope := 0.12

var rng := RandomNumberGenerator.new()
var terrain: Node
var grass_mesh: QuadMesh
var stone_mesh: SphereMesh
var grass_material: StandardMaterial3D
var stone_material: StandardMaterial3D

func _ready() -> void:
 rng.seed = seed
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 _build_resources()
 _build_chunks()
 set_meta("tool_role","EnvironmentScatter")
 set_meta("deterministic_seed",seed)
 set_meta("spatial_cell_m",cell_size)
 set_meta("art_status","ART-PASS-4-ECO-SCATTER")
 set_meta("placement_rule","height+slope+mission_clearance")

func _build_resources() -> void:
 grass_mesh=QuadMesh.new()
 grass_mesh.size=Vector2(0.42,0.72)
 grass_material=StandardMaterial3D.new()
 grass_material.albedo_color=Color(0.16,0.24,0.08,1)
 grass_material.shading_mode=BaseMaterial3D.SHADING_MODE_PER_PIXEL
 grass_material.cull_mode=BaseMaterial3D.CULL_DISABLED
 grass_mesh.material=grass_material
 stone_mesh=SphereMesh.new()
 stone_mesh.radius=0.34
 stone_mesh.height=0.48
 stone_mesh.radial_segments=8
 stone_mesh.rings=4
 stone_material=StandardMaterial3D.new()
 stone_material.albedo_color=Color(0.22,0.23,0.20,1)
 stone_material.roughness=1.0
 stone_mesh.material=stone_material

func _build_chunks() -> void:
 # Smaller spatial groups preserve useful coarse culling on mobile. MultiMesh is
 # intentionally split because individual instances are not frustum-culled.
 var centers := [Vector3(-54,0,-72),Vector3(54,0,-72),Vector3(-54,0,-28),Vector3(54,0,-28),Vector3(-54,0,24),Vector3(54,0,24),Vector3(-54,0,70),Vector3(54,0,70)]
 for index in range(centers.size()):
  var center:Vector3=centers[index]
  _make_multimesh_cell("GrassCell_%02d"%index,center,grass_mesh,grass_per_cell,true)
  _make_multimesh_cell("StoneCell_%02d"%index,center,stone_mesh,stone_per_cell,false)

func _make_multimesh_cell(node_name:String,center:Vector3,mesh:Mesh,count:int,is_grass:bool) -> void:
 var accepted:Array[Transform3D]=[]
 var attempts:=0
 var max_attempts:=count*10
 while accepted.size()<count and attempts<max_attempts:
  attempts+=1
  var wx:=center.x+rng.randf_range(-cell_size*0.46,cell_size*0.46)
  var wz:=center.z+rng.randf_range(-cell_size*0.46,cell_size*0.46)
  if not _placement_allowed(wx,wz,is_grass):
   continue
  var wy:=_terrain_height(wx,wz)+(0.03 if is_grass else 0.10)
  var yaw:=rng.randf_range(-PI,PI)
  var scale_value:=rng.randf_range(0.72,1.30) if is_grass else rng.randf_range(0.55,1.45)
  var basis:=Basis(Vector3.UP,yaw).scaled(Vector3(scale_value,scale_value,scale_value))
  accepted.append(Transform3D(basis,Vector3(wx-center.x,wy,wz-center.z)))
 if accepted.is_empty():
  return
 var node:=MultiMeshInstance3D.new()
 node.name=node_name
 node.position=Vector3(center.x,0.0,center.z)
 node.visibility_range_end=visibility_end if is_grass else visibility_end+26.0
 node.visibility_range_end_margin=8.0
 node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 var mm:=MultiMesh.new()
 mm.transform_format=MultiMesh.TRANSFORM_3D
 mm.mesh=mesh
 mm.instance_count=accepted.size()
 for i in range(accepted.size()):
  mm.set_instance_transform(i,accepted[i])
 node.multimesh=mm
 node.set_meta("scatter_cell",true)
 node.set_meta("collision_mode","decorative_none")
 node.set_meta("accepted_instances",accepted.size())
 add_child(node)

func _placement_allowed(x:float,z:float,is_grass:bool) -> bool:
 # Main road and village are authored negative space: readable traversal/combat.
 var road_center:=sin(z*0.018)*2.5
 if absf(x-road_center)<10.5:
  return false
 if Vector2(x,z-18.0).length()<31.0:
  return false
 # Keep the stream bed open while allowing vegetation on its banks.
 var stream_center:=-40.0-sin(x*0.035)*2.4
 if absf(z-stream_center)<4.2:
  return false
 # Explicit building/mission landmark exclusion circles.
 var exclusions := [
  Vector3(-22,0,-20),Vector3(20,0,-23),Vector3(-25,0,8),Vector3(24,0,9),
  Vector3(-20,0,35),Vector3(20,0,34),Vector3(-37,0,25),Vector3(37,0,-2),
  Vector3(-9,0,22),Vector3(7.5,0,23.5),Vector3(0,0,52)
 ]
 for p in exclusions:
  if Vector2(x-p.x,z-p.z).length()<9.0:
   return false
 var slope:=_terrain_slope(x,z)
 var height:=_terrain_height(x,z)
 if is_grass:
  # Grass favors gentle lower/mid terrain; sparse on steep ridge faces.
  return slope<=max_grass_slope and height<5.6
 # Stones reinforce drainage edges and ridges instead of peppering flat arenas.
 return slope>=min_stone_slope or height>2.4

func _terrain_height(x:float,z:float) -> float:
 if terrain!=null and terrain.has_method("get_height_at"):
  return float(terrain.call("get_height_at",x,z))
 return 0.0

func _terrain_slope(x:float,z:float) -> float:
 if terrain!=null and terrain.has_method("get_slope_at"):
  return float(terrain.call("get_slope_at",x,z))
 return 0.0
