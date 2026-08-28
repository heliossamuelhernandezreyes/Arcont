extends Node3D

const FOREST := "res://assets/provisional/cc0_runtime/forest/"
const TREE := FOREST + "tree_blocks.fbx"
const BUSH := FOREST + "plant_bush.fbx"
const GRASS := FOREST + "grass.fbx"
const STUMP := FOREST + "stump_old.fbx"
const ROCK := FOREST + "cliff_blockCave_rock.fbx"
const BRIDGE := FOREST + "bridge_center_stone.fbx"
const CAMPFIRE := FOREST + "campfire_logs.fbx"
const BUILDINGS := [
 "res://assets/provisional/city/building_A.fbx",
 "res://assets/provisional/city/building_B.fbx",
 "res://assets/provisional/city/building_C.fbx",
 "res://assets/provisional/city/building_D.fbx"
]
const CARS := [
 "res://assets/provisional/city/car_hatchback.fbx",
 "res://assets/provisional/city/car_police.fbx",
 "res://assets/provisional/city/car_sedan.fbx"
]
const BOX := "res://assets/provisional/city/box_A.fbx"

@export var world_size := Vector2(170.0, 220.0)
@export var seed := 73191
@export var tree_count := 108
@export var bush_count := 68
@export var grass_count := 88

var rng := RandomNumberGenerator.new()
var budget: Node
var mat_soil: StandardMaterial3D
var mat_path: StandardMaterial3D
var mat_path_dark: StandardMaterial3D
var mat_water: StandardMaterial3D
var mat_wood: StandardMaterial3D
var mat_stone: StandardMaterial3D
var mat_roof: StandardMaterial3D
var mat_dark: StandardMaterial3D
var mat_blood: StandardMaterial3D
var mat_grass: StandardMaterial3D
var mat_marker: StandardMaterial3D

func _ready() -> void:
 rng.seed = seed
 _materials()
 _ground_and_paths()
 _village()
 _tactical_routes()
 _forest_mass()
 _forest_detail()
 _story_props()
 _boundaries()
 _spawn_points()
 _bind_budget()
 set_meta("art_status", "ART-PASS-2")
 set_meta("environment_type", "forest_village")
 set_meta("mobile_validation", "PENDING")

func _materials() -> void:
 mat_soil = _mat(Color(0.095,0.088,0.058),0.98)
 mat_path = _mat(Color(0.255,0.205,0.132),0.97)
 mat_path_dark = _mat(Color(0.145,0.118,0.077),0.99)
 mat_water = _mat(Color(0.045,0.125,0.145),0.50)
 mat_wood = _mat(Color(0.19,0.115,0.055),0.94)
 mat_stone = _mat(Color(0.235,0.245,0.235),0.98)
 mat_roof = _mat(Color(0.18,0.062,0.046),0.92)
 mat_dark = _mat(Color(0.038,0.047,0.041),0.99)
 mat_blood = _mat(Color(0.16,0.018,0.015),0.85)
 mat_grass = _mat(Color(0.105,0.145,0.065),0.99)
 mat_marker = _mat(Color(0.52,0.30,0.06),0.88)

func _mat(color: Color, roughness: float) -> StandardMaterial3D:
 var material := StandardMaterial3D.new()
 material.albedo_color = color
 material.roughness = roughness
 return material

