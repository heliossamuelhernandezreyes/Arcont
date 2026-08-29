class_name ModularHouseBuilder
extends RefCounted

# ART-PASS-9: reusable metric architecture assembled from shared primitive modules.
# This is a visual grammar, not a structural-engineering simulator.

static func build(parent: Node3D, world_pos: Vector3, yaw_deg: float, archetype: int, materials: Dictionary) -> Node3D:
 var root := Node3D.new()
 root.name = "ModularHouse_%02d" % archetype
 root.position = world_pos
 root.rotation_degrees.y = yaw_deg
 root.set_meta("art_layer", "village")
 root.set_meta("architecture_contract", "MODULAR-HOUSE-V1")
 root.set_meta("terrain_grounded", true)
 root.set_meta("archetype", archetype)
 root.set_meta("construction_logic", "plinth>wall_bays>openings>roof>trim>porch>utilities")
 parent.add_child(root)

 var wall: Material = materials["wall"]
 var wall_alt: Material = materials["wall_alt"]
 var roof: Material = materials["roof"]
 var wood: Material = materials["wood"]
 var stone: Material = materials["stone"]
 var dark: Material = materials["dark"]
 var glass: Material = materials["glass"]

 var width: float = float([8.8, 10.2, 9.6, 10.8, 8.4, 10.6, 11.2, 9.8][archetype % 8])
 var depth: float = float([7.2, 8.2, 8.6, 8.0, 7.5, 8.8, 8.4, 9.0][archetype % 8])
 var floors: int = 2 if archetype % 8 in [4, 5] else 1
 var floor_h: float = 2.85
 var body_h: float = floor_h * float(floors)

 _piece(root, "Foundation", Vector3(0, 0.18, 0), Vector3(width + 0.35, 0.36, depth + 0.35), stone)
 _piece(root, "FloorSlab", Vector3(0, 0.42, 0), Vector3(width, 0.18, depth), wood)

 # Four enclosure walls. Front is assembled around openings rather than a single slab.
 _piece(root, "RearWall", Vector3(0, 0.48 + body_h * 0.5, depth * 0.5), Vector3(width, body_h, 0.24), wall)
 _piece(root, "LeftWall", Vector3(-width * 0.5, 0.48 + body_h * 0.5, 0), Vector3(0.24, body_h, depth), wall_alt)
 _piece(root, "RightWall", Vector3(width * 0.5, 0.48 + body_h * 0.5, 0), Vector3(0.24, body_h, depth), wall_alt)

 var door_x: float = -width * 0.18 if archetype % 2 == 0 else width * 0.17
 _front_facade(root, width, body_h, floor_h, floors, door_x, wall, wood, dark, glass)

 if archetype % 8 in [1, 6]:
  _side_addition(root, width, depth, wall_alt, roof, dark, glass)
 if archetype % 8 in [0, 2, 3, 7]:
  _porch(root, width, depth, wood, roof)
 if archetype % 8 == 5:
  _shopfront(root, width, depth, wall, dark, glass, roof)

 if archetype % 8 in [3, 7]:
  _hip_roof(root, width, depth, body_h + 0.55, roof)
 else:
  _gable_roof(root, width, depth, body_h + 0.55, roof)

 # Cheap architectural depth/details with finite visibility inherited by the parent budget pass.
 _piece(root, "Chimney", Vector3(width * 0.28, body_h + 1.65, depth * 0.12), Vector3(0.62, 2.0, 0.62), stone)
 _piece(root, "UtilityMeter", Vector3(width * 0.5 + 0.16, 1.25, depth * 0.12), Vector3(0.16, 0.55, 0.42), dark)
 _piece(root, "Downspout", Vector3(width * 0.5 + 0.13, 1.55, -depth * 0.36), Vector3(0.12, 2.7, 0.12), dark)
 return root

static func _front_facade(root: Node3D, width: float, body_h: float, floor_h: float, floors: int, door_x: float, wall: Material, wood: Material, dark: Material, glass: Material) -> void:
 var z: float = -float(root.get_meta("dummy_depth", 0.0))
 # caller dimensions are recovered from side-wall placement; use child geometry AABB-independent metadata.
 var depth: float = 0.0
 for child in root.get_children():
  if child.name == "LeftWall" and child is MeshInstance3D:
   depth = (child.mesh as BoxMesh).size.z
 z = -depth * 0.5
 var door_w: float = 1.05
 var door_h: float = 2.15
 var side_w: float = maxf(0.5, (width - door_w) * 0.5)
 _piece(root, "FrontWallL", Vector3(-width * 0.5 + side_w * 0.5, 0.48 + body_h * 0.5, z), Vector3(side_w, body_h, 0.26), wall)
 _piece(root, "FrontWallR", Vector3(width * 0.5 - side_w * 0.5, 0.48 + body_h * 0.5, z), Vector3(side_w, body_h, 0.26), wall)
 # Door is visually recessed; header and trim explain the opening.
 _piece(root, "Door", Vector3(door_x, 0.48 + door_h * 0.5, z - 0.04), Vector3(door_w, door_h, 0.12), dark)
 _piece(root, "DoorHeader", Vector3(door_x, 0.48 + door_h + 0.12, z - 0.08), Vector3(door_w + 0.32, 0.18, 0.16), wood)
 var window_y: float = 1.65
 for wx in [-width * 0.33, width * 0.31]:
  if absf(float(wx) - door_x) < 1.15:
   continue
  _window(root, Vector3(float(wx), window_y, z - 0.09), glass, wood)
 if floors > 1:
  for wx in [-width * 0.29, 0.0, width * 0.29]:
   _window(root, Vector3(float(wx), floor_h + 1.55, z - 0.09), glass, wood)

