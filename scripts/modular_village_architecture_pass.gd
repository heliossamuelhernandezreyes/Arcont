extends Node3D

# Replaces only the old single-mesh village visuals. Existing authored collision,
# terrain, mission routes and gameplay remain owned by ForestVillage.

const HOUSE_SPECS := [
 [Vector3(-22,0.12,-20),16.0,0], [Vector3(20,0.12,-23),-18.0,1],
 [Vector3(-25,0.12,8),-8.0,2], [Vector3(24,0.12,9),12.0,3],
 [Vector3(-20,0.12,35),18.0,4], [Vector3(20,0.12,34),-14.0,5],
 [Vector3(-37,0.12,25),80.0,6], [Vector3(37,0.12,-2),96.0,7]
]

var terrain: Node

func _ready() -> void:
 call_deferred("_build_pass")

func _build_pass() -> void:
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 var legacy := get_parent().get_node_or_null("ForestVillage")
 if legacy != null:
  _hide_legacy_houses(legacy)
 var materials := _materials()
 for spec in HOUSE_SPECS:
  var authored: Vector3 = spec[0]
  var pos := Vector3(authored.x, _height(authored.x, authored.z) + authored.y, authored.z)
  var house := ModularHouseBuilder.build(self, pos, float(spec[1]), int(spec[2]), materials)
  house.set_meta("terrain_base_y", _height(authored.x, authored.z))
 set_meta("art_status", "ART-PASS-9-MODULAR-ARCHITECTURE")
 set_meta("house_count", HOUSE_SPECS.size())
 set_meta("architecture_contract", "MODULAR-HOUSE-V1")
 set_meta("legacy_single_mesh_houses", "visuals_hidden; collision retained")
 set_meta("mobile_validation", "PENDING")

func _hide_legacy_houses(node: Node) -> void:
 for child in node.get_children():
  if child is Node3D and String(child.get_meta("art_layer", "")) == "village":
   (child as Node3D).visible = false
   child.set_meta("superseded_visual_by", "ModularVillageArchitecturePass")
  _hide_legacy_houses(child)

func _height(x: float, z: float) -> float:
 if terrain != null and terrain.has_method("get_height_at"):
  return float(terrain.call("get_height_at", x, z))
 return 0.0

func _materials() -> Dictionary:
 var plaster := _mat(Color(0.48,0.43,0.34),0.92)
 var plaster_alt := _mat(Color(0.31,0.34,0.30),0.95)
 var roof := _mat(Color(0.18,0.055,0.038),0.91)
 var wood := _mat(Color(0.19,0.105,0.047),0.94)
 var stone := _mat(Color(0.24,0.25,0.23),0.98)
 var dark := _mat(Color(0.035,0.043,0.038),0.97)
 var glass := _mat(Color(0.12,0.19,0.20),0.38)
 glass.metallic = 0.08
 return {"wall":plaster,"wall_alt":plaster_alt,"roof":roof,"wood":wood,"stone":stone,"dark":dark,"glass":glass}

func _mat(color: Color, roughness: float) -> StandardMaterial3D:
 var material := StandardMaterial3D.new()
 material.albedo_color = color
 material.roughness = roughness
 return material
