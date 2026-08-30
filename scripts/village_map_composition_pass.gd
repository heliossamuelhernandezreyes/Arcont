extends Node3D

# ART-PASS-13: settlement composition. The frame must read as an abandoned
# rural village being reclaimed by forest, with vegetation entering parcels
# and narrowing the urban void without blocking the authored mission spine.

const TREE := "res://assets/provisional/cc0_runtime/forest/tree_blocks.fbx"
const BUSH := "res://assets/provisional/cc0_runtime/forest/plant_bush.fbx"
const STUMP := "res://assets/provisional/cc0_runtime/forest/stump_old.fbx"

var terrain: Node
var rng := RandomNumberGenerator.new()
var mat_yard: StandardMaterial3D
var mat_mud: StandardMaterial3D
var mat_wood: StandardMaterial3D
var mat_dark: StandardMaterial3D
var mat_tree: StandardMaterial3D
var mat_shrub: StandardMaterial3D
var mat_decay: StandardMaterial3D

func _ready() -> void:
 call_deferred("_build")

func _build() -> void:
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 if terrain == null or not terrain.has_method("get_height_at"):
  return
 rng.seed = 130829
 mat_yard = _mat(Color(0.047,0.060,0.030),0.99)
 mat_mud = _mat(Color(0.055,0.037,0.023),1.0)
 mat_wood = _mat(Color(0.070,0.036,0.019),0.98)
 mat_dark = _mat(Color(0.010,0.014,0.012),1.0)
 mat_tree = _mat(Color(0.024,0.047,0.020),0.98)
 mat_shrub = _mat(Color(0.035,0.064,0.025),0.99)
 mat_decay = _mat(Color(0.052,0.032,0.018),1.0)
 _parcel_yards()
 _property_edges()
 _forest_enclosure()
 _parcel_encroachment()
 _street_edge_encroachment()
 _village_verticals()
 _abandonment_marks()
 set_meta("art_status","ART-PASS-13-FOREST-ENCROACHMENT")
 set_meta("map_contract","FOREST-VILLAGE-COMPOSITION-V3")
 set_meta("visual_goal","abandoned rural settlement visibly reclaimed by forest")
 set_meta("mission_spine_clearance","preserved by deterministic exclusion")
 set_meta("mobile_validation","PENDING")

func _parcel_yards() -> void:
 for parcel: Dictionary in VillageUrbanPlan.parcels():
  var center: Vector3 = parcel.get("center",Vector3.ZERO)
  var size: Vector2 = parcel.get("size",Vector2(15.0,14.0))
  _terrain_patch(String(parcel.get("id","parcel"))+"_Yard",center,Vector2(maxf(7.0,size.x-2.0),maxf(7.0,size.y-2.0)),mat_yard,0.018)
  var dir := _front_dir(String(parcel.get("front","east")))
  var gate_pos := center + dir * minf(5.8,maxf(3.8,size.x*0.28))
  _terrain_patch(String(parcel.get("id","parcel"))+"_MudEntry",gate_pos,Vector2(3.4,5.2) if absf(dir.z)>0.5 else Vector2(5.2,3.4),mat_mud,0.026)

func _property_edges() -> void:
 for parcel: Dictionary in VillageUrbanPlan.parcels():
  var center: Vector3 = parcel.get("center",Vector3.ZERO)
  var size: Vector2 = parcel.get("size",Vector2(15.0,14.0))
  var front: String = String(parcel.get("front","east"))
  var half_x: float = size.x*0.5
  var half_z: float = size.y*0.5
  _fence_line(center+Vector3(0,0,-half_z),Vector3(size.x,0,0),front=="north")
  _fence_line(center+Vector3(0,0,half_z),Vector3(size.x,0,0),front=="south")
  _fence_line(center+Vector3(-half_x,0,0),Vector3(0,0,size.y),front=="west")
  _fence_line(center+Vector3(half_x,0,0),Vector3(0,0,size.y),front=="east")

func _forest_enclosure() -> void:
 var belt := [
  Vector3(-58,0,-50),Vector3(-46,0,-57),Vector3(-31,0,-61),Vector3(-15,0,-66),Vector3(4,0,-68),Vector3(23,0,-64),Vector3(41,0,-58),Vector3(57,0,-48),
  Vector3(-62,0,-28),Vector3(-65,0,-5),Vector3(-64,0,18),Vector3(-60,0,42),Vector3(-52,0,63),Vector3(-38,0,76),
  Vector3(62,0,-26),Vector3(65,0,-4),Vector3(64,0,19),Vector3(60,0,42),Vector3(52,0,62),Vector3(37,0,77),
  Vector3(-22,0,82),Vector3(-5,0,86),Vector3(15,0,84),Vector3(29,0,81),
  Vector3(-45,0,-39),Vector3(-48,0,-18),Vector3(-49,0,4),Vector3(-47,0,27),Vector3(-43,0,50),
  Vector3(45,0,-40),Vector3(48,0,-18),Vector3(49,0,4),Vector3(47,0,27),Vector3(43,0,50)
 ]
 for i: int in range(belt.size()):
  _plant_tree(belt[i],rng.randf_range(10.5,14.0))
  if i % 2 == 0:
   _plant_bush(belt[i]+Vector3(rng.randf_range(-3.2,3.2),0,rng.randf_range(-3.2,3.2)),rng.randf_range(1.2,2.0))

