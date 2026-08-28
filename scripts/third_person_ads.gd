extends Node
class_name ThirdPersonADS

@export var hip_distance := 5.45
@export var hip_height := 0.95
@export var hip_shoulder := 1.15
@export var ads_distance := 2.85
@export var ads_height := 0.74
@export var ads_shoulder := 0.78
@export var transition_speed := 12.0
@export var collision_margin := 0.22

var player: CharacterBody3D
var camera_rig: Node3D
var spring_arm: SpringArm3D
var camera: Camera3D
var weapon: Node

func _ready() -> void:
 player = get_parent() as CharacterBody3D
 if player == null:
  return
 process_physics_priority = 100
 camera_rig = player.get_node_or_null("CameraRig") as Node3D
 spring_arm = player.get_node_or_null("CameraRig/SpringArm3D") as SpringArm3D
 camera = player.get_node_or_null("CameraRig/SpringArm3D/Camera3D") as Camera3D
 weapon = player.get_node_or_null("Weapon")
 if spring_arm:
  spring_arm.margin = collision_margin
  spring_arm.add_excluded_object(player.get_rid())
 _force_tactical_startup()

func _force_tactical_startup()->void:
 if player==null or spring_arm==null or camera==null:return
 player.set("camera_mode",0);player.set("shoulder_side",1.0)
 if weapon!=null and weapon.has_method("set_ads"):weapon.set_ads(false)
 var target:=_camera_target(false,1.0)
 spring_arm.spring_length=target.z;camera.position=Vector3(target.x,target.y,0.0)

func _physics_process(delta: float) -> void:
 if player == null or camera == null or camera_rig == null or spring_arm == null or weapon == null:
  return
 var aiming := bool(weapon.get("aiming"))
 var shoulder := float(player.get("shoulder_side"))
 if is_zero_approx(shoulder):
  shoulder = 1.0
 var target := _camera_target(aiming, shoulder)
 var blend := minf(delta * transition_speed, 1.0)
 spring_arm.spring_length = lerpf(spring_arm.spring_length, target.z, blend)
 camera.position.x = lerpf(camera.position.x, target.x, blend)
 camera.position.y = lerpf(camera.position.y, target.y, blend)
 camera.position.z = 0.0

func _camera_target(aiming: bool, shoulder: float) -> Vector3:
 var scale := float(player.camera_distance_scale()) if player.has_method("camera_distance_scale") else 1.0
 if aiming:
  return Vector3(ads_shoulder * shoulder, ads_height, ads_distance * scale)
 return Vector3(hip_shoulder * shoulder, hip_height, hip_distance * scale)

func is_aiming() -> bool:
 return weapon != null and bool(weapon.get("aiming"))
