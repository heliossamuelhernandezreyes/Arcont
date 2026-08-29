class_name ModularHouseBuilder
extends RefCounted

# ART-PASS-9B: reusable metric architecture assembled from shared primitive modules.
# This is a visual grammar, not a structural-engineering simulator.

static func build(parent: Node3D, world_pos: Vector3, yaw_deg: float, archetype: int, materials: Dictionary) -> Node3D:
 var root := Node3D.new()
 root.name = "ModularHouse_%02d" % archetype
 root.position = world_pos
 root.rotation_degrees.y = yaw_deg
 root.set_meta("art_layer", "village")
 root.set_meta("architecture_contract", "MODULAR-HOUSE-V2")
 root.set_meta("terrain_grounded", true)
 root.set_meta("archetype", archetype)
 root.set_meta("construction_logic", "plinth>wall_bays>openings>roof_assembly>trim>porch>utilities")
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

 _piece(root, "Foundation", Vector3(0, 0.18, 0), Vector3(width + 0.45, 0.36, depth + 0.45), stone)
 _piece(root, "BaseCourse", Vector3(0, 0.55, 0), Vector3(width + 0.18, 0.34, depth + 0.18), stone)
 _piece(root, "FloorSlab", Vector3(0, 0.74, 0), Vector3(width, 0.16, depth), wood)

 _piece(root, "RearWall", Vector3(0, 0.82 + body_h * 0.5, depth * 0.5), Vector3(width, body_h, 0.24), wall)
 _piece(root, "LeftWall", Vector3(-width * 0.5, 0.82 + body_h * 0.5, 0), Vector3(0.24, body_h, depth), wall_alt)
 _piece(root, "RightWall", Vector3(width * 0.5, 0.82 + body_h * 0.5, 0), Vector3(0.24, body_h, depth), wall_alt)

 var door_x: float = -width * 0.18 if archetype % 2 == 0 else width * 0.17
 _front_facade(root, width, depth, body_h, floor_h, floors, door_x, wall, wood, dark, glass)
 _corner_trim(root, width, depth, body_h, wood)

 if archetype % 8 in [1, 6]:
  _side_addition(root, width, depth, wall_alt, roof, dark, glass)
 if archetype % 8 in [0, 2, 3, 7]:
  _porch(root, width, depth, wood, roof)
 if archetype % 8 == 5:
  _shopfront(root, width, depth, wall, dark, glass, roof)

 var roof_base_y: float = body_h + 1.10
 if archetype % 8 in [3, 7]:
  _hip_roof(root, width, depth, roof_base_y, roof, wood)
 else:
  _gable_roof(root, width, depth, roof_base_y, roof, wood)

 _piece(root, "Chimney", Vector3(width * 0.28, body_h + 2.05, depth * 0.12), Vector3(0.62, 2.1, 0.62), stone)
 _piece(root, "UtilityMeter", Vector3(width * 0.5 + 0.16, 1.55, depth * 0.12), Vector3(0.16, 0.55, 0.42), dark)
 _piece(root, "Downspout", Vector3(width * 0.5 + 0.13, 1.90, -depth * 0.36), Vector3(0.12, 2.7, 0.12), dark)
 return root

