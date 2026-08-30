extends Node3D

# ART-PASS-15: organic forest silhouette proxy for visual validation.
# The current imported tree_blocks asset is useful for scale/scatter contracts but
# reads as giant cubes in gameplay captures. Hide those tree visuals and replace
# them with inexpensive trunk + clustered crown proxies until realistic audited
# tree LOD assets are promoted.

var terrain: Node
var rng := RandomNumberGenerator.new()
var trunk_mat: StandardMaterial3D
var crown_a: StandardMaterial3D
var crown_b: StandardMaterial3D
var crown_c: StandardMaterial3D

const TREE_LAYERS := {
 "canopy": true,
 "canopy_frame": true,
 "canopy_frame_polish": true,
 "composition_tree": true,
 "encroaching_tree": true,
 "roadside_tree": true
}

const TREE_POINTS := [
 Vector3(-38,0,52),Vector3(-30,0,61),Vector3(-20,0,70),Vector3(-8,0,78),Vector3(10,0,79),Vector3(23,0,72),Vector3(34,0,62),Vector3(40,0,51),
 Vector3(-42,0,39),Vector3(-36,0,28),Vector3(-39,0,16),Vector3(-35,0,3),Vector3(-39,0,-10),Vector3(-35,0,-23),Vector3(-40,0,-37),Vector3(-34,0,-49),
 Vector3(42,0,39),Vector3(36,0,28),Vector3(39,0,15),Vector3(35,0,2),Vector3(39,0,-11),Vector3(35,0,-24),Vector3(40,0,-38),Vector3(34,0,-50),
 Vector3(-26,0,45),Vector3(28,0,44),Vector3(-27,0,19),Vector3(28,0,18),Vector3(-26,0,-7),Vector3(27,0,-9),Vector3(-26,0,-33),Vector3(27,0,-34),
 Vector3(-22,0,-57),Vector3(-10,0,-64),Vector3(4,0,-66),Vector3(18,0,-61),Vector3(29,0,-55),
 Vector3(-48,0,5),Vector3(48,0,7),Vector3(-47,0,31),Vector3(47,0,32)
]

func _ready() -> void:
 call_deferred("_build")

func _build() -> void:
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 if terrain == null or not terrain.has_method("get_height_at"):
  return
 rng.seed = 150829
 trunk_mat = _mat(Color(0.075,0.044,0.025),0.98)
 crown_a = _foliage(Color(0.055,0.105,0.045),0.10)
 crown_b = _foliage(Color(0.075,0.130,0.052),0.09)
 crown_c = _foliage(Color(0.043,0.082,0.036),0.11)
 _hide_block_tree_visuals()
 for i: int in range(TREE_POINTS.size()):
  _tree(TREE_POINTS[i],i)
 set_meta("art_status","ART-PASS-15-ORGANIC-FOREST-PROXY")
 set_meta("visual_contract","ORGANIC-TREE-PROXY-V1")
 set_meta("tree_count",TREE_POINTS.size())
 set_meta("final_tree_asset",false)
 set_meta("reason","replace block-tree silhouette during map art validation")
 set_meta("mobile_validation","PENDING")

func _hide_block_tree_visuals() -> void:
 var world := get_parent()
 for node: Node in _all_nodes(world):
  if node == self or is_ancestor_of(node):
   continue
  if node is MultiMeshInstance3D and String(node.get_meta("biome_kind","")) == "tree":
   (node as MultiMeshInstance3D).visible = false
   node.set_meta("superseded_visual_by","OrganicForestProxyPass")
   continue
  if node is GeometryInstance3D:
   var layer := _effective_layer(node,world)
   if TREE_LAYERS.has(layer):
    (node as GeometryInstance3D).visible = false
    node.set_meta("superseded_visual_by","OrganicForestProxyPass")

func _tree(authored: Vector3,index: int) -> void:
 var ground_y: float = _height(authored.x,authored.z)
 var height: float = rng.randf_range(8.5,12.8)
 var trunk_h: float = height*rng.randf_range(0.44,0.55)
 var root := Node3D.new()
 root.name = "OrganicTree_%02d" % index
 root.position = Vector3(authored.x,ground_y,authored.z)
 root.rotation_degrees.y = rng.randf_range(0.0,360.0)
 root.set_meta("art_layer","organic_tree_proxy")
 root.set_meta("terrain_grounded",true)
 add_child(root)

 var trunk := MeshInstance3D.new()
 trunk.name = "Trunk"
 var trunk_mesh := CylinderMesh.new()
 trunk_mesh.top_radius = rng.randf_range(0.16,0.24)
 trunk_mesh.bottom_radius = rng.randf_range(0.28,0.40)
 trunk_mesh.height = trunk_h
 trunk_mesh.radial_segments = 7
 trunk.mesh = trunk_mesh
 trunk.material_override = trunk_mat
 trunk.position.y = trunk_h*0.5
 trunk.visibility_range_end = 155.0
 trunk.visibility_range_end_margin = 8.0
 root.add_child(trunk)

 var crown_y: float = trunk_h + height*0.12
 var spread: float = rng.randf_range(1.55,2.35)
 _crown(root,Vector3(0,crown_y,0),Vector3(spread*1.35,height*0.26,spread),crown_a)
 _crown(root,Vector3(-spread*0.55,crown_y-height*0.05,spread*0.18),Vector3(spread,height*0.22,spread*0.86),crown_b)
 _crown(root,Vector3(spread*0.52,crown_y-height*0.02,-spread*0.12),Vector3(spread*0.92,height*0.23,spread*0.82),crown_c)
 _crown(root,Vector3(0,crown_y+height*0.16,0),Vector3(spread*0.90,height*0.22,spread*0.78),crown_b)
 if index % 3 == 0:
  _crown(root,Vector3(spread*0.10,crown_y-height*0.12,spread*0.62),Vector3(spread*0.80,height*0.18,spread*0.72),crown_a)

func _crown(parent: Node3D,pos: Vector3,size: Vector3,material: Material) -> void:
 var node := MeshInstance3D.new()
 node.name = "Crown"
 var mesh := SphereMesh.new()
 mesh.radius = 1.0
 mesh.height = 2.0
 mesh.radial_segments = 8
 mesh.rings = 5
 node.mesh = mesh
 node.material_override = material
 node.position = pos
 node.scale = Vector3(size.x,size.y*0.5,size.z)
 node.rotation_degrees = Vector3(rng.randf_range(-8,8),rng.randf_range(0,180),rng.randf_range(-6,6))
 node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 node.visibility_range_end = 145.0
 node.visibility_range_end_margin = 7.0
 parent.add_child(node)

func _effective_layer(node: Node,stop: Node) -> String:
 var current: Node = node
 while current != null:
  if current.has_meta("art_layer"):
   return String(current.get_meta("art_layer",""))
  if current == stop:
   break
  current = current.get_parent()
 return ""

func _all_nodes(root: Node) -> Array[Node]:
 var out: Array[Node] = [root]
 var i: int = 0
 while i < out.size():
  var current: Node = out[i]
  for child: Node in current.get_children():
   out.append(child)
  i += 1
 return out

func _height(x: float,z: float) -> float:
 return float(terrain.call("get_height_at",x,z))

func _mat(color: Color,roughness: float) -> StandardMaterial3D:
 var m := StandardMaterial3D.new()
 m.albedo_color = color
 m.roughness = roughness
 return m

func _foliage(color: Color,energy: float) -> StandardMaterial3D:
 var m := _mat(color,0.98)
 m.emission_enabled = true
 m.emission = color
 m.emission_energy_multiplier = energy
 return m