func _parcel_encroachment() -> void:
 # Back/side-yard growth is intentionally asymmetric. It brings forest into
 # the settlement while leaving each authored front/gate readable.
 for parcel: Dictionary in VillageUrbanPlan.parcels():
  var center: Vector3 = parcel.get("center",Vector3.ZERO)
  var size: Vector2 = parcel.get("size",Vector2(15.0,14.0))
  var front_dir := _front_dir(String(parcel.get("front","east")))
  var back := -front_dir
  var side := Vector3(-front_dir.z,0,front_dir.x)
  var back_dist: float = minf(6.2,maxf(4.4,maxf(size.x,size.y)*0.34))
  var candidates := [
   center+back*back_dist+side*3.2,
   center+back*(back_dist-0.8)-side*3.5,
   center+side*minf(6.0,size.x*0.36),
   center-side*minf(5.4,size.x*0.33)
  ]
  for i: int in range(candidates.size()):
   var p: Vector3 = candidates[i]
   if _clear_of_mission_spine(p,7.2):
    if i < 2:
     _plant_tree(p+Vector3(rng.randf_range(-1.0,1.0),0,rng.randf_range(-1.0,1.0)),rng.randf_range(7.5,11.2))
    _plant_bush(p+Vector3(rng.randf_range(-1.8,1.8),0,rng.randf_range(-1.8,1.8)),rng.randf_range(1.25,2.15))

func _street_edge_encroachment() -> void:
 # Irregular clumps close the long street vistas without turning the main
 # combat route into a tunnel. Keep a central ~14 m corridor readable.
 var clumps := [
  Vector3(-12,0,57),Vector3(14,0,51),Vector3(-15,0,39),Vector3(13,0,27),
  Vector3(-14,0,12),Vector3(15,0,-4),Vector3(-13,0,-22),Vector3(14,0,-39),
  Vector3(-20,0,63),Vector3(21,0,18),Vector3(-21,0,-8),Vector3(20,0,-51)
 ]
 for i: int in range(clumps.size()):
  var p: Vector3 = clumps[i]
  if _clear_of_mission_spine(p,7.0):
   if i % 3 == 0:
    _plant_tree(p,rng.randf_range(7.8,10.8))
   _plant_bush(p+Vector3(rng.randf_range(-1.3,1.3),0,rng.randf_range(-1.3,1.3)),rng.randf_range(1.4,2.4))

func _clear_of_mission_spine(p: Vector3, clearance: float) -> bool:
 # Current primary authored road follows x ~= sin(z*.018)*2.5.
 var road_x: float = sin(p.z*0.018)*2.5
 return absf(p.x-road_x) >= clearance

func _village_verticals() -> void:
 var poles := [Vector3(-9,0,48),Vector3(8,0,38),Vector3(-8,0,20),Vector3(9,0,4),Vector3(-8,0,-15),Vector3(7,0,-34)]
 for p: Vector3 in poles:
  var y := _height(p.x,p.z)
  _box("UtilityPole",Vector3(p.x,y+2.7,p.z),Vector3(0.22,5.4,0.22),mat_wood)
  _box("UtilityCrossbar",Vector3(p.x,y+5.0,p.z),Vector3(2.3,0.16,0.16),mat_dark)
  _box("LampArm",Vector3(p.x+0.62,y+4.35,p.z),Vector3(1.2,0.10,0.10),mat_dark)

func _abandonment_marks() -> void:
 var debris := [Vector3(-13,0,44),Vector3(16,0,30),Vector3(-18,0,17),Vector3(18,0,-5),Vector3(-15,0,-28)]
 for i: int in range(debris.size()):
  var p: Vector3 = debris[i]
  p.y = _height(p.x,p.z)+0.16
  _box("BrokenFence",p,Vector3(2.6,0.18,0.16),mat_wood,Vector3(0,float(i*31-22),rng.randf_range(-16,16)))
  if i % 2 == 0:
   _plant_stump(p+Vector3(1.1,0,-0.8),rng.randf_range(0.8,1.2))

func _plant_tree(p: Vector3,target: float) -> void:
 p.y = _height(p.x,p.z)+0.05
 _spawn_asset(TREE,p,Vector3(0,rng.randf_range(0,360),0),target,"composition_tree",mat_tree)

func _plant_bush(p: Vector3,target: float) -> void:
 p.y = _height(p.x,p.z)+0.04
 _spawn_asset(BUSH,p,Vector3(0,rng.randf_range(0,360),0),target,"composition_understory",mat_shrub)

