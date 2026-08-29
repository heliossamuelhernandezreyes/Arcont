extends Node3D

# Mobile-first ecological forest dressing. The heightmap drives elevation and
# slope; authored masks preserve roads, village combat cells and landmarks.
# Repeated vegetation uses promoted CC0 runtime meshes through chunked
# MultiMeshes. Procedural geometry remains only as a safe fallback or where the
# selected CC0 library does not yet contain a semantically correct small prop.
const FOREST_ROOT := "res://assets/provisional/cc0_runtime/forest/"
const GRASS_ASSET := FOREST_ROOT + "grass.fbx"
const SHRUB_ASSET := FOREST_ROOT + "plant_bush.fbx"
const TREE_ASSET := FOREST_ROOT + "tree_blocks.fbx"

@export var seed := 73191
@export var cell_size := 36.0
@export var grass_per_cell := 12
@export var stone_per_cell := 9
@export var shrub_per_cell := 8
@export var tree_per_cell := 12
@export var visibility_end := 78.0
@export var max_grass_slope := 0.34
@export var max_tree_slope := 0.48
@export var min_stone_slope := 0.12

var rng := RandomNumberGenerator.new()
var terrain: Node
var prototypes := {}
var stone_mesh: SphereMesh
var stone_material: StandardMaterial3D
var fallback_grass: QuadMesh
var fallback_shrub: SphereMesh
var fallback_tree: CylinderMesh
var fallback_tree_material: StandardMaterial3D

func _ready() -> void:
 rng.seed=seed
 terrain=get_parent().get_node_or_null("ForestTerrainRelief")
 _build_resources()
 _build_chunks()
 _add_authored_edge_dressing()
 call_deferred("_remove_legacy_forest_duplicates")
 set_meta("tool_role","EnvironmentScatter")
 set_meta("deterministic_seed",seed)
 set_meta("spatial_cell_m",cell_size)
 set_meta("art_status","ART-PASS-7-CC0-SCATTER")
 set_meta("placement_rule","height+slope+biome+mission_clearance")
 set_meta("design_rule","dense edges + readable clearings + ridge silhouettes")
 set_meta("repeated_asset_owner","EnvironmentScatter")
 set_meta("cc0_runtime_assets",[GRASS_ASSET,SHRUB_ASSET,TREE_ASSET])

func _build_resources() -> void:
 fallback_grass=QuadMesh.new(); fallback_grass.size=Vector2(0.44,0.76)
 var grass_mat:=_mat(Color(0.14,0.22,0.07),0.98); grass_mat.cull_mode=BaseMaterial3D.CULL_DISABLED; fallback_grass.material=grass_mat
 fallback_shrub=SphereMesh.new(); fallback_shrub.radius=0.48; fallback_shrub.height=0.72; fallback_shrub.radial_segments=8; fallback_shrub.rings=4
 fallback_shrub.material=_mat(Color(0.085,0.16,0.045),0.96)
 fallback_tree=CylinderMesh.new(); fallback_tree.top_radius=0.16; fallback_tree.bottom_radius=0.26; fallback_tree.height=4.8; fallback_tree.radial_segments=7
 fallback_tree_material=_mat(Color(0.105,0.072,0.042),0.97); fallback_tree.material=fallback_tree_material
 stone_mesh=SphereMesh.new(); stone_mesh.radius=0.34; stone_mesh.height=0.48; stone_mesh.radial_segments=8; stone_mesh.rings=4
 stone_material=_mat(Color(0.22,0.23,0.20),1.0); stone_mesh.material=stone_material
 prototypes["grass"]=_load_prototype(GRASS_ASSET,fallback_grass,0.76,-0.38)
 prototypes["shrub"]=_load_prototype(SHRUB_ASSET,fallback_shrub,0.96,-0.36)
 prototypes["tree"]=_load_prototype(TREE_ASSET,fallback_tree,4.8,-2.4)