func _ground_and_paths() -> void:
 _box("ForestGround",Vector3(0,-0.22,0),Vector3(world_size.x,0.4,world_size.y),mat_soil,true)
 # Large readable shapes first: main road, two flank tracks, stream seam and village apron.
 _box("SouthRoad",Vector3(-2,0.01,70),Vector3(9,0.035,80),mat_path,false,Vector3(0,5,0))
 _box("VillageRoad",Vector3(1,0.012,5),Vector3(10,0.038,72),mat_path,false,Vector3(0,-8,0))
 _box("NorthRoad",Vector3(-4,0.01,-69),Vector3(8,0.035,72),mat_path,false,Vector3(0,7,0))
 _box("WestTrack",Vector3(-31,0.012,4),Vector3(54,0.03,5.5),mat_path_dark,false,Vector3(0,-8,0))
 _box("EastTrack",Vector3(31,0.012,-7),Vector3(52,0.03,5.0),mat_path_dark,false,Vector3(0,12,0))
 _box("VillageApron",Vector3(0,0.014,23),Vector3(39,0.035,34),mat_path,false)
 # Stream banks make the water read as a terrain cut rather than a blue stripe.
 _box("Stream",Vector3(-37,-0.03,-40),Vector3(72,0.08,5.5),mat_water,false,Vector3(0,-7,0))
 _detail_box("StreamBankA",Vector3(-37,0.015,-36.8),Vector3(73,0.04,1.25),mat_dark,100.0,Vector3(0,-7,0),"terrain_detail")
 _detail_box("StreamBankB",Vector3(-37,0.015,-43.1),Vector3(73,0.04,1.25),mat_dark,100.0,Vector3(0,-7,0),"terrain_detail")
 _spawn_asset(BRIDGE,Vector3(-4,0.12,-35),Vector3(0,83,0),125.0,"landmark",7.0)
 # Worn wheel ruts pull the eye through the settlement.
 for d in [[-1.8,66.0,5.0],[2.1,41.0,-8.0],[-1.4,4.0,-8.0],[0.8,-24.0,7.0],[3.0,-62.0,7.0]]:
  _detail_box("WheelRut",Vector3(float(d[0]),0.033,float(d[1])),Vector3(0.28,0.018,13.0),mat_path_dark,72.0,Vector3(0,float(d[2]),0),"road_wear")

func _village() -> void:
 var homes := [
  [Vector3(-22,0.12,-20),16.0,0],[Vector3(20,0.12,-23),-18.0,1],
  [Vector3(-25,0.12,8),-8.0,2],[Vector3(24,0.12,9),12.0,3],
  [Vector3(-20,0.12,35),18.0,1],[Vector3(20,0.12,34),-14.0,0],
  [Vector3(-37,0.12,25),80.0,3],[Vector3(37,0.12,-2),96.0,2]
 ]
 for data in homes:
  var pos: Vector3 = data[0]
  var yaw := float(data[1])
  _spawn_asset(BUILDINGS[int(data[2])],pos,Vector3(0,yaw,0),175.0,"village",13.5)
  _collision_box("HouseCollision",pos+Vector3(0,3.6,0),Vector3(11.5,7.2,11.5),Vector3(0,yaw,0))
  _yard_frame(pos,yaw)
 # Central square and bell tower form the dominant silhouette/focal point.
 _box("VillageSquare",Vector3(0,0.025,24),Vector3(31,0.055,26),mat_path,false)
 _box("BellTowerBase",Vector3(-9,2.5,22),Vector3(5.5,5.0,5.5),mat_stone,true)
 _box("BellTowerTop",Vector3(-9,6.0,22),Vector3(3.4,2.2,3.4),mat_stone,true)
 _roof("BellTowerRoof",Vector3(-9,7.55,22),Vector3(5.0,1.6,5.0))
 _detail_box("BellTowerDoor",Vector3(-9,1.25,19.2),Vector3(1.3,2.5,0.18),mat_dark,85.0,Vector3.ZERO,"landmark_detail")
 _build_well()
 # Asymmetric cover: each approach has a different silhouette and flank opening.
 var cover_data := [
  [Vector3(-5.6,0.55,31),22.0,Vector3(3.2,1.1,0.8)],
  [Vector3(5.7,0.55,28),-31.0,Vector3(2.7,1.1,0.8)],
  [Vector3(-4.0,0.55,15),-18.0,Vector3(2.4,1.1,0.72)],
  [Vector3(7.0,0.55,17),28.0,Vector3(3.0,1.1,0.72)],
  [Vector3(12.0,0.55,23),82.0,Vector3(2.8,1.1,0.72)],
  [Vector3(-13.0,0.55,27),96.0,Vector3(2.5,1.1,0.72)]
 ]
 for d in cover_data:
  var cover := _box("VillageCover",d[0],d[2],mat_wood,true,Vector3(0,float(d[1]),0))
  cover.set_meta("art_layer","tactical_cover")
 for i in range(6):
  _spawn_asset(BOX,Vector3(-7.0+i*2.9,0.15,35.0+float(i%2)),Vector3(0,float(i*29),0),58.0,"prop",1.0)
 # Evacuation traces; still sparse enough to remain a village.
 _spawn_asset(CARS[1],Vector3(7,0.15,-10),Vector3(0,-18,0),95.0,"vehicle",4.5)
 _spawn_asset(CARS[0],Vector3(-8,0.15,51),Vector3(0,12,0),95.0,"vehicle",4.5)
 _spawn_asset(CARS[2],Vector3(30,0.15,44),Vector3(0,76,0),90.0,"vehicle",4.5)

