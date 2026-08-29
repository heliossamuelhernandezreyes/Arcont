extends Node3D

# Secondary terrain dressing. The continuous heightmap owns macro relief; this
# pass adds PBR material families and sparse readable breakup only.
@export var seed := 44129
@export var grass_patch_count := 24
@export var dirt_patch_count := 18

const PBR_ROOT := "res://assets/provisional/cc0_runtime/pbr_terrain/poly_haven"

var rng := RandomNumberGenerator.new()
var budget: Node
var mat_grass: Material
var mat_grass_dark: Material
var mat_soil: Material
var mat_mud: Material
var mat_concrete: Material
var mat_rock: Material

func _ready() -> void:
 rng.seed = seed
 _build_materials()
 _apply_existing_surface_materials()
 _add_ground_breakup()
 _configure_sky()
 _bind_budget()
 set_meta("art_layer","terrain_surface_pass")
 set_meta("art_status","ART-PASS-6-PBR-SURFACES")
 set_meta("macro_relief_owner","ForestTerrainRelief")
 set_meta("mobile_validation","PENDING")

func _build_materials() -> void:
 mat_grass = _pbr_mat("forest_ground", Color(0.13,0.20,0.075),0.98,0.86)
 mat_grass_dark = _pbr_mat("forest_ground", Color(0.085,0.13,0.055),0.98,0.72)
 mat_soil = _pbr_mat("dirt_path", Color(0.16,0.115,0.065),0.99,0.82)
 mat_mud = _pbr_mat("dirt_path", Color(0.095,0.068,0.040),1.0,0.68)
 mat_concrete = _pbr_mat("concrete_moss", Color(0.30,0.31,0.29),0.96,0.90)
 mat_rock = _pbr_mat("rock_ground", Color(0.24,0.25,0.22),0.99,0.82)

func _pbr_mat(family: String, fallback_color: Color, fallback_roughness: float, tile_scale: float) -> Material:
 var root := PBR_ROOT + "/" + family
 var albedo := root + "/albedo.jpg"
 var normal := root + "/normal.jpg"
 var arm := root + "/arm.jpg"
 if ResourceLoader.exists(albedo) and ResourceLoader.exists(normal) and ResourceLoader.exists(arm):
  var material := ORMMaterial3D.new()
  material.albedo_texture = load(albedo) as Texture2D
  material.normal_enabled = true
  material.normal_texture = load(normal) as Texture2D
  material.orm_texture = load(arm) as Texture2D
  material.uv1_scale = Vector3(tile_scale,tile_scale,tile_scale)
  material.uv1_triplanar = true
  material.uv1_world_triplanar = true
  material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
  return material
 var fallback := StandardMaterial3D.new()
 fallback.albedo_color = fallback_color
 fallback.roughness = fallback_roughness
 return fallback

func _apply_existing_surface_materials() -> void:
 var environment := get_parent().get_node_or_null("ForestVillage")
 if environment == null:
  return
 var ground := environment.get_node_or_null("ForestGround") as MeshInstance3D
 if ground:
  ground.visible = false
  ground.set_meta("superseded_by","ForestTerrainRelief/ContinuousTerrain")
 for name in ["SouthRoad","VillageRoad","NorthRoad","VillageApron"]:
  var node := environment.get_node_or_null(name) as MeshInstance3D
  if node:
   node.material_override = mat_soil
 for name in ["WestTrack","EastTrack"]:
  var node := environment.get_node_or_null(name) as MeshInstance3D
  if node:
   node.material_override = mat_mud
 var square := environment.get_node_or_null("VillageSquare") as MeshInstance3D
 if square:
  square.material_override = mat_concrete

func _add_ground_breakup() -> void:
 for i in range(grass_patch_count):
  var pos := _random_patch_position()
  var size := Vector3(rng.randf_range(5.0,13.0),0.016,rng.randf_range(4.0,11.0))
  _patch("GrassPatch",pos,size,mat_grass,rng.randf_range(-35.0,35.0),58.0)
 for i in range(dirt_patch_count):
  var pos := _random_patch_position()
  var size := Vector3(rng.randf_range(3.5,9.0),0.014,rng.randf_range(3.0,8.0))
  _patch("SoilPatch",pos,size,mat_soil if i%3 else mat_mud,rng.randf_range(-45.0,45.0),52.0)
 for data in [
  [Vector3(-22,0.047,-20),Vector3(14,0.018,13),16.0],
  [Vector3(20,0.047,-23),Vector3(13,0.018,13),-18.0],
  [Vector3(-25,0.047,8),Vector3(13,0.018,12),-8.0],
  [Vector3(24,0.047,9),Vector3(13,0.018,12),12.0],
  [Vector3(-20,0.047,35),Vector3(13,0.018,12),18.0],
  [Vector3(20,0.047,34),Vector3(13,0.018,12),-14.0]
 ]:
  _patch("FoundationWear",data[0],data[1],mat_concrete,float(data[2]),64.0)

func _random_patch_position() -> Vector3:
 var side := -1.0 if rng.randf() < 0.5 else 1.0
 var x := rng.randf_range(18.0,74.0) * side
 var z := rng.randf_range(-94.0,94.0)
 if rng.randf() < 0.28:
  x = rng.randf_range(-38.0,38.0)
  z = rng.randf_range(45.0,88.0) if rng.randf() < 0.5 else rng.randf_range(-88.0,-48.0)
 return Vector3(x,0.038,z)

func _patch(name_text: String, pos: Vector3, size: Vector3, material: Material, yaw: float, visibility: float) -> void:
 var terrain := get_parent().get_node_or_null("ForestTerrainRelief")
 if terrain != null and terrain.has_method("get_height_at"):
  pos.y = float(terrain.call("get_height_at",pos.x,pos.z)) + 0.025
 var mesh_instance := MeshInstance3D.new()
 mesh_instance.name = name_text
 var mesh := BoxMesh.new()
 mesh.size = size
 mesh_instance.mesh = mesh
 mesh_instance.material_override = material
 mesh_instance.position = pos
 mesh_instance.rotation_degrees.y = yaw
 mesh_instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 mesh_instance.visibility_range_end = visibility
 mesh_instance.visibility_range_end_margin = 5.0
 mesh_instance.set_meta("budget_class","prop")
 mesh_instance.set_meta("base_visibility_end",visibility)
 add_child(mesh_instance)

func _configure_sky() -> void:
 var world_environment := get_parent().get_node_or_null("WorldEnvironment") as WorldEnvironment
 if world_environment == null or world_environment.environment == null:
  return
 var sky_material := ProceduralSkyMaterial.new()
 sky_material.sky_top_color = Color(0.018,0.035,0.070)
 sky_material.sky_horizon_color = Color(0.095,0.135,0.175)
 sky_material.ground_bottom_color = Color(0.012,0.020,0.018)
 sky_material.ground_horizon_color = Color(0.075,0.090,0.080)
 sky_material.sun_angle_max = 5.0
 sky_material.sun_curve = 0.12
 var sky := Sky.new()
 sky.sky_material = sky_material
 world_environment.environment.background_mode = Environment.BG_SKY
 world_environment.environment.sky = sky
 world_environment.environment.background_energy_multiplier = 0.78

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
  if child is GeometryInstance3D and child.has_meta("base_visibility_end"):
   var geometry := child as GeometryInstance3D
   var base := float(child.get_meta("base_visibility_end"))
   var factor := prop_scale if String(child.get_meta("budget_class","environment")) == "prop" else visibility_scale
   geometry.visibility_range_end = maxf(24.0,base*factor)
