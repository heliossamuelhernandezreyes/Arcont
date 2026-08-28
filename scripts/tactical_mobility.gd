extends Node
class_name TacticalMobility

signal stance_changed(state:String)
@export var crouch_speed_multiplier:=0.58
@export var crouch_height:=1.12
@export var crouch_visual_drop:=0.42
# Legacy slide exports remain for save/API compatibility, but sliding is intentionally disabled.
@export var slide_duration:=0.62
@export var slide_speed:=10.8
@export var slide_friction:=8.0
@export var vault_forward_distance:=1.35
@export var vault_height_min:=0.45
@export var vault_height_max:=1.35
@export var vault_duration:=0.34
@export var mantle_height_max:=2.05
@export var mantle_duration:=0.62
@export var dodge_distance:=2.15
@export var dodge_duration:=0.28
@export var dodge_cooldown:=0.48
@export var cover_transfer_distance:=4.6
@export var safe_fall_speed:=8.0
@export var hard_fall_speed:=13.5
@export var severe_leg_threshold:=1.25
var player:CharacterBody3D
var collision:CollisionShape3D
var body_visual:Node3D
var camera_rig:Node3D
var standing_height:=1.8
var base_body_y:=0.0
var base_camera_y:=0.0
var crouched:=false
var sliding:=false
var vaulting:=false
var mantling:=false
var dodging:=false
var slide_remaining:=0.0
var slide_direction:=Vector3.ZERO
var slide_velocity:=0.0
var traverse_elapsed:=0.0
var traverse_duration:=0.0
var traverse_start:=Vector3.ZERO
var traverse_end:=Vector3.ZERO
var dodge_remaining:=0.0
var dodge_cooldown_remaining:=0.0
var dodge_direction:=Vector3.ZERO
var dodge_speed:=0.0
var last_vertical_speed:=0.0
func _ready()->void:
 player=get_parent() as CharacterBody3D
 if player==null:return
 collision=player.get_node_or_null("Collision") as CollisionShape3D;body_visual=player.get_node_or_null("BodyVisual") as Node3D;camera_rig=player.get_node_or_null("CameraRig") as Node3D
 if collision and collision.shape is CapsuleShape3D:standing_height=(collision.shape as CapsuleShape3D).height
 if body_visual:base_body_y=body_visual.position.y
 if camera_rig:base_camera_y=camera_rig.position.y
func _physics_process(delta:float)->void:
 if player==null:return
 dodge_cooldown_remaining=maxf(dodge_cooldown_remaining-delta,0.0)
 if dodging:
  dodge_remaining=maxf(dodge_remaining-delta,0.0)
  if dodge_remaining<=0.0:_end_dodge()
 if vaulting or mantling:_update_traverse(delta)
 _update_stance_visual(delta)
func toggle_crouch()->void:
 if vaulting or mantling or dodging:return
 if crouched:
  if _can_stand():_set_crouched(false)
 else:_set_crouched(true)
func request_crouch_or_slide()->bool:
 # Arcont uses an explicit dodge, not an automatic shooter-style slide.
 if player==null or vaulting or mantling or dodging:return false
 toggle_crouch();return true
func request_slide()->bool:
 # Compatibility endpoint. Sliding is intentionally disabled by design.
 return false
func try_contextual_jump()->bool:
 if try_vault():return true
 return try_mantle()
func try_vault()->bool:return _try_traverse(vault_height_min,vault_height_max,vault_duration,0.95,"vault")
func try_mantle()->bool:
 if _leg_load()>=severe_leg_threshold:return false
 return _try_traverse(vault_height_max+0.05,mantle_height_max,mantle_duration,0.72,"mantle")