static func _front_facade(root: Node3D, width: float, depth: float, body_h: float, floor_h: float, floors: int, door_x: float, wall: Material, wood: Material, dark: Material, glass: Material) -> void:
 var z: float = -depth * 0.5
 var wall_bottom: float = 0.82
 var door_w: float = 1.08
 var door_h: float = 2.16
 var left_edge: float = -width * 0.5
 var right_edge: float = width * 0.5
 var door_left: float = door_x - door_w * 0.5
 var door_right: float = door_x + door_w * 0.5
 var left_w: float = maxf(0.45, door_left - left_edge)
 var right_w: float = maxf(0.45, right_edge - door_right)
 var header_h: float = maxf(0.35, body_h - door_h)

 _piece(root, "FrontWallL", Vector3(left_edge + left_w * 0.5, wall_bottom + body_h * 0.5, z), Vector3(left_w, body_h, 0.26), wall)
 _piece(root, "FrontWallR", Vector3(door_right + right_w * 0.5, wall_bottom + body_h * 0.5, z), Vector3(right_w, body_h, 0.26), wall)
 _piece(root, "FrontWallOverDoor", Vector3(door_x, wall_bottom + door_h + header_h * 0.5, z), Vector3(door_w, header_h, 0.26), wall)

 _piece(root, "Door", Vector3(door_x, wall_bottom + door_h * 0.5, z - 0.09), Vector3(door_w, door_h, 0.12), dark)
 _piece(root, "DoorHeader", Vector3(door_x, wall_bottom + door_h + 0.10, z - 0.16), Vector3(door_w + 0.34, 0.18, 0.18), wood)
 _piece(root, "DoorSill", Vector3(door_x, wall_bottom - 0.02, z - 0.18), Vector3(door_w + 0.22, 0.10, 0.30), stone_like(wood))

 var window_y: float = wall_bottom + 1.38
 for wx_value in [-width * 0.34, width * 0.33]:
  var wx: float = float(wx_value)
  if absf(wx - door_x) < 1.25:
   continue
  _window(root, Vector3(wx, window_y, z - 0.10), glass, wood)
 if floors > 1:
  for wx_value in [-width * 0.30, 0.0, width * 0.30]:
   _window(root, Vector3(float(wx_value), wall_bottom + floor_h + 1.40, z - 0.10), glass, wood)

static func stone_like(material: Material) -> Material:
 return material

static func _window(root: Node3D, pos: Vector3, glass: Material, trim: Material) -> void:
 _piece(root, "WindowRecess", pos + Vector3(0, 0, 0.04), Vector3(1.62, 1.42, 0.14), trim)
 _piece(root, "WindowGlass", pos + Vector3(0, 0, -0.08), Vector3(1.28, 1.08, 0.06), glass)
 _piece(root, "WindowMullionV", pos + Vector3(0, 0, -0.13), Vector3(0.07, 1.10, 0.08), trim)
 _piece(root, "WindowMullionH", pos + Vector3(0, 0, -0.13), Vector3(1.28, 0.06, 0.08), trim)
 _piece(root, "WindowSill", pos + Vector3(0, -0.72, -0.16), Vector3(1.78, 0.12, 0.30), trim)

static func _corner_trim(root: Node3D, width: float, depth: float, body_h: float, trim: Material) -> void:
 var y: float = 0.82 + body_h * 0.5
 for x in [-width * 0.5 - 0.03, width * 0.5 + 0.03]:
  for z in [-depth * 0.5 - 0.03, depth * 0.5 + 0.03]:
   _piece(root, "CornerTrim", Vector3(float(x), y, float(z)), Vector3(0.20, body_h + 0.10, 0.20), trim)

static func _porch(root: Node3D, width: float, depth: float, wood: Material, roof: Material) -> void:
 var porch_w: float = minf(width * 0.70, 6.8)
 var front_z: float = -depth * 0.5 - 1.12
 _piece(root, "PorchDeck", Vector3(0, 0.77, front_z), Vector3(porch_w, 0.20, 2.10), wood)
 for x_value in [-porch_w * 0.43, porch_w * 0.43]:
  _piece(root, "PorchPost", Vector3(float(x_value), 1.88, front_z - 0.62), Vector3(0.18, 2.30, 0.18), wood)
 _piece(root, "PorchBeam", Vector3(0, 2.96, front_z - 0.62), Vector3(porch_w, 0.18, 0.18), wood)
 _piece(root, "PorchCanopy", Vector3(0, 3.05, front_z - 0.08), Vector3(porch_w + 0.28, 0.24, 2.25), roof, Vector3(7, 0, 0))
 _piece(root, "FrontStep", Vector3(0, 0.46, front_z - 1.12), Vector3(2.15, 0.24, 0.66), wood)

