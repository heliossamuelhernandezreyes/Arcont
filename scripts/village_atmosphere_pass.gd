extends Node

# ART-PASS-20B: readable dusk for a forest-swallowed village.
# Keep nocturnal mood while revealing tree trunks, house edges and understory in captures/mobile.

func _ready() -> void:
 call_deferred("_apply")

func _apply() -> void:
 var world := get_parent()
 var env_node := world.get_node_or_null("WorldEnvironment") as WorldEnvironment
 if env_node != null and env_node.environment != null:
  var env := env_node.environment
  env.background_mode = Environment.BG_COLOR
  env.background_color = Color(0.026,0.041,0.048,1)
  env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
  env.ambient_light_color = Color(0.31,0.39,0.34,1)
  env.ambient_light_energy = 1.02
  env.reflected_light_source = Environment.REFLECTION_SOURCE_BG
  env.fog_enabled = true
  env.fog_light_color = Color(0.125,0.155,0.150,1)
  env.fog_light_energy = 0.58
  env.fog_density = 0.0044
  env.fog_height = 2.7
  env.fog_height_density = 0.064
 var moon := world.get_node_or_null("MoonLight") as DirectionalLight3D
 if moon != null:
  moon.light_color = Color(0.64,0.76,0.82,1)
  moon.light_energy = 1.58
  moon.shadow_enabled = true
 var emergency := world.get_node_or_null("EmergencyLight") as OmniLight3D
 if emergency != null:
  emergency.light_energy = 2.15
  emergency.omni_range = 11.5
 var far_light := world.get_node_or_null("EmergencyLightFar") as OmniLight3D
 if far_light != null:
  far_light.light_energy = 1.05
  far_light.omni_range = 8.5
 set_meta("art_status","ART-PASS-20B-READABLE-FOREST-DUSK")
 set_meta("lighting_contract","FOREST-VILLAGE-DUSK-V4")
 set_meta("visual_acceptance","PENDING_CAPTURE_REVIEW")
 set_meta("device_validation","PENDING")