func _try_traverse(min_height:float,max_height:float,duration:float,forward_landing:float,kind:String)->bool:
 if player==null or vaulting or mantling or dodging or not player.is_on_floor():return false
 var world:=player.get_world_3d();if world==null:return false
 var forward:Vector3=-player.global_transform.basis.z;forward.y=0.0;forward=forward.normalized();var origin:=player.global_position+Vector3.UP*0.55;var reach:=vault_forward_distance+(0.28 if kind=="mantle" else 0.0)
 var front_query:=PhysicsRayQueryParameters3D.create(origin,origin+forward*reach);front_query.exclude=[player.get_rid()];var front_hit:=world.direct_space_state.intersect_ray(front_query);if front_hit.is_empty():return false
 var obstacle_point:Vector3=front_hit.get("position",origin);var top_origin:=obstacle_point+Vector3.UP*(max_height+0.35)-forward*0.10;var down_query:=PhysicsRayQueryParameters3D.create(top_origin,obstacle_point-Vector3.UP*0.15);down_query.exclude=[player.get_rid()];var top_hit:=world.direct_space_state.intersect_ray(down_query);if top_hit.is_empty():return false
 var top_point:Vector3=top_hit.get("position",obstacle_point);var obstacle_height:=top_point.y-player.global_position.y;if obstacle_height<min_height or obstacle_height>max_height:return false
 var landing:=top_point+forward*forward_landing+Vector3.UP*0.05;var clearance:=PhysicsRayQueryParameters3D.create(landing+Vector3.UP*0.15,landing+Vector3.UP*1.65);clearance.exclude=[player.get_rid()];if not world.direct_space_state.intersect_ray(clearance).is_empty():return false
 vaulting=kind=="vault";mantling=kind=="mantle";crouched=false;traverse_elapsed=0.0;traverse_duration=duration*clampf(1.0+_leg_load()*0.22,1.0,1.35);traverse_start=player.global_position;traverse_end=landing;player.velocity=Vector3.ZERO
 if player.has_method("_leave_cover"):player.call("_leave_cover")
 stance_changed.emit(kind);return true
func request_dodge(input_direction:=Vector3.ZERO)->bool:
 if player==null or dodging or vaulting or mantling or not player.is_on_floor() or dodge_cooldown_remaining>0.0:return false
 if _leg_load()>=severe_leg_threshold:return false
 if bool(player.get("in_cover")) and _try_cover_transfer(input_direction):return true
 var direction:Vector3=input_direction;direction.y=0.0
 if direction.length_squared()<0.04:direction=-player.global_transform.basis.z
 direction=direction.normalized();dodging=true;dodge_remaining=dodge_duration*clampf(1.0-_leg_load()*0.10,0.78,1.0);dodge_cooldown_remaining=dodge_cooldown;dodge_direction=direction
 var distance:=dodge_distance*clampf(1.0-_leg_load()*0.25,0.52,1.0);dodge_speed=distance/maxf(dodge_remaining,0.05);stance_changed.emit("dodge");return true
func _try_cover_transfer(preferred:Vector3)->bool:
 if player==null:return false
 var world:=player.get_world_3d();if world==null:return false
 var direction:Vector3=preferred;direction.y=0.0
 if direction.length_squared()<0.04:direction=player.global_transform.basis.x*float(player.get("shoulder_side"))
 direction=direction.normalized();var best_point:=Vector3.INF
 for distance_value:float in [2.0,3.0,4.0,cover_transfer_distance]:
  var probe:=player.global_position+direction*distance_value+Vector3.UP*0.7;var rays:Array[Vector3]=[direction,-direction,-player.global_transform.basis.z]
  for ray_dir:Vector3 in rays:
   var query:=PhysicsRayQueryParameters3D.create(probe,probe+ray_dir.normalized()*1.2);query.exclude=[player.get_rid()];var hit:=world.direct_space_state.intersect_ray(query)
   if not hit.is_empty():best_point=hit.get("position",probe)-ray_dir.normalized()*0.48;break
  if best_point!=Vector3.INF:break
 if best_point==Vector3.INF:return false
 vaulting=true;mantling=false;traverse_elapsed=0.0;traverse_duration=0.38*clampf(1.0+_leg_load()*0.20,1.0,1.35);traverse_start=player.global_position;traverse_end=best_point;player.velocity=Vector3.ZERO
 if player.has_method("_leave_cover"):player.call("_leave_cover")
 stance_changed.emit("cover_transfer");return true
