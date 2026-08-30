extends Node
class_name MeleeCombatController

signal guard_changed(line:String)
signal melee_feedback(text:String)
signal execution_window_changed(active:bool)
signal attack_visual(line:String,profile:String)
signal parry_visual(line:String,result:String)
signal execute_visual(profile:String)
@export var reach:=2.05
@export var high_damage:=125.0
@export var mid_damage:=34.0
@export var low_damage:=46.0
@export var guard_parry_window:=0.16
@export var execute_window:=0.45
@export var mid_parry_advantage:=0.20
@export var attack_cooldown:=0.46
var player:CharacterBody3D
var camera:Camera3D
var weapon:Node
var guarding:=false
var guard_line:="mid"
var guard_started:=0.0
var attack_timer:=0.0
var execute_timer:=0.0
var execute_target:Node=null
var input_origin:=Vector2.ZERO
func _ready()->void:
 player=get_parent() as CharacterBody3D
 if player:
  camera=player.get_node_or_null("CameraRig/Camera3D") as Camera3D
  weapon=player.get_node_or_null("Weapon")
func _process(delta:float)->void:
 attack_timer=maxf(attack_timer-delta,0.0)
 if execute_timer>0.0:
  execute_timer=maxf(execute_timer-delta,0.0)
  if execute_timer<=0.0:execute_target=null;execution_window_changed.emit(false)
func begin_guard(screen_position:=Vector2.ZERO)->void:
 if attack_timer>0.0:return
 guarding=true;guard_line="mid";guard_started=Time.get_ticks_msec()/1000.0;input_origin=screen_position;guard_changed.emit(guard_line)
func update_guard_drag(current:Vector2)->void:
 if not guarding:return
 var dy:=current.y-input_origin.y;var next_line:="mid"
 if dy < -32.0:next_line="high"
 elif dy > 32.0:next_line="low"
 if next_line!=guard_line:guard_line=next_line;guard_changed.emit(guard_line)
func release_attack()->bool:
 if not guarding:return false
 guarding=false
 if execute_timer>0.0 and is_instance_valid(execute_target):return _execute_target()
 return _attack_line(guard_line)
func quick_execute()->bool:
 if execute_timer<=0.0 or not is_instance_valid(execute_target):return false
 return _execute_target()
func _attack_line(line:String)->bool:
 if attack_timer>0.0 or camera==null:return false
 attack_timer=attack_cooldown;var profile:=_profile_name();attack_visual.emit(line,profile);var hit:=_melee_trace(reach)
 if hit.is_empty():melee_feedback.emit(line.to_upper());return true
 var target:Node=hit.get("collider") as Node
 if target==null:return true
 var point:Vector3=hit.get("position",target.global_position if target is Node3D else player.global_position);var direction:Vector3=-camera.global_transform.basis.z
 if target.has_method("receive_melee_attack"):target.call("receive_melee_attack",line,profile,player,direction)
 elif target.has_method("apply_hit"):
  var damage:=mid_damage
  if line=="high":damage=high_damage
  elif line=="low":damage=low_damage
  target.call("apply_hit",point,direction,damage,"heavy",5.0)
  if line=="low" and target.has_method("force_knockdown"):target.call("force_knockdown",1.35)
 melee_feedback.emit("STRIKE "+line.to_upper());return true
func receive_melee_attack(line:String,attacker:Node,damage:=35.0)->Dictionary:
 if not guarding:return {"result":"hit","damage":damage}
 if line!=guard_line:return {"result":"hit","damage":damage}
 var elapsed:=Time.get_ticks_msec()/1000.0-guard_started;var perfect:=elapsed<=guard_parry_window
 if not perfect:parry_visual.emit(line,"block");return {"result":"block","damage":damage*0.28}
 if line=="mid":_push_apart(attacker);parry_visual.emit(line,"mid_parry");melee_feedback.emit("PARRY · SPACE");return {"result":"mid_parry","damage":0.0,"advantage":mid_parry_advantage}
 execute_target=attacker;execute_timer=execute_window;execution_window_changed.emit(true);parry_visual.emit(line,"parry");melee_feedback.emit("PARRY · EXECUTE");return {"result":"parry","damage":0.0,"execute":true}
func open_execution(target:Node)->void:
 if target==null:return
 execute_target=target;execute_timer=execute_window;execution_window_changed.emit(true)
func _execute_target()->bool:
 var target:=execute_target;execute_target=null;execute_timer=0.0;execution_window_changed.emit(false)
 if target==null or not is_instance_valid(target):return false
 var profile:=_profile_name();execute_visual.emit(profile)
 if target.has_method("melee_execute"):target.call("melee_execute",player,profile)
 elif target.has_method("apply_hit") and target is Node3D:target.call("apply_hit",target.global_position,-camera.global_transform.basis.z,9999.0,"heavy",10.0)
 melee_feedback.emit("EXECUTE");attack_timer=0.38;return true
func _push_apart(attacker:Node)->void:
 if not (attacker is Node3D) or player==null:return
 var away:=player.global_position-(attacker as Node3D).global_position;away.y=0.0
 if away.length_squared()<0.01:away=player.global_transform.basis.z
 away=away.normalized();player.velocity+=away*4.0
 if attacker is CharacterBody3D:(attacker as CharacterBody3D).velocity-=away*3.2
func _melee_trace(distance:float)->Dictionary:
 var world:=player.get_world_3d();if world==null:return {}
 var origin:=camera.global_position;var forward:=-camera.global_transform.basis.z;var query:=PhysicsRayQueryParameters3D.create(origin,origin+forward*distance);query.exclude=[player.get_rid()];query.collide_with_areas=false;return world.direct_space_state.intersect_ray(query)
func _profile_name()->String:
 if weapon and "weapon_name" in weapon:return String(weapon.weapon_name)
 return "UNARMED"
func is_guarding()->bool:return guarding
func current_guard()->String:return guard_line