func _yard_frame(pos: Vector3, yaw: float) -> void:
 # Low fragmented fences visually explain property boundaries while preserving combat access.
 var side := -1.0 if pos.x < 0.0 else 1.0
 var fence_pos := pos + Vector3(-side*6.0,0.52,4.5)
 var fence := _detail_box("YardFence",fence_pos,Vector3(7.0,1.0,0.16),mat_wood,68.0,Vector3(0,yaw+8.0*side,0),"village_meso")
 fence.set_meta("budget_class","prop")

func _build_well() -> void:
 var well := MeshInstance3D.new()
 well.name = "VillageWell"
 var cylinder := CylinderMesh.new()
 cylinder.top_radius = 1.25
 cylinder.bottom_radius = 1.35
 cylinder.height = 0.85
 cylinder.radial_segments = 12
 well.mesh = cylinder
 well.material_override = mat_stone
 well.position = Vector3(7.5,0.44,23.5)
 well.set_meta("art_layer","landmark_detail")
 well.set_meta("budget_class","environment")
 well.set_meta("base_visibility_end",90.0)
 add_child(well)
 _collision_box("VillageWellCollision",well.position,Vector3(2.5,0.9,2.5))

func _tactical_routes() -> void:
 # Explicit meso layer: six readable approach/flank gates into the village.
 var route_marks := [
  [Vector3(-31,0.03,-18),Vector3(18,0.025,3.6),-11.0],
  [Vector3(30,0.03,-22),Vector3(20,0.025,3.6),14.0],
  [Vector3(-34,0.03,18),Vector3(17,0.025,3.5),8.0],
  [Vector3(34,0.03,18),Vector3(17,0.025,3.5),-10.0],
  [Vector3(-26,0.03,49),Vector3(17,0.025,3.4),-16.0],
  [Vector3(27,0.03,48),Vector3(17,0.025,3.4),17.0]
 ]
 for d in route_marks:
  _detail_box("TacticalRoute",d[0],d[1],mat_path_dark,74.0,Vector3(0,float(d[2]),0),"tactical_route")
 # Route mouths get low stone/wood silhouettes, leaving clear openings between them.
 for data in [[Vector3(-39,0.48,-13),18.0],[Vector3(39,0.48,-17),-14.0],[Vector3(-42,0.48,24),-9.0],[Vector3(42,0.48,22),11.0],[Vector3(-33,0.48,54),19.0],[Vector3(34,0.48,53),-18.0]]:
  var gate_cover := _detail_box("RouteMouthCover",data[0],Vector3(4.6,0.95,0.55),mat_stone,92.0,Vector3(0,float(data[1]),0),"tactical_cover")
  gate_cover.set_meta("budget_class","environment")

