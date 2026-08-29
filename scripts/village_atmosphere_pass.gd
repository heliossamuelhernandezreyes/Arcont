extends Node

# ART-PASS-13B: readable dusk hierarchy for the forest village. Contrast reveals
# forest and architecture silhouettes without crushing the settlement to black.

func _ready() -> void:
 call_deferred("_apply")

func _apply() -> void:
 var world := get_parent()
 var env_node := world.get_node_or_null("WorldEnvironment") as WorldEnvironment
 if env_node != null and env_node.environment != null:
  var env := env_node.environment
  env.background_mode = Environment.BG_COLOR
  env.background_color = Color(0.020,0.032,0.040,1)
  env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
  env.ambient_light_color = Color(0.27,0.34,0.31,1)
  env.ambient_light_energy = 0.82
  env.reflected_light_source = Environment.REFLECTION_SOURCE_BG
  env.fog_enabled = true
  env.fog_light_color = Color(0.105,0.132,0.136,1)
  env.fog_light_energy = 0.50
  env.fog_density = 0.0052
  env.fog_height = 2.4
  env.fog_height_density = 0.078
 var moon := world.get_node_or_null("MoonLight") as DirectionalLight3D
 if moon != null:
  moon.light_color = Color(0.60,0.73,0.80,1)
  moon.light_energy = 1.38
  moon.shadow_enabled = true
 var emergency := world.get_node_or_null("EmergencyLight") as OmniLight3D
 if emergency != null:
  emergency.light_energy = 2.5
  emergency.omni_range = 12.5
 var far_light := world.get_node_or_null("EmergencyLightFar") as OmniLight3D
 if far_light != null:
  far_light.light_energy = 1.25
  far_light.omni_range = 9.0
 set_meta("art_status","ART-PASS-13B-READABLE-DUSK")
 set_meta("lighting_contract","FOREST-VILLAGE-DUSK-V3")
 set_meta("device_validation","PENDING")