func _load_prototype(path:String,fallback:Mesh,fallback_extent:float,fallback_bottom:float)->Dictionary:
 var result := {"mesh":fallback,"local_transform":Transform3D.IDENTITY,"source_extent":fallback_extent,"bottom_y":fallback_bottom,"real":false,"path":path}
 if not ResourceLoader.exists(path): return result
 var packed:=load(path) as PackedScene
 if packed==null: return result
 var root:=packed.instantiate() as Node3D
 if root==null: return result
 var meshes:Array[MeshInstance3D]=[]
 _collect_meshes(root,meshes)
 # MultiMesh can only own one Mesh resource. Do not silently discard pieces of
 # a multi-mesh source; keep the known-safe fallback until that source is baked.
 if meshes.size()==1 and meshes[0].mesh!=null:
  var bounds:=AssetScaleNormalizer.visual_bounds(root)
  var longest:=maxf(bounds.size.x,maxf(bounds.size.y,bounds.size.z))
  if longest>0.0001:
   result["mesh"]=meshes[0].mesh
   result["local_transform"]=_relative_transform(meshes[0],root)
   result["source_extent"]=longest
   result["bottom_y"]=bounds.position.y
   result["real"]=true
 root.free()
 return result

func _collect_meshes(node:Node,result:Array[MeshInstance3D])->void:
 if node is MeshInstance3D and (node as MeshInstance3D).mesh!=null: result.append(node as MeshInstance3D)
 for child in node.get_children(): _collect_meshes(child,result)

func _relative_transform(node:Node3D,root:Node3D)->Transform3D:
 var chain:Array[Node3D]=[]
 var current:Node=node
 while current!=null and current!=root:
  if current is Node3D: chain.push_front(current as Node3D)
  current=current.get_parent()
 var result:=Transform3D.IDENTITY
 for part in chain: result=result*part.transform
 return result

func _mat(color:Color,roughness:float)->StandardMaterial3D:
 var m:=StandardMaterial3D.new(); m.albedo_color=color; m.roughness=roughness; return m

func _build_chunks() -> void:
 var centers := [Vector3(-54,0,-72),Vector3(54,0,-72),Vector3(-54,0,-28),Vector3(54,0,-28),Vector3(-54,0,24),Vector3(54,0,24),Vector3(-54,0,70),Vector3(54,0,70)]
 for index in range(centers.size()):
  var center:Vector3=centers[index]
  _make_cell("GrassCell_%02d"%index,center,grass_per_cell,"grass")
  _make_cell("StoneCell_%02d"%index,center,stone_per_cell,"stone")
  _make_cell("ShrubCell_%02d"%index,center,shrub_per_cell,"shrub")
  _make_cell("TreeCell_%02d"%index,center,tree_per_cell,"tree")

func _make_cell(node_name:String,center:Vector3,count:int,kind:String)->void:
 var mesh:Mesh=stone_mesh if kind=="stone" else prototypes[kind]["mesh"] as Mesh
 if mesh==null: return
 var accepted:Array[Transform3D]=[]
 var attempts:=0
 while accepted.size()<count and attempts<count*16:
  attempts+=1
  var wx:=center.x+rng.randf_range(-cell_size*0.46,cell_size*0.46)
  var wz:=center.z+rng.randf_range(-cell_size*0.46,cell_size*0.46)
  if not _placement_allowed(wx,wz,kind): continue
  var wy:=_terrain_height(wx,wz)
  var yaw:=rng.randf_range(-PI,PI)
  if kind=="stone":
   var stone_scale:=rng.randf_range(0.55,1.55)
   var stone_basis:=Basis(Vector3.UP,yaw).scaled(Vector3.ONE*stone_scale)
   accepted.append(Transform3D(stone_basis,Vector3(wx-center.x,wy+0.10,wz-center.z)))
  else:
   var prototype:Dictionary=prototypes[kind]
   var factor:=_target_extent(kind)/float(prototype["source_extent"])
   var placement:=Transform3D(Basis(Vector3.UP,yaw).scaled(Vector3.ONE*factor),Vector3(wx-center.x,wy-float(prototype["bottom_y"])*factor+0.02,wz-center.z))
   accepted.append(placement*(prototype["local_transform"] as Transform3D))
 if accepted.is_empty(): return
 var node:=MultiMeshInstance3D.new(); node.name=node_name; node.position=Vector3(center.x,0,center.z)
 node.visibility_range_end=_visibility_for(kind); node.visibility_range_end_margin=9.0
 node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON if kind=="tree" else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 var mm:=MultiMesh.new(); mm.transform_format=MultiMesh.TRANSFORM_3D; mm.mesh=mesh; mm.instance_count=accepted.size()
 for i in range(accepted.size()): mm.set_instance_transform(i,accepted[i])
 node.multimesh=mm
 node.set_meta("scatter_cell",true); node.set_meta("biome_kind",kind); node.set_meta("accepted_instances",accepted.size())
 if kind!="stone":
  node.set_meta("asset_source",String(prototypes[kind]["path"])); node.set_meta("cc0_runtime",bool(prototypes[kind]["real"]))
 add_child(node)

