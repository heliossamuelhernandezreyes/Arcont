extends Node3D

const FOREST := "res://assets/provisional/cc0_runtime/forest/"
const TREE := FOREST + "tree_blocks.fbx"
const BUSH := FOREST + "plant_bush.fbx"
const GRASS := FOREST + "grass.fbx"
const STUMP := FOREST + "stump_old.fbx"
const ROCK := FOREST + "cliff_blockCave_rock.fbx"
const CAMPFIRE := FOREST + "campfire_logs.fbx"
const BOX := "res://assets/provisional/city/box_B.fbx"
const CAR_POLICE := "res://assets/provisional/city/car_police.fbx"
const CAR_WAGON := "res://assets/provisional/city/car_stationwagon.fbx"

var rng := RandomNumberGenerator.new()
var mat_meadow: StandardMaterial3D
var mat_leaf_litter: StandardMaterial3D
var mat_mud: StandardMaterial3D
var mat_char: StandardMaterial3D
var mat_wood: StandardMaterial3D
var mat_stone: StandardMaterial3D
var mat_warm: StandardMaterial3D
var mat_cool: StandardMaterial3D
var mat_blood: StandardMaterial3D
var budget: Node

func _ready() -> void:
 rng.seed = 928741
 _materials()
 _macro_composition()
 _entrance_identities()
 _village_depth()
 _mission_landmarks()
 _forest_frames()
 _storytelling_pass()
 _lighting_pass()
 _bind_budget()
 set_meta("art_status", "ART-PASS-2-POLISHED")
 set_meta("mobile_validation", "PENDING")
 set_meta("design_rule", "macro>meso>micro")

func _materials() -> void:
 mat_meadow = _mat(Color(0.125,0.145,0.075),0.98)
 mat_leaf_litter = _mat(Color(0.105,0.072,0.040),0.99)
 mat_mud = _mat(Color(0.09,0.066,0.045),1.0)
 mat_char = _mat(Color(0.028,0.030,0.026),0.99)
 mat_wood = _mat(Color(0.17,0.095,0.045),0.94)
 mat_stone = _mat(Color(0.24,0.25,0.23),0.98)
 mat_warm = _emissive_mat(Color(0.82,0.32,0.08),Color(1.0,0.26,0.06),1.65)
 mat_cool = _emissive_mat(Color(0.08,0.18,0.22),Color(0.12,0.38,0.52),0.9)
 mat_blood = _mat(Color(0.15,0.015,0.012),0.84)

func _mat(color: Color, roughness: float) -> StandardMaterial3D:
 var m := StandardMaterial3D.new()
 m.albedo_color = color
 m.roughness = roughness
 return m

func _emissive_mat(color: Color, emission: Color, energy: float) -> StandardMaterial3D:
 var m := _mat(color,0.82)
 m.emission_enabled = true
 m.emission = emission
 m.emission_energy_multiplier = energy
 return m

func _macro_composition() -> void:
 # Transition bands prevent the settlement from looking stamped directly into a flat forest plane.
 _detail_box("MeadowSouth",Vector3(0,0.018,61),Vector3(46,0.018,20),mat_meadow,92.0,Vector3(0,4,0),"macro_transition")
 _detail_box("MeadowWest",Vector3(-35,0.017,31),Vector3(20,0.018,31),mat_meadow,84.0,Vector3(0,-7,0),"macro_transition")
 _detail_box("MeadowEast",Vector3(35,0.017,27),Vector3(18,0.018,32),mat_meadow,84.0,Vector3(0,8,0),"macro_transition")
 _detail_box("LeafLitterNorth",Vector3(-2,0.016,-55),Vector3(62,0.018,25),mat_leaf_litter,105.0,Vector3(0,5,0),"macro_transition")
 # Dark side masses create a visual tunnel that reveals the village square later rather than immediately.
 for p in [Vector3(-52,1.8,-8),Vector3(52,1.8,-10),Vector3(-54,1.6,35),Vector3(53,1.7,36)]:
  _rock_mass(p,Vector3(8.5,3.6,11.0),rng.randf_range(-22,22))
 # The northern ridge closes the skyline while leaving the bridge/supply approach readable.
 for x in [-56.0,-39.0,38.0,55.0]:
  _rock_mass(Vector3(x,2.2,-76),Vector3(13.0,4.4,9.0),rng.randf_range(-18,18))