func movement_speed_multiplier()->float:
 if vaulting or mantling:return 0.0
 if dodging:return 1.0
 return crouch_speed_multiplier if crouched else 1.0
func apply_motion_override()->void:
 if player==null:return
 if dodging:player.velocity.x=dodge_direction.x*dodge_speed;player.velocity.z=dodge_direction.z*dodge_speed
func blocks_normal_movement()->bool:return vaulting or mantling
func blocks_jump()->bool:return vaulting or mantling or dodging
func is_crouched()->bool:return crouched
func record_vertical_speed(speed:float)->void:last_vertical_speed=minf(last_vertical_speed,speed)
func handle_landing()->void:
 var impact:=absf(minf(last_vertical_speed,0.0));last_vertical_speed=0.0
 if impact<=safe_fall_speed:return
 var severity:=clampf((impact-safe_fall_speed)/maxf(hard_fall_speed-safe_fall_speed,0.1),0.0,1.5)
 if player.has_method("apply_damage"):player.call("apply_damage",lerpf(7.0,34.0,minf(severity,1.0)),Vector3.ZERO,"left_leg" if randf()<0.5 else "right_leg",1.0)
 if severity>0.45:stance_changed.emit("hard_land")
func _update_traverse(delta:float)->void:
 traverse_elapsed+=delta;var t:=clampf(traverse_elapsed/maxf(traverse_duration,0.01),0.0,1.0);var smooth:=t*t*(3.0-2.0*t);var pos:=traverse_start.lerp(traverse_end,smooth);pos.y+=sin(t*PI)*(0.52 if vaulting else 0.72);player.global_position=pos;player.velocity=Vector3.ZERO
 if t>=1.0:vaulting=false;mantling=false;stance_changed.emit("crouch" if crouched else "stand")
func _end_slide()->void:
 sliding=false;slide_remaining=0.0;slide_velocity=0.0;stance_changed.emit("crouch" if crouched else "stand")
func _end_dodge()->void:
 if not dodging:return
 dodging=false;dodge_remaining=0.0;dodge_speed=0.0;stance_changed.emit("crouch" if crouched else "stand")
func _set_crouched(active:bool)->void:crouched=active;stance_changed.emit("crouch" if crouched else "stand")
func _can_stand()->bool:
 if player==null:return false
 var world:=player.get_world_3d();if world==null:return true
 var query:=PhysicsRayQueryParameters3D.create(player.global_position+Vector3.UP*0.95,player.global_position+Vector3.UP*1.75);query.exclude=[player.get_rid()];return world.direct_space_state.intersect_ray(query).is_empty()
func _update_stance_visual(delta:float)->void:
 var crouch_alpha:=1.0 if crouched else 0.0
 if collision and collision.shape is CapsuleShape3D:
  var capsule:=collision.shape as CapsuleShape3D;var target_height:=crouch_height if crouch_alpha>0.5 else standing_height;capsule.height=lerpf(capsule.height,target_height,minf(delta*13.0,1.0))
 if body_visual:
  var target_body_y:=base_body_y-crouch_visual_drop*crouch_alpha;body_visual.position.y=lerpf(body_visual.position.y,target_body_y,minf(delta*12.0,1.0))
 # CameraRig height is stance ownership; Camera3D position remains exclusively ThirdPersonADS ownership.
 if camera_rig:
  var target_camera_y:=base_camera_y-0.34*crouch_alpha;camera_rig.position.y=lerpf(camera_rig.position.y,target_camera_y,minf(delta*12.0,1.0))
func _leg_load()->float:
 if player==null:return 0.0
 var data=player.get("injuries");if not data is Dictionary:return 0.0
 var injury_data:=data as Dictionary;return float(injury_data.get("left_leg",0.0))+float(injury_data.get("right_leg",0.0))