func _forest_mass() -> void:
 # Four independent forest sectors give coarse spatial culling now and a clean MultiMesh/HLOD conversion path later.
 var chunks := [Vector2(-55,-65),Vector2(55,-65),Vector2(-55,62),Vector2(55,62)]
 var per_chunk := maxi(tree_count/chunks.size(),1)
 for chunk_index in range(chunks.size()):
  var chunk := Node3D.new()
  chunk.name = "ForestChunk_%02d" % chunk_index
  chunk.set_meta("art_layer","forest_chunk")
  add_child(chunk)
  var center: Vector2 = chunks[chunk_index]
  for i in range(per_chunk):
   var pos := Vector3(center.x+rng.randf_range(-29,29),0.08,center.y+rng.randf_range(-39,39))
   if _reserved_clearance(pos):
    continue
   var distance_to_village := Vector2(pos.x,pos.z-18.0).length()
   var target_height := rng.randf_range(9.0,13.2) if distance_to_village > 55.0 else rng.randf_range(8.0,11.0)
   var tree := _spawn_asset_to(chunk,TREE,pos,Vector3(0,rng.randf_range(0,360),0),150.0,"canopy",target_height)
   if tree:
    tree.set_meta("forest_chunk",chunk_index)
 # Hand-placed threshold trees frame entrances and hide the square until the final approach.
 for p in [Vector3(-45,0.08,-45),Vector3(43,0.08,-48),Vector3(-48,0.08,47),Vector3(47,0.08,46),Vector3(-22,0.08,73),Vector3(22,0.08,75)]:
  _spawn_asset(TREE,p,Vector3(0,rng.randf_range(0,360),0),145.0,"canopy_frame",rng.randf_range(9.0,11.5))

func _forest_detail() -> void:
 for i in range(bush_count):
  var p := _random_outer_position()
  if not _reserved_clearance(p):
   _spawn_asset(BUSH,p,Vector3(0,rng.randf_range(0,360),0),68.0,"understory",rng.randf_range(1.1,1.85))
 for i in range(grass_count):
  var p := _random_outer_position()
  if not _reserved_clearance(p):
   _spawn_asset(GRASS,p,Vector3(0,rng.randf_range(0,360),0),42.0,"ground_detail",rng.randf_range(0.62,1.12))
 for i in range(18):
  var p := _random_outer_position()
  if not _reserved_clearance(p):
   _spawn_asset(STUMP,p,Vector3(0,rng.randf_range(0,360),0),64.0,"prop",rng.randf_range(0.7,1.2))
 for p in [Vector3(-57,0,-18),Vector3(54,0,19),Vector3(-49,0,58),Vector3(48,0,-62),Vector3(-63,0,-72),Vector3(61,0,72),Vector3(-69,0,18),Vector3(67,0,-5)]:
  _spawn_asset(ROCK,p,Vector3(0,rng.randf_range(0,360),0),145.0,"landform",rng.randf_range(7.0,11.5))
 # Ground-value breakup around the forest edge keeps the soil from reading as a single flat slab.
 for p in [Vector3(-57,0.018,-51),Vector3(59,0.018,-37),Vector3(-62,0.018,41),Vector3(56,0.018,56),Vector3(-28,0.018,74),Vector3(30,0.018,77)]:
  _detail_box("ForestMossPatch",p,Vector3(9.0,0.018,7.0),mat_grass,70.0,Vector3(0,rng.randf_range(0,180),0),"ground_story")

func _story_props() -> void:
 for p in [Vector3(11,0.12,25),Vector3(-31,0.12,-4),Vector3(23,0.12,-50)]:
  _spawn_asset(CAMPFIRE,p,Vector3(0,rng.randf_range(0,360),0),62.0,"story_prop",2.0)
  var glow := OmniLight3D.new()
  glow.position = p+Vector3(0,1.1,0)
  glow.light_color = Color(1.0,0.31,0.08)
  glow.light_energy = 1.75
  glow.omni_range = 7.0
  glow.shadow_enabled = false
  glow.set_meta("budget_class","vfx_light")
  add_child(glow)
 # Fallen barricades, scorch marks, blood and abandoned belongings imply a failed retreat.
 for data in [[Vector3(-2,0.25,5),18.0],[Vector3(5,0.25,44),-24.0],[Vector3(-6,0.25,-18),31.0],[Vector3(27,0.25,-28),74.0]]:
  var barricade := _box("FallenBarricade",data[0],Vector3(3.2,0.5,0.55),mat_wood,true,Vector3(0,float(data[1]),0))
  barricade.set_meta("art_layer","story_prop")
 for p in [Vector3(2,0.025,12),Vector3(-4,0.025,40),Vector3(5,0.025,-22),Vector3(25,0.025,-29)]:
  _detail_box("ScorchedGround",p,Vector3(3.2,0.018,4.5),mat_dark,50.0,Vector3(0,rng.randf_range(-25,25),0),"story_prop")
 for d in [[Vector3(3.5,0.037,14.0),Vector3(0.8,0.015,2.4),12.0],[Vector3(2.8,0.037,11.8),Vector3(0.5,0.015,1.7),26.0],[Vector3(-5.0,0.037,-28.0),Vector3(0.7,0.015,2.0),-16.0]]:
  _detail_box("BloodTrail",d[0],d[1],mat_blood,42.0,Vector3(0,float(d[2]),0),"story_prop")
 _build_cemetery()