static func _window(root: Node3D, pos: Vector3, glass: Material, trim: Material) -> void:
 _piece(root, "WindowTrim", pos, Vector3(1.55, 1.35, 0.12), trim)
 _piece(root, "WindowGlass", pos + Vector3(0, 0, -0.07), Vector3(1.27, 1.08, 0.07), glass)
 _piece(root, "WindowMullionV", pos + Vector3(0, 0, -0.12), Vector3(0.07, 1.1, 0.08), trim)
 _piece(root, "WindowSill", pos + Vector3(0, -0.72, -0.14), Vector3(1.7, 0.12, 0.24), trim)

static func _porch(root: Node3D, width: float, depth: float, wood: Material, roof: Material) -> void:
 var porch_w: float = minf(width * 0.72, 7.2)
 var front_z: float = -depth * 0.5 - 1.15
 _piece(root, "PorchDeck", Vector3(0, 0.56, front_z), Vector3(porch_w, 0.18, 2.15), wood)
 for x in [-porch_w * 0.43, porch_w * 0.43]:
  _piece(root, "PorchPost", Vector3(float(x), 1.72, front_z - 0.65), Vector3(0.18, 2.35, 0.18), wood)
 _piece(root, "PorchCanopy", Vector3(0, 2.9, front_z - 0.15), Vector3(porch_w + 0.35, 0.16, 2.45), roof, Vector3(8, 0, 0))
 _piece(root, "FrontStep", Vector3(0, 0.27, front_z - 1.2), Vector3(2.2, 0.22, 0.65), wood)

static func _side_addition(root: Node3D, width: float, depth: float, wall: Material, roof: Material, dark: Material, glass: Material) -> void:
 var x: float = width * 0.5 + 1.65
 _piece(root, "SideAddition", Vector3(x, 1.55, depth * 0.08), Vector3(3.2, 2.45, depth * 0.62), wall)
 _piece(root, "SideAdditionRoof", Vector3(x, 2.92, depth * 0.08), Vector3(3.55, 0.18, depth * 0.7), roof, Vector3(0, 0, -7))
 _window(root, Vector3(x + 1.62, 1.65, depth * 0.08), glass, dark)

static func _shopfront(root: Node3D, width: float, depth: float, wall: Material, dark: Material, glass: Material, roof: Material) -> void:
 var z: float = -depth * 0.5 - 0.12
 _piece(root, "ShopGlazing", Vector3(1.8, 1.55, z), Vector3(3.15, 1.9, 0.10), glass)
 _piece(root, "ShopFrameTop", Vector3(1.8, 2.55, z - 0.03), Vector3(3.4, 0.16, 0.15), dark)
 _piece(root, "ShopAwning", Vector3(1.8, 2.75, z - 0.72), Vector3(3.8, 0.12, 1.35), roof, Vector3(-10, 0, 0))

static func _gable_roof(root: Node3D, width: float, depth: float, y: float, material: Material) -> void:
 var slope: float = 28.0
 var plane_w: float = width * 0.58
 _piece(root, "RoofLeft", Vector3(-width * 0.23, y + 0.72, 0), Vector3(plane_w, 0.18, depth + 0.75), material, Vector3(0, 0, -slope))
 _piece(root, "RoofRight", Vector3(width * 0.23, y + 0.72, 0), Vector3(plane_w, 0.18, depth + 0.75), material, Vector3(0, 0, slope))
 _piece(root, "RidgeCap", Vector3(0, y + 1.38, 0), Vector3(0.18, 0.18, depth + 0.82), material)

static func _hip_roof(root: Node3D, width: float, depth: float, y: float, material: Material) -> void:
 # Four shallow planes approximate a hipped silhouette while retaining cheap primitive geometry.
 _piece(root, "HipFront", Vector3(0, y + 0.62, -depth * 0.25), Vector3(width + 0.7, 0.16, depth * 0.58), material, Vector3(-20, 0, 0))
 _piece(root, "HipRear", Vector3(0, y + 0.62, depth * 0.25), Vector3(width + 0.7, 0.16, depth * 0.58), material, Vector3(20, 0, 0))
 _piece(root, "HipLeft", Vector3(-width * 0.28, y + 0.72, 0), Vector3(width * 0.58, 0.16, depth * 0.72), material, Vector3(0, 0, -18))
 _piece(root, "HipRight", Vector3(width * 0.28, y + 0.72, 0), Vector3(width * 0.58, 0.16, depth * 0.72), material, Vector3(0, 0, 18))

static func _piece(parent: Node3D, name_text: String, pos: Vector3, size: Vector3, material: Material, rot := Vector3.ZERO) -> MeshInstance3D:
 var node := MeshInstance3D.new()
 node.name = name_text
 var mesh := BoxMesh.new()
 mesh.size = size
 node.mesh = mesh
 node.material_override = material
 node.position = pos
 node.rotation_degrees = rot
 node.set_meta("architecture_module", true)
 node.set_meta("budget_class", "environment")
 node.set_meta("base_visibility_end", 175.0)
 node.visibility_range_end = 175.0
 node.visibility_range_end_margin = 8.0
 parent.add_child(node)
 return node
