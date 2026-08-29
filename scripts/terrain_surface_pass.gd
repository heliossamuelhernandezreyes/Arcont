extends Node3D

# Lightweight terrain surface pass for Android: procedural textures, visual relief
# and sky variation without shipping large terrain texture sets.
@export var seed := 44129
@export var mound_count := 24
@export var grass_patch_count := 42
@export var dirt_patch_count := 30

var rng := RandomNumberGenerator.new()
var budget: Node
var mat_grass: StandardMaterial3D
var mat_grass_dark: StandardMaterial3D
var mat_soil: StandardMaterial3D
var mat_mud: StandardMaterial3D
var mat_concrete: StandardMaterial3D
var mat_rock: StandardMaterial3D

func _ready() -> void:
 rng.seed = seed
 _build_materials()
 _apply_existing_surface_materials()
 _add_ground_breakup()
 _add_mounds()
 _configure_sky()
 _bind_budget()
 set_meta("art_layer","terrain_surface_pass")
 set_meta("art_status","ART-PASS-2-TERRAIN")
 set_meta("mobile_validation","PENDING")

func _build_materials() -> void:
 mat_grass = _textured_mat(Color(0.13,0.20,0.075),0.98,8.0,0.58,13)
 mat_grass_dark = _textured_mat(Color(0.075,0.125,0.045),0.99,7.0,0.72,27)
 mat_soil = _textured_mat(Color(0.16,0.115,0.065),0.99,6.0,0.64,41)
 mat_mud = _textured_mat(Color(0.095,0.068,0.040),1.0,5.0,0.78,53)
 mat_concrete = _textured_mat(Color(0.30,0.31,0.29),0.96,10.0,0.42,67)
 mat_rock = _textured_mat(Color(0.24,0.25,0.22),0.99,5.0,0.55,79)

func _textured_mat(color: Color, roughness: float, tile: float, contrast: float, noise_seed: int) -> StandardMaterial3D:
 var material := StandardMaterial3D.new()
 material.albedo_color = color
 material.roughness = roughness
 material.uv1_scale = Vector3(tile,tile,tile)
 material.uv1_triplanar = true
 var noise := FastNoiseLite.new()
 noise.seed = noise_seed
 noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
 noise.frequency = 0.055
 noise.fractal_octaves = 3
 noise.fractal_gain = 0.55
 var gradient := Gradient.new()
 gradient.colors = PackedColorArray([
  Color(1.0-contrast*0.45,1.0-contrast*0.45,1.0-contrast*0.45,1.0),
  Color(1.0,1.0,1.0,1.0)
 ])
 var texture := NoiseTexture2D.new()
 texture.width = 256
 texture.height = 256
 texture.seamless = true
 texture.noise = noise
 texture.color_ramp = gradient
 material.albedo_texture = texture
 return material

func _apply_existing_surface_materials() -> void:
 var environment := get_parent().get_node_or_null("ForestVillage")
 if environment == null:
  return
 var ground := environment.get_node_or_null("ForestGround") as MeshInstance3D
 if ground:
  ground.material_override = mat_grass_dark
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
 # Larger patches first, then smaller edge noise. Keep the playable center readable.
 for i in range(grass_patch_count):
  var pos := _random_patch_position()
  var size := Vector3(rng.randf_range(5.0,13.0),0.016,rng.randf_range(4.0,11.0))
  _patch("GrassPatch",pos,size,mat_grass,rng.randf_range(-35.0,35.0),58.0)
 for i in range(dirt_patch_count):
  var pos := _random_patch_position()
  var size := Vector3(rng.randf_range(3.5,9.0),0.014,rng.randf_range(3.0,8.0))
  _patch("SoilPatch",pos,size,mat_soil if i%3 else mat_mud,rng.randf_range(-45.0,45.0),52.0)
 # Concrete/stone scars around village architecture stop the settlement from floating on dirt.
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

func _add_mounds() -> void:
 # Visual landforms live outside the combat lanes. They reshape the skyline without
 # increasing navigation complexity or changing mission coordinates.
 var anchors := [
  Vector3(-69,-1.2,-72),Vector3(68,-1.0,-70),Vector3(-70,-1.0,-25),Vector3(70,-1.2,-18),
  Vector3(-72,-1.1,31),Vector3(70,-1.0,38),Vector3(-63,-1.2,78),Vector3(63,-1.1,80)
 ]
 for anchor in anchors:
  _mound(anchor,Vector3(rng.randf_range(13,22),rng.randf_range(2.8,5.6),rng.randf_range(11,20)))
 for i in range(mound_count-anchors.size()):
  var side := -1.0 if rng.randf()<0.5 else 1.0
  var pos := Vector3(rng.randf_range(53.0,78.0)*side,rng.randf_range(-1.4,-0.7),rng.randf_range(-96.0,96.0))
  _mound(pos,Vector3(rng.randf_range(8,15),rng.randf_range(1.8,3.8),rng.randf_range(7,14)))

func _mound(pos: Vector3, scale_size: Vector3) -> void:
 var mound := MeshInstance3D.new()
 mound.name = "TerrainMound"
 var sphere := SphereMesh.new()
 sphere.radius = 1.0
 sphere.height = 2.0
 sphere.radial_segments = 12
 sphere.rings = 6
 mound.mesh = sphere
 mound.material_override = mat_grass_dark if rng.randf()<0.72 else mat_rock
 mound.position = pos
 mound.scale = scale_size
 mound.rotation_degrees.y = rng.randf_range(0,180)
 mound.visibility_range_end = 118.0
 mound.visibility_range_end_margin = 8.0
 mound.set_meta("budget_class","environment")
 mound.set_meta("base_visibility_end",118.0)
 add_child(mound)

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