func _build_cemetery() -> void:
 # Quiet secondary landmark, useful for orientation and a future encounter pocket.
 var origin := Vector3(-48,0.0,5)
 for row in range(3):
  for col in range(4):
   var pos := origin+Vector3(float(col)*2.1,0.6,float(row)*2.8)
   var grave := _detail_box("GraveStone",pos,Vector3(0.75,1.2,0.22),mat_stone,78.0,Vector3(0,rng.randf_range(-6,6),0),"story_prop")
   grave.set_meta("budget_class","prop")
 _detail_box("CemeteryWall",origin+Vector3(3.1,0.5,-2.0),Vector3(10.5,1.0,0.42),mat_stone,96.0,Vector3.ZERO,"landmark_detail")

func _reserved_clearance(pos: Vector3) -> bool:
 # Protect aim lanes, village core, stream crossing and main road from random vegetation.
 if absf(pos.x) < 43.0 and pos.z > -48.0 and pos.z < 58.0:
  return true
 if absf(pos.x) < 9.5:
  return true
 if pos.distance_to(Vector3(-4,0,-35)) < 11.0:
  return true
 return false

func _random_outer_position() -> Vector3:
 return Vector3(rng.randf_range(-78,78),0.08,rng.randf_range(-102,102))

func _boundaries() -> void:
 var hx := world_size.x*0.5
 var hz := world_size.y*0.5
 _collision_box("BoundaryN",Vector3(0,2,-hz),Vector3(world_size.x,4,1))
 _collision_box("BoundaryS",Vector3(0,2,hz),Vector3(world_size.x,4,1))
 _collision_box("BoundaryW",Vector3(-hx,2,0),Vector3(1,4,world_size.y))
 _collision_box("BoundaryE",Vector3(hx,2,0),Vector3(1,4,world_size.y))

func _spawn_points() -> void:
 var points := [
  Vector3(-60,0.2,-78),Vector3(58,0.2,-75),Vector3(-66,0.2,-20),Vector3(65,0.2,-15),
  Vector3(-62,0.2,55),Vector3(61,0.2,60),Vector3(-25,0.2,82),Vector3(26,0.2,85),
  Vector3(-5,0.2,-88),Vector3(4,0.2,92)
 ]
 for i in range(points.size()):
  var marker := Marker3D.new()
  marker.name = "ForestSpawn_%02d" % i
  marker.position = points[i]
  marker.add_to_group("enemy_spawn")
  add_child(marker)

func _spawn_asset(path: String, pos: Vector3, rot: Vector3, visibility: float, layer: String, target_extent: float) -> Node3D:
 return _spawn_asset_to(self,path,pos,rot,visibility,layer,target_extent)

func _spawn_asset_to(parent: Node3D, path: String, pos: Vector3, rot: Vector3, visibility: float, layer: String, target_extent: float) -> Node3D:
 if not ResourceLoader.exists(path):
  return null
 var packed := load(path) as PackedScene
 if packed == null:
  return null
 var node := packed.instantiate() as Node3D
 if node == null:
  return null
 parent.add_child(node)
 node.global_position = pos
 node.rotation_degrees = rot
 AssetScaleNormalizer.normalize_longest_extent(node,target_extent)
 _set_visibility_recursive(node,visibility,layer)
 node.set_meta("art_layer",layer)
 node.set_meta("budget_class","prop" if layer in ["understory","ground_detail","prop","story_prop"] else "environment")
 node.set_meta("base_visibility_end",visibility)
 return node

