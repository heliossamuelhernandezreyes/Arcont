extends Node3D

# Replaces only the old single-mesh village visuals. Existing authored collision,
# terrain, mission routes and gameplay remain owned by ForestVillage.

const CONTINUOUS_ROUTE_PASS := preload("res://scripts/continuous_route_surface_pass.gd")
const FOREST_TONE_PASS := preload("res://scripts/forest_visual_tone_pass.gd")

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
 var repaired_roofs := 0
 for spec in HOUSE_SPECS:
  var authored: Vector3 = spec[0]
  var pos := Vector3(authored.x, _height(authored.x, authored.z) + authored.y, authored.z)
  var house := ModularHouseBuilder.build(self, pos, float(spec[1]), int(spec[2]), materials)
  house.set_meta("terrain_base_y", _height(authored.x, authored.z))
  _repair_roof_readability(house)
  repaired_roofs += 1
 _mount_map_legibility_passes()
 set_meta("art_status", "ART-PASS-10-MAP-LEGIBILITY")
 set_meta("house_count", HOUSE_SPECS.size())
 set_meta("architecture_contract", "MODULAR-HOUSE-V2-ROOF-FIX")
 set_meta("repaired_roofs", repaired_roofs)
 set_meta("legacy_single_mesh_houses", "visuals_hidden; collision retained")
 set_meta("visual_acceptance", "PENDING_CAPTURE_REVIEW")
 set_meta("mobile_validation", "PENDING")

func _repair_roof_readability(house: Node3D) -> void:
 # CI #450 showed the generated gable planes forming a valley/inverted-V.
 # Correct their slope directions after construction. The four-plane hip
 # approximation also overlapped badly in the capture, so suppress its side
 # plates until a purpose-built hip mesh replaces the approximation.
 var left := house.get_node_or_null("RoofLeft") as Node3D
 var right := house.get_node_or_null("RoofRight") as Node3D
 if left != null:
  left.rotation_degrees.z = 28.0
 if right != null:
  right.rotation_degrees.z = -28.0
 var fascia_left := house.get_node_or_null("FasciaLeft") as Node3D
 var fascia_right := house.get_node_or_null("FasciaRight") as Node3D
 if fascia_left != null:
  fascia_left.rotation_degrees.z = 28.0
 if fascia_right != null:
  fascia_right.rotation_degrees.z = -28.0
 var hip_left := house.get_node_or_null("HipLeft") as Node3D
 var hip_right := house.get_node_or_null("HipRight") as Node3D
 if hip_left != null:
  hip_left.visible = false
 if hip_right != null:
  hip_right.visible = false
 house.set_meta("roof_visual_fix", "CI450-slope-correction")

func _mount_map_legibility_passes() -> void:
 var world := get_parent()
 if world.get_node_or_null("ContinuousRouteSurfacePass") == null:
  var route_pass := CONTINUOUS_ROUTE_PASS.new()
  route_pass.name = "ContinuousRouteSurfacePass"
  world.add_child(route_pass)
 if world.get_node_or_null("ForestVisualTonePass") == null:
  var tone_pass := FOREST_TONE_PASS.new()
  tone_pass.name = "ForestVisualTonePass"
  world.add_child(tone_pass)

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
 # Muted procedural placeholders: silhouette/layout first, architectural PBR
 # after this pass survives capture review.
 var plaster := _mat(Color(0.38,0.35,0.29),0.94)
 var plaster_alt := _mat(Color(0.255,0.285,0.255),0.96)
 var roof := _mat(Color(0.145,0.048,0.036),0.93)
 var wood := _mat(Color(0.155,0.088,0.042),0.96)
 var stone := _mat(Color(0.205,0.215,0.20),0.99)
 var dark := _mat(Color(0.028,0.034,0.031),0.98)
 var glass := _mat(Color(0.075,0.105,0.105),0.45)
 glass.metallic = 0.04
 return {"wall":plaster,"wall_alt":plaster_alt,"roof":roof,"wood":wood,"stone":stone,"dark":dark,"glass":glass}

func _mat(color: Color, roughness: float) -> StandardMaterial3D:
 var material := StandardMaterial3D.new()
 material.albedo_color = color
 material.roughness = roughness
 return material
