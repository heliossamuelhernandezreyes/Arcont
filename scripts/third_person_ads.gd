extends Node
class_name ThirdPersonADS

# CameraRig owns orbit. The pivot is raised to chest/head level; SpringArm owns
# collision distance; Camera3D only owns the lateral shoulder offset.
@export var hip_distance := 4.65
@export var hip_pivot_height := 1.58
@export var hip_shoulder := 0.82
@export var hip_fov := 72.0
@export var ads_distance := 2.35
@export var ads_pivot_height := 1.52
@export var ads_shoulder := 0.58
@export var transition_speed := 10.5
@export var collision_margin := 0.18
@export var minimum_safe_distance := 0.72

var player: CharacterBody3D
var camera_rig: Node3D
var spring_arm: SpringArm3D
var camera: Camera3D
var weapon: Node
var body_visual: Node3D
var body_meshes: Array[GeometryInstance3D] = []

func _ready() -> void:
 player = get_parent() as CharacterBody3D
 if player == null:
  return
 process_physics_priority = 100
 camera_rig = player.get_node_or_null("CameraRig") as Node3D
 spring_arm = player.get_node_or_null("CameraRig/SpringArm3D") as SpringArm3D
 camera = player.get_node_or_null("CameraRig/SpringArm3D/Camera3D") as Camera3D
 weapon = player.get_node_or_null("Weapon")
 body_visual = player.get_node_or_null("BodyVisual") as Node3D
 if spring_arm:
  spring_arm.margin = collision_margin
  spring_arm.add_excluded_object(player.get_rid())
 _collect_body_meshes(body_visual)
 _force_tactical_startup()

func _collect_body_meshes(node: Node) -> void:
 if node == null:
  return
 if node is GeometryInstance3D:
  body_meshes.append(node as GeometryInstance3D)
 for child in node.get_children():
  _collect_body_meshes(child)

func _force_tactical_startup() -> void:
 if player == null or spring_arm == null or camera == null or camera_rig == null:
  return
 player.set("camera_mode",0)
 player.set("shoulder_side",1.0)
 if weapon != null and weapon.has_method("set_ads"):
  weapon.set_ads(false)
 var target := _camera_target(false,1.0)
 camera_rig.position.y = target.y
 spring_arm.spring_length = target.z
 camera.position = Vector3(target.x,0.0,0.0)
 camera.fov = hip_fov
 _update_near_camera_visibility()

func _physics_process(delta: float) -> void:
 if player == null or camera == null or camera_rig == null or spring_arm == null or weapon == null:
  return
 var aiming := bool(weapon.get("aiming"))
 var shoulder := float(player.get("shoulder_side"))
 if is_zero_approx(shoulder):
  shoulder = 1.0
 var target := _camera_target(aiming,shoulder)
 var blend := 1.0 - exp(-transition_speed * delta)
 camera_rig.position.y = lerpf(camera_rig.position.y,target.y,blend)
 spring_arm.spring_length = lerpf(spring_arm.spring_length,target.z,blend)
 camera.position.x = lerpf(camera.position.x,target.x,blend)
 camera.position.y = 0.0
 camera.position.z = 0.0
 _update_near_camera_visibility()

func _camera_target(aiming: bool, shoulder: float) -> Vector3:
 var scale := float(player.camera_distance_scale()) if player.has_method("camera_distance_scale") else 1.0
 if aiming:
  return Vector3(ads_shoulder * shoulder,ads_pivot_height,maxf(ads_distance * scale,minimum_safe_distance))
 return Vector3(hip_shoulder * shoulder,hip_pivot_height,maxf(hip_distance * scale,minimum_safe_distance))

func _update_near_camera_visibility() -> void:
 # SpringArm can legitimately collapse in doorways. Hiding only the operator shell
 # at extreme compression prevents the camera from rendering from inside the head.
 var actual_distance := camera.global_position.distance_to(player.global_position + Vector3.UP * camera_rig.position.y)
 var shell_visible := actual_distance >= minimum_safe_distance
 for mesh in body_meshes:
  if is_instance_valid(mesh):
   mesh.visible = shell_visible

func get_camera_distance() -> float:
 if camera == null or player == null or camera_rig == null:
  return 0.0
 return camera.global_position.distance_to(player.global_position + Vector3.UP * camera_rig.position.y)

func is_aiming() -> bool:
 return weapon != null and bool(weapon.get("aiming"))