func _entrance_identities() -> void:
 # SOUTH: evacuation approach / abandoned convoy.
 _spawn_asset(CAR_WAGON,Vector3(-8.2,0.15,69),Vector3(0,17,0),98.0,"entrance_south",4.5)
 _spawn_asset(CAR_POLICE,Vector3(7.4,0.15,62),Vector3(0,-12,0),98.0,"entrance_south",4.5)
 _detail_box("SouthRoadblockA",Vector3(-4.7,0.48,58),Vector3(4.8,0.95,0.55),mat_wood,82.0,Vector3(0,18,0),"entrance_south")
 _detail_box("SouthRoadblockB",Vector3(4.6,0.48,55),Vector3(4.1,0.95,0.55),mat_wood,82.0,Vector3(0,-23,0),"entrance_south")
 # NORTH: creek/bridge threshold, colder and more exposed.
 _detail_box("NorthMarkerL",Vector3(-11.5,1.45,-48),Vector3(0.42,2.9,0.42),mat_stone,90.0,Vector3.ZERO,"entrance_north")
 _detail_box("NorthMarkerR",Vector3(4.5,1.45,-48),Vector3(0.42,2.9,0.42),mat_stone,90.0,Vector3.ZERO,"entrance_north")
 _detail_box("NorthCrossbeam",Vector3(-3.5,2.75,-48),Vector3(16.5,0.42,0.42),mat_wood,90.0,Vector3.ZERO,"entrance_north")
 # WEST: cemetery route, tighter and ominous.
 for p in [Vector3(-44,0.12,-5),Vector3(-47,0.12,14),Vector3(-52,0.12,28)]:
  _spawn_asset(STUMP,p,Vector3(0,rng.randf_range(0,360),0),62.0,"entrance_west",rng.randf_range(0.8,1.25))
 # EAST: service path / emergency staging.
 for i in range(3):
  _spawn_asset(BOX,Vector3(39.0+float(i)*1.6,0.15,8.0+float(i%2)*1.4),Vector3(0,float(i*23),0),55.0,"entrance_east",1.0)
 _detail_box("EastSignalPost",Vector3(43,2.1,3),Vector3(0.34,4.2,0.34),mat_wood,82.0,Vector3.ZERO,"entrance_east")

func _village_depth() -> void:
 # A second meso layer around the square: porches, wood piles, service sheds and lighting anchors.
 var sheds := [
  [Vector3(-14,1.05,39),Vector3(5.4,2.1,4.2),-6.0],
  [Vector3(13.5,1.0,39),Vector3(4.8,2.0,3.8),9.0],
  [Vector3(-31,1.0,14),Vector3(4.5,2.0,5.0),84.0],
  [Vector3(31,1.0,17),Vector3(4.4,2.0,4.8),-82.0]
 ]
 for d in sheds:
  var shed := _box("VillageShed",d[0],d[1],mat_wood,true,Vector3(0,float(d[2]),0))
  shed.set_meta("art_layer","village_meso")
  shed.set_meta("budget_class","environment")
 for data in [[Vector3(-16,0.45,30),24.0],[Vector3(15,0.45,31),-19.0],[Vector3(-13,0.45,10),-12.0],[Vector3(14,0.45,12),16.0]]:
  _detail_box("WoodPile",data[0],Vector3(2.6,0.9,0.9),mat_wood,58.0,Vector3(0,float(data[1]),0),"village_meso")
 # Window glows: tiny opaque emissive planes instead of extra shadowed lights.
 for p in [Vector3(-20.5,2.8,29.6),Vector3(19.0,2.7,27.6),Vector3(-24.0,2.5,1.6),Vector3(23.0,2.6,2.5)]:
  _detail_box("WindowGlow",p,Vector3(1.25,1.0,0.08),mat_warm,48.0,Vector3.ZERO,"window_glow")
 # Square edge stones visually separate navigation/defense space from housing yards.
 for x in [-14.0,-9.5,-5.0,5.0,9.5,14.0]:
  _detail_box("SquareEdgeStone",Vector3(x,0.22,11.5),Vector3(2.8,0.44,0.55),mat_stone,65.0,Vector3(0,rng.randf_range(-5,5),0),"village_meso")