func _target_extent(kind:String)->float:
 match kind:
  "tree": return rng.randf_range(8.0,13.2)
  "shrub": return rng.randf_range(1.1,1.85)
  "grass": return rng.randf_range(0.62,1.12)
  _: return 1.0

func _visibility_for(kind:String)->float:
 if kind=="grass": return minf(visibility_end,48.0)
 if kind=="shrub": return visibility_end+22.0
 return visibility_end+48.0

func _placement_allowed(x:float,z:float,kind:String)->bool:
 if _in_authored_clearance(x,z): return false
 var slope:=_terrain_slope(x,z)
 var height:=_terrain_height(x,z)
 var edge_factor:float=clampf((absf(x)-34.0)/28.0,0.0,1.0)
 var ridge_factor:float=clampf((height-1.2)/3.8,0.0,1.0)
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

func _remove_legacy_forest_duplicates()->void:
 var legacy:=get_parent().get_node_or_null("ForestVillage")
 if legacy==null: return
 var removed:=0
 var nodes:Array[Node]=[]
 _collect_nodes(legacy,nodes)
 for node in nodes:
  if node==legacy or not node.has_meta("art_layer"): continue
  var layer:=String(node.get_meta("art_layer",""))
  if layer in ["canopy","understory","ground_detail"]:
   node.queue_free(); removed+=1
 set_meta("legacy_forest_duplicates_removed",removed)

func _collect_nodes(node:Node,result:Array[Node])->void:
 result.append(node)
 for child in node.get_children(): _collect_nodes(child,result)

func _add_authored_edge_dressing()->void:
 # No selected CC0 asset is a true fallen trunk yet; retain a cheap procedural
 # placeholder rather than misuse campfire_logs.fbx. This is tracked as an
 # acquisition gap in Reference Lab.
 var anchors := [Vector3(-35,0,-67),Vector3(37,0,-61),Vector3(-43,0,-12),Vector3(42,0,18),Vector3(-39,0,53),Vector3(38,0,61)]
 for i in range(anchors.size()):
  var p:Vector3=anchors[i]; p.y=_terrain_height(p.x,p.z)+0.22
  var log:=MeshInstance3D.new(); log.name="FallenLog_%02d"%i
  var mesh:=CylinderMesh.new(); mesh.top_radius=0.22; mesh.bottom_radius=0.28; mesh.height=rng.randf_range(3.4,5.6); mesh.radial_segments=7; mesh.material=fallback_tree_material
  log.mesh=mesh; log.position=p; log.rotation_degrees=Vector3(90,rng.randf_range(-35,35),0); log.visibility_range_end=112.0; log.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON; log.set_meta("forest_edge_dressing",true); log.set_meta("placeholder_reason","no_semantic_cc0_fallen_trunk"); add_child(log)

func _terrain_height(x:float,z:float)->float:
 if terrain!=null and terrain.has_method("get_height_at"): return float(terrain.call("get_height_at",x,z))
 return 0.0

func _terrain_slope(x:float,z:float)->float:
 if terrain!=null and terrain.has_method("get_slope_at"): return float(terrain.call("get_slope_at",x,z))
 return 0.0