func _plant_stump(p: Vector3,target: float) -> void:
 p.y = _height(p.x,p.z)+0.03
 _spawn_asset(STUMP,p,Vector3(0,rng.randf_range(0,360),0),target,"composition_decay",mat_decay)

func _front_dir(front: String) -> Vector3:
 match front:
  "west": return Vector3(-1,0,0)
  "north": return Vector3(0,0,-1)
  "south": return Vector3(0,0,1)
  _: return Vector3(1,0,0)

func _fence_line(center: Vector3, span: Vector3, leave_gate: bool) -> void:
 var length: float = maxf(absf(span.x),absf(span.z))
 var along_x: bool = absf(span.x) >= absf(span.z)
 var count: int = maxi(2,int(floor(length/2.4)))
 for i: int in range(count+1):
  var t: float = float(i)/float(count)-0.5
  if leave_gate and absf(t) < 0.15: continue
  var p := center + (Vector3(t*length,0,0) if along_x else Vector3(0,0,t*length))
  var y := _height(p.x,p.z)
  _box("FencePost",Vector3(p.x,y+0.72,p.z),Vector3(0.12,1.44,0.12),mat_wood)
  if i < count:
   var next_t: float = float(i+1)/float(count)-0.5
   if leave_gate and (absf(t)<0.15 or absf(next_t)<0.15): continue
   var mid_t: float = (t+next_t)*0.5
   var mid := center + (Vector3(mid_t*length,0,0) if along_x else Vector3(0,0,mid_t*length))
   var my := _height(mid.x,mid.z)
   var seg_len: float = length/float(count)
   var rail_size := Vector3(seg_len,0.10,0.10) if along_x else Vector3(0.10,0.10,seg_len)
   _box("FenceRail",Vector3(mid.x,my+0.82,mid.z),rail_size,mat_wood)
   _box("FenceRail",Vector3(mid.x,my+0.38,mid.z),rail_size,mat_wood)

func _terrain_patch(name_text: String, center: Vector3, size: Vector2, material: Material, offset: float) -> void:
 var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
 var hx := size.x*0.5; var hz := size.y*0.5
 var p := [Vector3(center.x-hx,0,center.z-hz),Vector3(center.x+hx,0,center.z-hz),Vector3(center.x+hx,0,center.z+hz),Vector3(center.x-hx,0,center.z+hz)]
 for i: int in range(4): p[i].y = _height(p[i].x,p[i].z)+offset
 _tri(st,p[0],p[1],p[2]); _tri(st,p[0],p[2],p[3]); st.generate_normals()
 var node := MeshInstance3D.new(); node.name=name_text; node.mesh=st.commit(); node.material_override=material
 node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; node.set_meta("art_layer","parcel_ground"); node.set_meta("terrain_grounded",true); add_child(node)

func _tri(st: SurfaceTool,a: Vector3,b: Vector3,c: Vector3) -> void:
 st.set_uv(Vector2(a.x,a.z)*0.15); st.add_vertex(a); st.set_uv(Vector2(b.x,b.z)*0.15); st.add_vertex(b); st.set_uv(Vector2(c.x,c.z)*0.15); st.add_vertex(c)

func _spawn_asset(path: String,pos: Vector3,rot: Vector3,target_extent: float,layer: String,override_material: Material) -> Node3D:
 if not ResourceLoader.exists(path): return null
 var packed := load(path) as PackedScene
 if packed == null: return null
 var node := packed.instantiate() as Node3D
 if node == null: return null
 add_child(node); node.position=pos; node.rotation_degrees=rot
 AssetScaleNormalizer.normalize_longest_extent(node,target_extent)
 node.set_meta("art_layer",layer); node.set_meta("base_visibility_end",145.0)
 _visibility_and_material(node,145.0,override_material); return node

func _visibility_and_material(node: Node,distance: float,override_material: Material) -> void:
 if node is GeometryInstance3D:
  var g:=node as GeometryInstance3D; g.visibility_range_end=distance; g.visibility_range_end_margin=7.0; g.material_override=override_material
 for child: Node in node.get_children(): _visibility_and_material(child,distance,override_material)

func _box(name_text: String,pos: Vector3,size: Vector3,material: Material,rot := Vector3.ZERO) -> MeshInstance3D:
 var node:=MeshInstance3D.new(); node.name=name_text; var mesh:=BoxMesh.new(); mesh.size=size; node.mesh=mesh; node.material_override=material; node.position=pos; node.rotation_degrees=rot
 node.visibility_range_end=120.0; node.visibility_range_end_margin=6.0; node.set_meta("art_layer","village_composition"); add_child(node); return node

func _height(x: float,z: float) -> float:
 return float(terrain.call("get_height_at",x,z))

func _mat(color: Color,roughness: float) -> StandardMaterial3D:
 var m:=StandardMaterial3D.new(); m.albedo_color=color; m.roughness=roughness; return m
