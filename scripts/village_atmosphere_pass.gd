extends Node

# ART-PASS-12: capture-visible dusk hierarchy for the forest village. This is a
# conservative runtime lighting pass; final exposure remains subject to device review.

func _ready() -> void:
 call_deferred("_apply")

func _apply() -> void:
 var world := get_parent()
 var env_node := world.get_node_or_null("WorldEnvironment") as WorldEnvironment
 if env_node != null and env_node.environment != null:
  var env := env_node.environment
  env.background_mode = Environment.BG_COLOR
  env.background_color = Color(0.010,0.018,0.025,1)
  env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
  env.ambient_light_color = Color(0.16,0.22,0.20,1)
  env.ambient_light_energy = 0.46
  env.reflected_light_source = Environment.REFLECTION_SOURCE_BG
  env.fog_enabled = true
  env.fog_light_color = Color(0.075,0.095,0.10,1)
  env.fog_light_energy = 0.42
  env.fog_density = 0.009
  env.fog_height = 2.2
  env.fog_height_density = 0.11
 var moon := world.get_node_or_null("MoonLight") as DirectionalLight3D
 if moon != null:
  moon.light_color = Color(0.56,0.68,0.76,1)
  moon.light_energy = 0.92
  moon.shadow_enabled = true
 var emergency := world.get_node_or_null("EmergencyLight") as OmniLight3D
 if emergency != null:
  emergency.light_energy = 2.25
  emergency.omni_range = 12.0
 var far_light := world.get_node_or_null("EmergencyLightFar") as OmniLight3D
 if far_light != null:
  far_light.light_energy = 1.1
  far_light.omni_range = 8.0
 set_meta("art_status","ART-PASS-12-DUSK-ATMOSPHERE")
 set_meta("lighting_contract","FOREST-VILLAGE-DUSK-V1")
 set_meta("device_validation","PENDING")
