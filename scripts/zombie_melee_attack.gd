extends Node
class_name ZombieMeleeAttack

@export var attack_range:=1.28
@export var cooldown:=0.92
@export var windup_high:=0.42
@export var windup_mid:=0.26
@export var windup_low:=0.40
@export var recovery:=0.34

var host:CharacterBody3D
var target:Node3D
var body:Node3D
var arm_l:Node3D
var arm_r:Node3D
var base_body_rot:=Vector3.ZERO
var base_arm_l_rot:=Vector3.ZERO
var base_arm_r_rot:=Vector3.ZERO
var state:="idle"
var line:="mid"
var timer:=0.0
var cooldown_timer:=0.0
var base_damage:=8.0

func _ready()->void:
 host=get_parent() as CharacterBody3D
 if host==null:return
 target=get_tree().get_first_node_in_group("player") as Node3D
 body=host.get_node_or_null("Body") as Node3D;arm_l=host.get_node_or_null("ArmL") as Node3D;arm_r=host.get_node_or_null("ArmR") as Node3D
 if body:base_body_rot=body.rotation
 if arm_l:base_arm_l_rot=arm_l.rotation
 if arm_r:base_arm_r_rot=arm_r.rotation
 base_damage=float(host.get("contact_damage"));host.set("contact_damage",0.0)

func _physics_process(delta:float)->void:
 if host==null or bool(host.get("dead")) or not bool(host.get("active")):return
 cooldown_timer=maxf(cooldown_timer-delta,0.0)
 if target==null or not is_instance_valid(target):target=get_tree().get_first_node_in_group("player") as Node3D
 if state=="idle":
  _restore_pose(delta)
  if target and cooldown_timer<=0.0 and host.global_position.distance_to(target.global_position)<=attack_range:_begin_attack()
  return
 timer=maxf(timer-delta,0.0)
 if state=="windup":
  _apply_telegraph_pose()
  if timer<=0.0:_resolve_attack()
 elif state=="recovery":
  _restore_pose(delta)
  if timer<=0.0:state="idle"

func _begin_attack()->void:
 if bool(host.get("crawling")):line="low"
 else:
  var roll:=randf()
  line="mid" if roll<0.46 else ("high" if roll<0.73 else "low")
 state="windup";timer=_windup_for(line);cooldown_timer=cooldown

func _windup_for(value:String)->float:
 if value=="high":return windup_high
 if value=="low":return windup_low
 return windup_mid

func _apply_telegraph_pose()->void:
 var progress:=1.0-clampf(timer/maxf(_windup_for(line),0.01),0.0,1.0)
 var a:=smoothstep(0.0,1.0,progress)
 if body:
  var target_rot:=base_body_rot
  if line=="high":target_rot.x+=deg_to_rad(-16.0)
  elif line=="mid":target_rot.y+=deg_to_rad(10.0)
  else:target_rot.x+=deg_to_rad(20.0)
  body.rotation=base_body_rot.lerp(target_rot,a)
 if arm_l and arm_r:
  var left:=base_arm_l_rot;var right:=base_arm_r_rot
  if line=="high":left.x=deg_to_rad(-38.0);right.x=deg_to_rad(-46.0);left.z+=deg_to_rad(-24.0);right.z+=deg_to_rad(24.0)
  elif line=="mid":left.x=deg_to_rad(104.0);right.x=deg_to_rad(104.0);left.z+=deg_to_rad(18.0);right.z-=deg_to_rad(18.0)
  else:left.x=deg_to_rad(132.0);right.x=deg_to_rad(126.0);left.z+=deg_to_rad(10.0);right.z-=deg_to_rad(10.0)
  arm_l.rotation=base_arm_l_rot.lerp(left,a);arm_r.rotation=base_arm_r_rot.lerp(right,a)

func _resolve_attack()->void:
 if target and host.global_position.distance_to(target.global_position)<=attack_range+0.18:
  var damage:=base_damage
  if line=="high":damage*=1.18
  elif line=="mid":damage*=0.72
  else:damage*=0.92
  var result:Dictionary={"result":"hit","damage":damage}
  var melee:=target.get_node_or_null("MeleeCombat")
  if melee and melee.has_method("receive_melee_attack"):result=melee.receive_melee_attack(line,host,damage)
  var outcome:=String(result.get("result","hit"))
  if outcome=="hit" and target.has_method("apply_damage"):
   var push:=target.global_position-host.global_position;push.y=0.0;target.apply_damage(float(result.get("damage",damage)),push.normalized())
  elif outcome=="block":
   if target.has_method("apply_damage"):
    var push:=target.global_position-host.global_position;push.y=0.0;target.apply_damage(float(result.get("damage",damage*0.28)),push.normalized())
  elif outcome=="parry":host.set("stagger_timer",maxf(float(host.get("stagger_timer")),0.72))
  elif outcome=="mid_parry":host.set("stagger_timer",maxf(float(host.get("stagger_timer")),float(result.get("advantage",0.2))+0.18))
 state="recovery";timer=recovery

func _restore_pose(delta:float)->void:
 var alpha:=minf(delta*12.0,1.0)
 if body:body.rotation=body.rotation.lerp(base_body_rot,alpha)
 if arm_l:arm_l.rotation=arm_l.rotation.lerp(base_arm_l_rot,alpha)
 if arm_r:arm_r.rotation=arm_r.rotation.lerp(base_arm_r_rot,alpha)

func current_attack_line()->String:return line if state=="windup" else ""
func is_telegraphing()->bool:return state=="windup"
