extends Node3D

# ART-PASS-14: readability layer for current prototype assets. Forest masses
# use a very low emissive floor only so CI/software captures preserve their
# silhouette; final foliage shading remains pending the realistic tree family.

const TREE := "res://assets/provisional/cc0_runtime/forest/tree_blocks.fbx"
const BUSH := "res://assets/provisional/cc0_runtime/forest/plant_bush.fbx"

var terrain: Node
var rng := RandomNumberGenerator.new()
var tree_mat: StandardMaterial3D
var shrub_mat: StandardMaterial3D
var wood_mat: StandardMaterial3D
var lamp_mat: StandardMaterial3D

func _ready() -> void:
 call_deferred("_build")

func _build() -> void:
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 if terrain == null or not terrain.has_method("get_height_at"):
  return
 rng.seed = 130829
 tree_mat = _foliage(Color(0.075,0.135,0.065),0.18)
 shrub_mat = _foliage(Color(0.085,0.145,0.060),0.16)
 wood_mat = _mat(Color(0.080,0.045,0.026),0.98)
 lamp_mat = _emissive(Color(0.42,0.18,0.055),Color(1.0,0.34,0.08),2.0)
 _encroach_forest()
 _roadside_growth()
 _practical_lights()
 set_meta("art_status","ART-PASS-14-FOREST-VILLAGE-READABILITY")
 set_meta("visual_contract","FOREST-ENCROACHMENT-AND-PRACTICALS-V3")
 set_meta("final_tree_asset",false)
 set_meta("mobile_validation","PENDING")

func _encroach_forest() -> void:
 var positions := [
  Vector3(-34,0,-42),Vector3(-31,0,-26),Vector3(-35,0,-8),Vector3(-33,0,12),Vector3(-36,0,33),Vector3(-32,0,54),
  Vector3(34,0,-43),Vector3(31,0,-27),Vector3(35,0,-8),Vector3(33,0,13),Vector3(36,0,33),Vector3(32,0,54),
  Vector3(-25,0,67),Vector3(24,0,69),Vector3(-19,0,-54),Vector3(20,0,-55),
  Vector3(-27,0,47),Vector3(28,0,46),Vector3(-28,0,22),Vector3(28,0,20),Vector3(-27,0,-5),Vector3(27,0,-7),Vector3(-28,0,-38),Vector3(28,0,-39)
 ]
 for i: int in range(positions.size()):
  var p: Vector3 = positions[i]
  p.y = _height(p.x,p.z)+0.04
  _spawn(TREE,p,rng.randf_range(9.5,13.2),tree_mat,"encroaching_tree")
  if i % 2 == 0:
   var b := p + Vector3(rng.randf_range(-2.8,2.8),0,rng.randf_range(-2.8,2.8))
   b.y = _height(b.x,b.z)+0.03
   _spawn(BUSH,b,rng.randf_range(1.2,1.8),shrub_mat,"encroaching_understory")

func _roadside_growth() -> void:
 var zs := [44.0,32.0,18.0,4.0,-11.0,-26.0]
 for zi: int in range(zs.size()):
  var z: float = zs[zi]
  for side in [-1.0,1.0]:
   var x: float = side*(11.5+rng.randf_range(-1.0,1.2))
   if zi in [1,4] and side > 0.0:
    continue
   var p := Vector3(x,_height(x,z)+0.03,z+rng.randf_range(-1.2,1.2))
   _spawn(BUSH,p,rng.randf_range(1.7,2.5),shrub_mat,"roadside_overgrowth")
  if zi % 2 == 0:
   var tx: float = (-1.0 if zi % 4 == 0 else 1.0)*rng.randf_range(16.0,20.0)
   var tp := Vector3(tx,_height(tx,z)+0.04,z+rng.randf_range(-2.0,2.0))
   _spawn(TREE,tp,rng.randf_range(8.5,10.5),tree_mat,"roadside_tree")

func _practical_lights() -> void:
 var lights := [Vector3(-8,0,28),Vector3(8,0,8),Vector3(-8,0,-18)]
 for i: int in range(lights.size()):
  var p: Vector3 = lights[i]
  var y := _height(p.x,p.z)
  _box("VillageLampPole",Vector3(p.x,y+2.5,p.z),Vector3(0.18,5.0,0.18),wood_mat)
  _box("VillageLampHead",Vector3(p.x,y+4.65,p.z),Vector3(0.42,0.24,0.42),lamp_mat)
  var light := OmniLight3D.new()
  light.name = "VillagePracticalLight_%02d" % i
  light.position = Vector3(p.x,y+4.45,p.z)
  light.light_color = Color(1.0,0.36,0.10,1)
  light.light_energy = 1.45 if i == 0 else 0.95
  light.omni_range = 8.5
  light.shadow_enabled = false
  add_child(light)

func _spawn(path: String,pos: Vector3,target_extent: float,material: Material,layer: String) -> Node3D:
 if not ResourceLoader.exists(path): return null
 var packed := load(path) as PackedScene
 if packed == null: return null
 var node := packed.instantiate() as Node3D
 if node == null: return null
 add_child(node)
 node.position = pos
 node.rotation_degrees.y = rng.randf_range(0,360)
 AssetScaleNormalizer.normalize_longest_extent(node,target_extent)
 node.set_meta("art_layer",layer)
 _apply_material(node,material)
 return node

func _apply_material(node: Node,material: Material) -> void:
 if node is GeometryInstance3D:
  var g := node as GeometryInstance3D
  g.material_override = material
  g.visibility_range_end = 140.0
  g.visibility_range_end_margin = 7.0
 for child: Node in node.get_children(): _apply_material(child,material)

func _box(name_text: String,pos: Vector3,size: Vector3,material: Material) -> MeshInstance3D:
 var node := MeshInstance3D.new()
 node.name = name_text
 var mesh := BoxMesh.new(); mesh.size = size
 node.mesh = mesh
 node.material_override = material
 node.position = pos
 node.visibility_range_end = 120.0
 add_child(node)
 return node

func _height(x: float,z: float) -> float:
 return float(terrain.call("get_height_at",x,z))

func _mat(color: Color,roughness: float) -> StandardMaterial3D:
 var m := StandardMaterial3D.new(); m.albedo_color = color; m.roughness = roughness; return m

func _foliage(color: Color,energy: float) -> StandardMaterial3D:
 var m := _mat(color,0.98); m.emission_enabled = true; m.emission = color; m.emission_energy_multiplier = energy; return m

func _emissive(color: Color,emission: Color,energy: float) -> StandardMaterial3D:
 var m := _mat(color,0.86); m.emission_enabled = true; m.emission = emission; m.emission_energy_multiplier = energy; return m
