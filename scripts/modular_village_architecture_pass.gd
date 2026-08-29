extends Node3D

# Replaces only the old single-mesh village visuals. Existing authored collision,
# terrain, mission routes and gameplay remain owned by ForestVillage.

const CONTINUOUS_ROUTE_PASS := preload("res://scripts/continuous_route_surface_pass.gd")
const FOREST_TONE_PASS := preload("res://scripts/forest_visual_tone_pass.gd")
const URBAN_STRUCTURE_PASS := preload("res://scripts/village_urban_structure_pass.gd")
const MAP_COMPOSITION_PASS := preload("res://scripts/village_map_composition_pass.gd")
const ATMOSPHERE_PASS := preload("res://scripts/village_atmosphere_pass.gd")
const READABILITY_PASS := preload("res://scripts/forest_village_readability_pass.gd")
const PROP_TONE_PASS := preload("res://scripts/village_prop_tone_pass.gd")
const ORGANIC_FOREST_PASS := preload("res://scripts/organic_forest_proxy_pass.gd")
const SURFACE_CLEANUP_PASS := preload("res://scripts/village_surface_cleanup_pass.gd")
const FOREST_STRATA_PASS := preload("res://scripts/forest_strata_pass.gd")

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
  var pos := Vector3(authored.x,_height(authored.x,authored.z)+authored.y,authored.z)
  var house := ModularHouseBuilder.build(self,pos,float(spec[1]),int(spec[2]),materials)
  house.set_meta("terrain_base_y",_height(authored.x,authored.z))
 _mount_map_legibility_passes()
 set_meta("art_status","ART-PASS-17-LAYERED-FOREST")
 set_meta("house_count",HOUSE_SPECS.size())
 set_meta("architecture_contract","MODULAR-HOUSE-V2-MESH-ROOF")
 set_meta("legacy_single_mesh_houses","visuals_hidden; collision retained")
 set_meta("visual_acceptance","PENDING_CAPTURE_REVIEW")
 set_meta("mobile_validation","PENDING")

func _mount_map_legibility_passes() -> void:
 var world := get_parent()
 _mount(world,"ContinuousRouteSurfacePass",CONTINUOUS_ROUTE_PASS)
 _mount(world,"VillageUrbanStructurePass",URBAN_STRUCTURE_PASS)
 _mount(world,"VillageMapCompositionPass",MAP_COMPOSITION_PASS)
 _mount(world,"ForestVisualTonePass",FOREST_TONE_PASS)
 _mount(world,"VillageAtmospherePass",ATMOSPHERE_PASS)
 _mount(world,"ForestVillageReadabilityPass",READABILITY_PASS)
 _mount(world,"VillagePropTonePass",PROP_TONE_PASS)
 _mount(world,"OrganicForestProxyPass",ORGANIC_FOREST_PASS)
 _mount(world,"VillageSurfaceCleanupPass",SURFACE_CLEANUP_PASS)
 _mount(world,"ForestStrataPass",FOREST_STRATA_PASS)

func _mount(world: Node,name_text: String,script_resource: Script) -> void:
 if world.get_node_or_null(name_text) != null:
  return
 var pass_node: Node = script_resource.new() as Node
 if pass_node == null:
  push_error("Failed to instantiate art pass: %s" % name_text)
  return
 pass_node.name = name_text
 world.add_child(pass_node)

func _hide_legacy_houses(node: Node) -> void:
 for child in node.get_children():
  if child is Node3D and String(child.get_meta("art_layer","")) == "village":
   (child as Node3D).visible = false
   child.set_meta("superseded_visual_by","ModularVillageArchitecturePass")
  _hide_legacy_houses(child)

func _height(x: float, z: float) -> float:
 if terrain != null and terrain.has_method("get_height_at"):
  return float(terrain.call("get_height_at",x,z))
 return 0.0

func _materials() -> Dictionary:
 var plaster := _mat(Color(0.31,0.285,0.23),0.94)
 var plaster_alt := _mat(Color(0.20,0.235,0.205),0.96)
 var roof := _mat(Color(0.105,0.034,0.028),0.94)
 var wood := _mat(Color(0.115,0.062,0.030),0.97)
 var stone := _mat(Color(0.145,0.155,0.145),0.99)
 var dark := _mat(Color(0.018,0.024,0.022),0.99)
 var glass := _mat(Color(0.045,0.070,0.068),0.48)
 glass.metallic = 0.03
 return {"wall":plaster,"wall_alt":plaster_alt,"roof":roof,"wood":wood,"stone":stone,"dark":dark,"glass":glass}

func _mat(color: Color, roughness: float) -> StandardMaterial3D:
 var material := StandardMaterial3D.new()
 material.albedo_color = color
 material.roughness = roughness
 return material
