extends Node3D

# Deterministic mobile-first forest scatter. Repeated low-cost vegetation is split
# into spatial MultiMesh cells so culling/visibility works per forest sector.
@export var seed := 73191
@export var cell_size := 36.0
@export var grass_per_cell := 24
@export var stone_per_cell := 7
@export var visibility_end := 78.0

var rng := RandomNumberGenerator.new()
var grass_mesh: QuadMesh
var stone_mesh: SphereMesh
var grass_material: StandardMaterial3D
var stone_material: StandardMaterial3D

func _ready() -> void:
 rng.seed = seed
 _build_resources()
 _build_chunks()
 set_meta("tool_role","EnvironmentScatter")
 set_meta("deterministic_seed",seed)
 set_meta("spatial_cell_m",cell_size)
 set_meta("art_status","ART-PASS-3-SCATTER")

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
 var centers := [Vector3(-54,0,-72),Vector3(54,0,-72),Vector3(-54,0,-28),Vector3(54,0,-28),Vector3(-54,0,24),Vector3(54,0,24),Vector3(-54,0,70),Vector3(54,0,70)]
 for index in range(centers.size()):
  var center:Vector3=centers[index]
  _make_multimesh_cell("GrassCell_%02d"%index,center,grass_mesh,grass_per_cell,true)
  _make_multimesh_cell("StoneCell_%02d"%index,center,stone_mesh,stone_per_cell,false)

func _make_multimesh_cell(node_name:String,center:Vector3,mesh:Mesh,count:int,is_grass:bool) -> void:
 var node:=MultiMeshInstance3D.new()
 node.name=node_name
 node.position=center
 node.visibility_range_end=visibility_end if is_grass else visibility_end+26.0
 node.visibility_range_end_margin=8.0
 node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 var mm:=MultiMesh.new()
 mm.transform_format=MultiMesh.TRANSFORM_3D
 mm.mesh=mesh
 mm.instance_count=count
 for i in range(count):
  var local:=Vector3(rng.randf_range(-cell_size*0.46,cell_size*0.46),0.04,rng.randf_range(-cell_size*0.46,cell_size*0.46))
  # Keep the central mission road readable instead of filling every surface uniformly.
  if absf(center.x+local.x)<12.0:
   local.x=signf(center.x if center.x!=0 else 1.0)*rng.randf_range(13.0,cell_size*0.48)
  var yaw:=rng.randf_range(-PI,PI)
  var scale_value:=rng.randf_range(0.72,1.30) if is_grass else rng.randf_range(0.55,1.45)
  var basis:=Basis(Vector3.UP,yaw).scaled(Vector3(scale_value,scale_value,scale_value))
  mm.set_instance_transform(i,Transform3D(basis,local))
 node.multimesh=mm
 node.set_meta("scatter_cell",true)
 node.set_meta("collision_mode","decorative_none")
 add_child(node)