func _set_visibility_recursive(node: Node, distance: float, layer: String) -> void:
 if node is GeometryInstance3D:
  var geometry := node as GeometryInstance3D
  geometry.visibility_range_end = distance
  geometry.visibility_range_end_margin = minf(8.0,distance*0.08)
  geometry.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
  if layer in ["ground_detail","understory"]:
   geometry.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 for child in node.get_children():
  _set_visibility_recursive(child,distance,layer)

func _box(name_text: String, pos: Vector3, size: Vector3, material: Material, collision: bool, rot := Vector3.ZERO) -> MeshInstance3D:
 var mesh_node := MeshInstance3D.new()
 mesh_node.name = name_text
 var mesh := BoxMesh.new()
 mesh.size = size
 mesh_node.mesh = mesh
 mesh_node.material_override = material
 mesh_node.position = pos
 mesh_node.rotation_degrees = rot
 mesh_node.set_meta("art_layer",name_text)
 add_child(mesh_node)
 if collision:
  _collision_box(name_text+"Collision",pos,size,rot)
 return mesh_node

func _detail_box(name_text: String, pos: Vector3, size: Vector3, material: Material, visibility: float, rot := Vector3.ZERO, layer := "detail") -> MeshInstance3D:
 var node := _box(name_text,pos,size,material,false,rot)
 node.set_meta("art_layer",layer)
 node.set_meta("budget_class","prop")
 node.set_meta("base_visibility_end",visibility)
 node.visibility_range_end = visibility
 node.visibility_range_end_margin = minf(6.0,visibility*0.08)
 node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 return node

func _roof(name_text: String, pos: Vector3, size: Vector3) -> void:
 var roof := _box(name_text,pos,size,mat_roof,false,Vector3(0,45,0))
 roof.scale = Vector3(1.0,0.55,1.0)
 roof.set_meta("art_layer","landmark_detail")

func _collision_box(name_text: String, pos: Vector3, size: Vector3, rot := Vector3.ZERO) -> void:
 var body := StaticBody3D.new()
 body.name = name_text
 body.position = pos
 body.rotation_degrees = rot
 var shape := CollisionShape3D.new()
 var box := BoxShape3D.new()
 box.size = size
 shape.shape = box
 body.add_child(shape)
 add_child(body)

func _bind_budget() -> void:
 budget = get_parent().get_node_or_null("PerformanceBudget")
 if budget == null:
  return
 if budget.has_signal("visual_budget_changed"):
  budget.visual_budget_changed.connect(_on_visual_budget_changed)
 if budget.has_method("get_visibility_scale"):
  _apply_visibility(float(budget.get_visibility_scale()),float(budget.get_prop_scale()))

func _on_visual_budget_changed(_tier: int, visibility_scale: float, prop_scale: float, _enemy_detail: float) -> void:
 _apply_visibility(visibility_scale,prop_scale)

func _apply_visibility(visibility_scale: float, prop_scale: float) -> void:
 for child in get_children():
  _apply_budget_recursive(child,visibility_scale,prop_scale)

func _apply_budget_recursive(node: Node, visibility_scale: float, prop_scale: float) -> void:
 if node is GeometryInstance3D:
  var geometry := node as GeometryInstance3D
  var owner: Node = node
  while owner != null and not owner.has_meta("base_visibility_end"):
   owner = owner.get_parent()
  if owner != null:
   var base := float(owner.get_meta("base_visibility_end"))
   var factor := prop_scale if String(owner.get_meta("budget_class","environment")) == "prop" else visibility_scale
   geometry.visibility_range_end = maxf(22.0,base*factor)
 for child in node.get_children():
  _apply_budget_recursive(child,visibility_scale,prop_scale)
