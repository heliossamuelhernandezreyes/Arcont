extends Node
class_name ThirdPersonADS

@export var hip_distance := 6.0
@export var hip_height := 1.18
@export var hip_shoulder := 1.22
@export var ads_distance := 3.35
@export var ads_height := 1.02
@export var ads_shoulder := 0.86
@export var transition_speed := 14.0
@export var collision_margin := 0.18

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