func _mission_landmarks() -> void:
 # Generator yard at MissionDirector's generator position (-8, 28).
 _detail_box("GeneratorPad",Vector3(-8,0.055,28),Vector3(7.5,0.09,6.8),mat_char,72.0,Vector3.ZERO,"mission_landmark")
 _detail_box("GeneratorHousing",Vector3(-8,1.0,28),Vector3(3.3,2.0,2.1),mat_stone,78.0,Vector3(0,14,0),"mission_landmark")
 for x in [-10.8,-5.2]:
  _detail_box("GeneratorBollard",Vector3(x,0.6,30.5),Vector3(0.42,1.2,0.42),mat_wood,58.0,Vector3.ZERO,"mission_landmark")
 # Supply point around (10,-34): readable from bridge without neon signage.
 _detail_box("SupplyDeck",Vector3(10,0.16,-34),Vector3(7.0,0.3,4.8),mat_wood,72.0,Vector3(0,-9,0),"mission_landmark")
 for i in range(4):
  _spawn_asset(BOX,Vector3(8.0+float(i%2)*2.0,0.4,-35.0+float(i/2)*1.7),Vector3(0,float(i*21),0),50.0,"mission_landmark",1.15)
 # Evac point around (0,-64): silhouette visible through north approach.
 _detail_box("EvacPostL",Vector3(-4.2,2.0,-64),Vector3(0.42,4.0,0.42),mat_stone,105.0,Vector3.ZERO,"mission_landmark")
 _detail_box("EvacPostR",Vector3(4.2,2.0,-64),Vector3(0.42,4.0,0.42),mat_stone,105.0,Vector3.ZERO,"mission_landmark")
 _detail_box("EvacBeam",Vector3(0,3.7,-64),Vector3(9.0,0.45,0.45),mat_wood,105.0,Vector3.ZERO,"mission_landmark")
 _detail_box("EvacBeacon",Vector3(0,4.15,-64),Vector3(0.5,0.5,0.5),mat_cool,105.0,Vector3.ZERO,"mission_landmark")

func _forest_frames() -> void:
 # Entrance framing groups are deterministic and intentionally asymmetric.
 var frame_trees := [
  Vector3(-18,0.08,67),Vector3(23,0.08,70),Vector3(-31,0.08,62),Vector3(35,0.08,61),
  Vector3(-22,0.08,-51),Vector3(18,0.08,-54),Vector3(-35,0.08,-57),Vector3(34,0.08,-58),
  Vector3(-48,0.08,-25),Vector3(-51,0.08,38),Vector3(49,0.08,-27),Vector3(53,0.08,37)
 ]
 for i in range(frame_trees.size()):
  _spawn_asset(TREE,frame_trees[i],Vector3(0,rng.randf_range(0,360),0),142.0,"canopy_frame_polish",rng.randf_range(9.2,12.2))
 # Low understory is kept away from the central aim corridor; it builds depth at the edges.
 var clusters := [Vector3(-58,0.08,-32),Vector3(57,0.08,-35),Vector3(-61,0.08,48),Vector3(60,0.08,50),Vector3(-38,0.08,76),Vector3(39,0.08,79)]
 for center in clusters:
  for j in range(5):
   var offset := Vector3(rng.randf_range(-4.5,4.5),0,rng.randf_range(-4.5,4.5))
   _spawn_asset(BUSH,center+offset,Vector3(0,rng.randf_range(0,360),0),58.0,"understory_polish",rng.randf_range(1.0,1.65))
  for j in range(5):
   var offset := Vector3(rng.randf_range(-5.2,5.2),0,rng.randf_range(-5.2,5.2))
   _spawn_asset(GRASS,center+offset,Vector3(0,rng.randf_range(0,360),0),38.0,"ground_polish",rng.randf_range(0.6,1.0))

func _storytelling_pass() -> void:
 # Retreat sequence: south roadblock -> wounded trail -> generator defense -> north evac failure.
 for d in [[Vector3(3.0,0.036,48),Vector3(0.6,0.015,2.0),18.0],[Vector3(0.8,0.036,43),Vector3(0.5,0.015,1.6),9.0],[Vector3(-3.0,0.036,36),Vector3(0.55,0.015,1.9),-12.0]]:
  _detail_box("RetreatBlood",d[0],d[1],mat_blood,42.0,Vector3(0,float(d[2]),0),"story_chain")
 _detail_box("BurnedCartBody",Vector3(5.5,0.75,20),Vector3(3.8,1.3,2.1),mat_char,65.0,Vector3(0,-28,8),"story_chain")
 _detail_box("BurnedCartAxle",Vector3(5.5,0.6,20),Vector3(4.7,0.25,0.25),mat_stone,55.0,Vector3(0,-28,0),"story_chain")
 _spawn_asset(CAMPFIRE,Vector3(5.5,0.15,20),Vector3(0,15,0),52.0,"story_chain",1.7)
 # A failed barricade at extraction gives the northern endpoint narrative closure.
 _detail_box("EvacBarricadeL",Vector3(-6,0.48,-58),Vector3(4.6,0.95,0.55),mat_wood,74.0,Vector3(0,24,0),"story_chain")
 _detail_box("EvacBarricadeR",Vector3(6,0.48,-59),Vector3(4.6,0.95,0.55),mat_wood,74.0,Vector3(0,-18,0),"story_chain")
 for p in [Vector3(-2,0.025,-59),Vector3(1.8,0.025,-61)]:
  _detail_box("EvacScorch",p,Vector3(2.6,0.018,3.2),mat_char,48.0,Vector3(0,rng.randf_range(-20,20),0),"story_chain")

