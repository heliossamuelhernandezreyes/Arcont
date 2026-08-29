extends Node3D

# Candidate urban structure pass. Intentionally not mounted until the current
# architecture screenshots are reviewed, so visual comparisons stay isolated.

var terrain: Node
var sidewalk_material: StandardMaterial3D
var curb_material: StandardMaterial3D
var driveway_material: StandardMaterial3D

func _ready() -> void:
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 sidewalk_material = _make_material(Color(0.31, 0.31, 0.29), 0.96)
 curb_material = _make_material(Color(0.22, 0.23, 0.22), 0.98)
 driveway_material = _make_material(Color(0.18, 0.17, 0.14), 0.99)
 _build_core_edges()
 _build_driveways()
 set_meta("map_contract", "VILLAGE-URBAN-STRUCTURE-V1")
 set_meta("visual_status", "CANDIDATE_REQUIRES_SCREENSHOT_REVIEW")
 set_meta("mobile_validation", "PENDING")

func _make_material(color: Color, roughness: float) -> StandardMaterial3D:
 var material := StandardMaterial3D.new()
 material.albedo_color = color
 material.roughness = roughness
 return material

func _build_core_edges() -> void:
 _strip("CivicWalkWest", Vector3(-7.2, 0.034, 23.0), Vector3(2.0, 0.07, 29.0), sidewalk_material, 4.0)
 _strip("CivicWalkEast", Vector3(7.2, 0.034, 23.0), Vector3(2.0, 0.07, 29.0), sidewalk_material, 4.0)
 _strip("CivicCrossing", Vector3(0.0, 0.038, 10.5), Vector3(12.2, 0.055, 2.3), sidewalk_material, 3.0)
 _strip("CurbWestCore", Vector3(-5.8, 0.075, 23.0), Vector3(0.22, 0.15, 31.0), curb_material, 3.5)
 _strip("CurbEastCore", Vector3(5.8, 0.075, 23.0), Vector3(0.22, 0.15, 31.0), curb_material, 3.5)

func _build_driveways() -> void:
 var parcels: Array[Dictionary] = VillageUrbanPlan.parcels()
 for parcel: Dictionary in parcels:
  var center: Vector3 = parcel.get("center", Vector3.ZERO)
  var front: String = String(parcel.get("front", "east"))
  var parcel_id: String = String(parcel.get("id", "parcel"))
  var direction := Vector3(1.0, 0.0, 0.0)
  if front == "west": direction = Vector3(-1.0, 0.0, 0.0)
  elif front == "north": direction = Vector3(0.0, 0.0, -1.0)
  elif front == "south": direction = Vector3(0.0, 0.0, 1.0)
  var drive_center: Vector3 = center + direction * 5.3
  var drive_size := Vector3(7.0, 0.035, 2.5) if absf(direction.x) > 0.5 else Vector3(2.5, 0.035, 7.0)
  _strip("%s_Driveway" % parcel_id, drive_center, drive_size, driveway_material, 2.8)

func _height(x: float, z: float) -> float:
 if terrain != null and terrain.has_method("get_height_at"):
  return float(terrain.call("get_height_at", x, z))
 return 0.0

func _strip(name_text: String, center: Vector3, size: Vector3, material: Material, segment_length: float) -> void:
 var root := Node3D.new()
 root.name = name_text
 root.set_meta("art_layer", "urban_structure")
 root.set_meta("terrain_following_path", true)
 root.set_meta("visual_only", true)
 add_child(root)
 var along_z: bool = size.z >= size.x
 var total: float = size.z if along_z else size.x
 var count: int = maxi(1, ceili(total / maxf(segment_length, 0.5)))
 var piece_length: float = total / float(count)
 for i: int in range(count):
  var t: float = (float(i) + 0.5) / float(count) - 0.5
  var position := center + (Vector3(0.0, 0.0, t * total) if along_z else Vector3(t * total, 0.0, 0.0))
  position.y = _height(position.x, position.z) + center.y
  var piece_size := Vector3(size.x, size.y, piece_length) if along_z else Vector3(piece_length, size.y, size.z)
  var node := MeshInstance3D.new()
  node.name = "%s_%02d" % [name_text, i]
  var mesh := BoxMesh.new()
  mesh.size = piece_size
  node.mesh = mesh
  node.material_override = material
  node.position = position
  node.visibility_range_end = 145.0
  node.visibility_range_end_margin = 7.0
  node.set_meta("terrain_grounded", true)
  root.add_child(node)
 root.set_meta("segment_count", count)
