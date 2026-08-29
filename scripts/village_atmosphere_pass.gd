extends Node

# ART-PASS-13: readable dusk hierarchy for the forest village. Contrast should
# reveal silhouettes and depth without crushing the entire settlement to black.

func _ready() -> void:
 call_deferred("_apply")

func _apply() -> void:
 var world := get_parent()
 var env_node := world.get_node_or_null("WorldEnvironment") as WorldEnvironment
 if env_node != null and env_node.environment != null:
  var env := env_node.environment
  env.background_mode = Environment.BG_COLOR
  env.background_color = Color(0.016,0.027,0.034,1)
  env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
  env.ambient_light_color = Color(0.22,0.29,0.27,1)
  env.ambient_light_energy = 0.68
  env.reflected_light_source = Environment.REFLECTION_SOURCE_BG
  env.fog_enabled = true
  env.fog_light_color = Color(0.095,0.120,0.125,1)
  env.fog_light_energy = 0.48
  env.fog_density = 0.0062
  env.fog_height = 2.4
  env.fog_height_density = 0.085
 var moon := world.get_node_or_null("MoonLight") as DirectionalLight3D
 if moon != null:
  moon.light_color = Color(0.58,0.70,0.78,1)
  moon.light_energy = 1.12
  moon.shadow_enabled = true
 var emergency := world.get_node_or_null("EmergencyLight") as OmniLight3D
 if emergency != null:
  emergency.light_energy = 2.35
  emergency.omni_range = 12.0
 var far_light := world.get_node_or_null("EmergencyLightFar") as OmniLight3D
 if far_light != null:
  far_light.light_energy = 1.2
  far_light.omni_range = 9.0
 set_meta("art_status","ART-PASS-13-READABLE-DUSK")
 set_meta("lighting_contract","FOREST-VILLAGE-DUSK-V2")
 set_meta("device_validation","PENDING")