func _lighting_pass() -> void:
 # Only three polish lights; all unshadowed. Moon remains the single expensive shadowed key.
 _accent_light("SquareFireLight",Vector3(5.5,2.2,20),Color(1.0,0.29,0.08),1.45,8.0)
 _accent_light("BridgeColdLight",Vector3(-4,2.4,-35),Color(0.16,0.34,0.43),0.85,9.0)
 _accent_light("EvacColdLight",Vector3(0,4.3,-64),Color(0.10,0.38,0.58),1.2,10.0)

func _accent_light(name_text: String, pos: Vector3, color: Color, energy: float, radius: float) -> void:
 var light := OmniLight3D.new()
 light.name = name_text
 light.position = pos
 light.light_color = color
 light.light_energy = energy
 light.omni_range = radius
 light.shadow_enabled = false
 light.set_meta("art_layer","accent_light")
 light.set_meta("budget_class","vfx_light")
 add_child(light)

func _rock_mass(pos: Vector3, size: Vector3, yaw: float) -> void:
 var rock := _box("RockMass",pos,size,mat_stone,true,Vector3(rng.randf_range(-5,5),yaw,rng.randf_range(-4,4)))
 rock.set_meta("art_layer","macro_occluder")
 rock.set_meta("budget_class","environment")
 rock.set_meta("base_visibility_end",145.0)
 rock.visibility_range_end = 145.0

func _spawn_asset(path: String, pos: Vector3, rot: Vector3, visibility: float, layer: String, target_extent: float) -> Node3D:
 if not ResourceLoader.exists(path):
  return null
 var packed := load(path) as PackedScene
 if packed == null:
  return null
 var node := packed.instantiate() as Node3D
 if node == null:
  return null
 add_child(node)
 node.position = pos
 node.rotation_degrees = rot
 AssetScaleNormalizer.normalize_longest_extent(node,target_extent)
 node.set_meta("art_layer",layer)
 node.set_meta("budget_class","prop" if layer in ["understory_polish","ground_polish","story_chain"] else "environment")
 node.set_meta("base_visibility_end",visibility)
 _visibility_recursive(node,visibility,layer)
 return node

func _visibility_recursive(node: Node, distance: float, layer: String) -> void:
 if node is GeometryInstance3D:
  var g := node as GeometryInstance3D
  g.visibility_range_end = distance
  g.visibility_range_end_margin = minf(7.0,distance*0.08)
  g.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
  if layer in ["understory_polish","ground_polish","story_chain"]:
   g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 for child in node.get_children():
  _visibility_recursive(child,distance,layer)

func _box(name_text: String, pos: Vector3, size: Vector3, material: Material, collision: bool, rot := Vector3.ZERO) -> MeshInstance3D:
 var node := MeshInstance3D.new()
 node.name = name_text
 var mesh := BoxMesh.new()
 mesh.size = size
 node.mesh = mesh
 node.material_override = material
 node.position = pos
 node.rotation_degrees = rot
 add_child(node)
 if collision:
  _collision_box(name_text+"Collision",pos,size,rot)
 return node

func _detail_box(name_text: String, pos: Vector3, size: Vector3, material: Material, visibility: float, rot := Vector3.ZERO, layer := "detail") -> MeshInstance3D:
 var node := _box(name_text,pos,size,material,false,rot)
 node.set_meta("art_layer",layer)
 node.set_meta("budget_class","prop")
 node.set_meta("base_visibility_end",visibility)
 node.visibility_range_end = visibility
 node.visibility_range_end_margin = minf(6.0,visibility*0.08)
 node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 return node

func _collision_box(name_text: String, pos: Vector3, size: Vector3, rot := Vector3.ZERO) -> void:
 var body := StaticBody3D.new()
 body.name = name_text
 body.position = pos
 body.rotation_degrees = rot
 var shape_node := CollisionShape3D.new()
 var shape := BoxShape3D.new()
 shape.size = size
 shape_node.shape = shape
 body.add_child(shape_node)
 add_child(body)

func _bind_budget() -> void:
 budget = get_parent().get_node_or_null("PerformanceBudget")
 if budget == null:
  return
 if budget.has_signal("visual_budget_changed"):
  budget.visual_budget_changed.connect(_on_visual_budget_changed)
 if budget.has_method("get_visibility_scale"):
  _apply_budget(float(budget.get_visibility_scale()),float(budget.get_prop_scale()))

func _on_visual_budget_changed(_tier: int, visibility_scale: float, prop_scale: float, _enemy_detail: float) -> void:
 _apply_budget(visibility_scale,prop_scale)

func _apply_budget(visibility_scale: float, prop_scale: float) -> void:
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
   geometry.visibility_range_end = maxf(20.0,base*factor)
 for child in node.get_children():
  _apply_budget_recursive(child,visibility_scale,prop_scale)