static func _side_addition(root: Node3D, width: float, depth: float, wall: Material, roof: Material, dark: Material, glass: Material) -> void:
 var x: float = width * 0.5 + 1.65
 _piece(root, "SideAddition", Vector3(x, 1.82, depth * 0.08), Vector3(3.2, 2.45, depth * 0.62), wall)
 _piece(root, "SideAdditionFascia", Vector3(x, 3.08, depth * 0.08), Vector3(3.55, 0.22, depth * 0.72), dark, Vector3(0, 0, -7))
 _piece(root, "SideAdditionRoof", Vector3(x, 3.18, depth * 0.08), Vector3(3.55, 0.26, depth * 0.72), roof, Vector3(0, 0, -7))
 _window(root, Vector3(x + 1.62, 1.90, depth * 0.08), glass, dark)

static func _shopfront(root: Node3D, width: float, depth: float, wall: Material, dark: Material, glass: Material, roof: Material) -> void:
 var z: float = -depth * 0.5 - 0.14
 _piece(root, "ShopGlazing", Vector3(1.8, 1.84, z), Vector3(3.15, 1.9, 0.10), glass)
 _piece(root, "ShopFrameTop", Vector3(1.8, 2.84, z - 0.03), Vector3(3.4, 0.18, 0.18), dark)
 _piece(root, "ShopFrameBottom", Vector3(1.8, 0.88, z - 0.03), Vector3(3.4, 0.18, 0.22), dark)
 _piece(root, "ShopAwning", Vector3(1.8, 3.02, z - 0.70), Vector3(3.8, 0.20, 1.35), roof, Vector3(-9, 0, 0))

static func _gable_roof(root: Node3D, width: float, depth: float, y: float, material: Material, fascia: Material) -> void:
 var slope: float = 28.0
 var plane_w: float = width * 0.555
 var overhang_z: float = 0.46
 var thickness: float = 0.34
 _piece(root, "RoofLeft", Vector3(-width * 0.232, y + 0.73, 0), Vector3(plane_w, thickness, depth + overhang_z * 2.0), material, Vector3(0, 0, -slope))
 _piece(root, "RoofRight", Vector3(width * 0.232, y + 0.73, 0), Vector3(plane_w, thickness, depth + overhang_z * 2.0), material, Vector3(0, 0, slope))
 _piece(root, "RidgeCap", Vector3(0, y + 1.42, 0), Vector3(0.28, 0.24, depth + overhang_z * 2.0 + 0.08), material)
 for z_value in [-depth * 0.5 - overhang_z, depth * 0.5 + overhang_z]:
  _piece(root, "GableFasciaL", Vector3(-width * 0.235, y + 0.68, float(z_value)), Vector3(plane_w, 0.16, 0.15), fascia, Vector3(0, 0, -slope))
  _piece(root, "GableFasciaR", Vector3(width * 0.235, y + 0.68, float(z_value)), Vector3(plane_w, 0.16, 0.15), fascia, Vector3(0, 0, slope))

static func _hip_roof(root: Node3D, width: float, depth: float, y: float, material: Material, fascia: Material) -> void:
 var thickness: float = 0.30
 _piece(root, "HipFront", Vector3(0, y + 0.62, -depth * 0.25), Vector3(width + 0.62, thickness, depth * 0.58), material, Vector3(-20, 0, 0))
 _piece(root, "HipRear", Vector3(0, y + 0.62, depth * 0.25), Vector3(width + 0.62, thickness, depth * 0.58), material, Vector3(20, 0, 0))
 _piece(root, "HipLeft", Vector3(-width * 0.28, y + 0.72, 0), Vector3(width * 0.58, thickness, depth * 0.72), material, Vector3(0, 0, -18))
 _piece(root, "HipRight", Vector3(width * 0.28, y + 0.72, 0), Vector3(width * 0.58, thickness, depth * 0.72), material, Vector3(0, 0, 18))
 _piece(root, "HipFasciaFront", Vector3(0, y + 0.16, -depth * 0.53), Vector3(width + 0.65, 0.18, 0.16), fascia)
 _piece(root, "HipFasciaRear", Vector3(0, y + 0.16, depth * 0.53), Vector3(width + 0.65, 0.18, 0.16), fascia)

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
