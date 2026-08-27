extends CharacterBody3D

signal died(enemy:Node)
@export var max_health:=145.0
@export var move_speed:=6.2
@export var attack_range:=2.15
@export var attack_cooldown:=0.72
@export var high_windup:=0.30
@export var mid_windup:=0.18
@export var low_windup:=0.31
@export var high_damage:=42.0
@export var mid_damage:=18.0
@export var low_damage:=30.0
@export var chain_gap:=0.14
@export var sidestep_speed:=7.6
@export var sidestep_duration:=0.19
@export var feint_hold:=0.105

@onready var body:Node3D=$Body
@onready var arm_l:Node3D=$ArmL
@onready var arm_r:Node3D=$ArmR
@onready var core:OmniLight3D=$CoreLight
var player:Node3D
var health:=145.0
var gravity:float=ProjectSettings.get_setting("physics/3d/default_gravity")
var cooldown_timer:=0.4
var state:="hunt"
var attack_line:="mid"
var attack_timer:=0.0
var recovery_timer:=0.0
var active:=true
var base_body_rot:=Vector3.ZERO
var base_l_rot:=Vector3.ZERO
var base_r_rot:=Vector3.ZERO
var guard_line:="mid"
var guard_timer:=0.0
var combo:Array[String]=[]
var combo_index:=0
var combo_pending:=false
var sequence_has_feint:=false
var feint_from:=""
var feint_to:=""
var feint_timer:=0.0
var sidestep_timer:=0.0
var sidestep_direction:=1.0

func _ready()->void:
 health=max_health;player=get_tree().get_first_node_in_group("player") as Node3D;base_body_rot=body.rotation;base_l_rot=arm_l.rotation;base_r_rot=arm_r.rotation
 add_to_group("xeno_enemy");add_to_group("tactical_enemy");add_to_group("enemies_active")

func _physics_process(delta:float)->void:
 if not active:return
 if player==null or not is_instance_valid(player):player=get_tree().get_first_node_in_group("player") as Node3D;return
 cooldown_timer=maxf(cooldown_timer-delta,0.0);guard_timer=maxf(guard_timer-delta,0.0)
 if not is_on_floor():velocity.y-=gravity*delta
 var flat:=player.global_position-global_position;flat.y=0.0;var distance:=flat.length()
 if flat.length_squared()>0.02:look_at(global_position+flat,Vector3.UP)
 match state:
  "hunt":
   _restore_pose(delta)
   velocity.x=move_toward(velocity.x,flat.normalized().x*move_speed if distance>1.55 else 0.0,14.0*delta);velocity.z=move_toward(velocity.z,flat.normalized().z*move_speed if distance>1.55 else 0.0,14.0*delta)
   if distance<=attack_range and cooldown_timer<=0.0:_begin_engagement()
  "sidestep":
   _update_sidestep(delta,flat)
  "feint":
   velocity.x=move_toward(velocity.x,0.0,18.0*delta);velocity.z=move_toward(velocity.z,0.0,18.0*delta);feint_timer=maxf(feint_timer-delta,0.0);_telegraph_pose_for(feint_from,1.0)
   core.light_energy=6.0 if fmod(feint_timer*1000.0,70.0)>35.0 else 1.0
   if feint_timer<=0.0:_commit_feint()
  "windup":
   velocity.x=move_toward(velocity.x,0.0,18.0*delta);velocity.z=move_toward(velocity.z,0.0,18.0*delta);attack_timer=maxf(attack_timer-delta,0.0);_telegraph_pose()
   if attack_timer<=0.0:_resolve_attack()
  "chain_gap":
   recovery_timer=maxf(recovery_timer-delta,0.0);_restore_pose(delta)
   if recovery_timer<=0.0:_begin_combo_strike()
  "recovery":
   recovery_timer=maxf(recovery_timer-delta,0.0);_restore_pose(delta)
   if recovery_timer<=0.0:state="hunt"
 move_and_slide()

func _begin_engagement()->void:
 _choose_sequence();cooldown_timer=attack_cooldown
 if randf()<0.46:
  state="sidestep";sidestep_timer=sidestep_duration;sidestep_direction=-1.0 if randf()<0.5 else 1.0;core.light_energy=2.8
 else:_begin_sequence()

func _choose_sequence()->void:
 combo.clear();combo_index=0;combo_pending=false;sequence_has_feint=false;feint_from="";feint_to=""
 var roll:=randf()
 if roll<0.24:combo=["high","mid"]
 elif roll<0.44:combo=["low","mid"]
 elif roll<0.62:combo=["mid","high"]
 elif roll<0.77:combo=["mid"]
 elif roll<0.89:
  sequence_has_feint=true;feint_from="high";feint_to="low";combo=["low"]
 else:
  sequence_has_feint=true;feint_from="low";feint_to="high";combo=["high"]

func _begin_sequence()->void:
 if sequence_has_feint:
  state="feint";feint_timer=feint_hold;attack_line=feint_from;core.light_energy=5.5
 else:_begin_combo_strike()

func _commit_feint()->void:
 attack_line=feint_to;state="windup";attack_timer=_windup_for(attack_line)*0.92;core.light_energy=5.2

func _begin_combo_strike()->void:
 if combo_index>=combo.size():_finish_sequence();return
 attack_line=combo[combo_index];state="windup"
 var chain_scale:=0.86 if combo_index>0 else 1.0
 attack_timer=_windup_for(attack_line)*chain_scale;core.light_energy=4.5

func _finish_sequence()->void:
 combo.clear();combo_index=0;combo_pending=false;sequence_has_feint=false;state="recovery";recovery_timer=0.30;core.light_energy=1.5

func _update_sidestep(delta:float,flat:Vector3)->void:
 sidestep_timer=maxf(sidestep_timer-delta,0.0)
 var forward:=flat.normalized() if flat.length_squared()>0.01 else -global_transform.basis.z
 var lateral:=Vector3(-forward.z,0.0,forward.x)*sidestep_direction
 velocity.x=move_toward(velocity.x,lateral.x*sidestep_speed,28.0*delta);velocity.z=move_toward(velocity.z,lateral.z*sidestep_speed,28.0*delta)
 body.rotation.z=lerpf(body.rotation.z,deg_to_rad(-9.0*sidestep_direction),minf(delta*18.0,1.0))
 if sidestep_timer<=0.0:_begin_sequence()

func _windup()->float:return _windup_for(attack_line)
func _windup_for(line:String)->float:
 if line=="high":return high_windup
 if line=="low":return low_windup
 return mid_windup

func _telegraph_pose()->void:
 var a:=smoothstep(0.0,1.0,1.0-attack_timer/maxf(_windup_for(attack_line),0.01));_telegraph_pose_for(attack_line,a)

func _telegraph_pose_for(line:String,a:float)->void:
 var br:=base_body_rot;var lr:=base_l_rot;var rr:=base_r_rot
 if line=="high":br.x+=deg_to_rad(-22.0);lr.x=deg_to_rad(-58.0);rr.x=deg_to_rad(-42.0);lr.z-=deg_to_rad(32.0)
 elif line=="mid":br.y+=deg_to_rad(-18.0);lr.x=deg_to_rad(98.0);rr.x=deg_to_rad(108.0);rr.z+=deg_to_rad(34.0)
 else:br.x+=deg_to_rad(24.0);lr.x=deg_to_rad(138.0);rr.x=deg_to_rad(130.0)
 body.rotation=body.rotation.lerp(br,clampf(a,0.0,1.0));arm_l.rotation=arm_l.rotation.lerp(lr,clampf(a,0.0,1.0));arm_r.rotation=arm_r.rotation.lerp(rr,clampf(a,0.0,1.0))
 core.light_color=Color(1.0,0.12,0.28) if line=="high" else (Color(1.0,0.72,0.12) if line=="mid" else Color(0.28,0.42,1.0))

func _resolve_attack()->void:
 var interrupted:=false
 if player and global_position.distance_to(player.global_position)<=attack_range+0.25:
  var damage:=high_damage if attack_line=="high" else (low_damage if attack_line=="low" else mid_damage)
  var result:Dictionary={"result":"hit","damage":damage};var melee:=player.get_node_or_null("MeleeCombat")
  if melee and melee.has_method("receive_melee_attack"):result=melee.receive_melee_attack(attack_line,self,damage)
  var outcome:=String(result.get("result","hit"))
  if outcome=="hit" and player.has_method("apply_damage"):
   var push:=player.global_position-global_position;push.y=0.0;player.apply_damage(float(result.get("damage",damage)),push.normalized())
  elif outcome=="block" and player.has_method("apply_damage"):
   var push:=player.global_position-global_position;push.y=0.0;player.apply_damage(float(result.get("damage",damage*0.28)),push.normalized())
  elif outcome=="parry":state="recovery";recovery_timer=0.78;core.light_energy=0.3;interrupted=true
  elif outcome=="mid_parry":state="recovery";recovery_timer=float(result.get("advantage",0.20))+0.20;core.light_energy=0.3;interrupted=true
 if interrupted:return
 combo_index+=1
 if combo_index<combo.size():state="chain_gap";recovery_timer=chain_gap;combo_pending=true;core.light_energy=2.1
 else:_finish_sequence()

func receive_melee_attack(line:String,_profile:String,attacker:Node,direction:Vector3)->Dictionary:
 if not active:return {"result":"dead"}
 if guard_timer<=0.0:guard_line=["high","mid","low"].pick_random();guard_timer=0.55+randf_range(0.0,0.35)
 if line==guard_line:
  velocity-=direction.normalized()*2.0
  return {"result":"block","damage":0.0}
 var damage:=999.0 if line=="high" else (46.0 if line=="low" else 38.0)
 health-=damage
 if line=="low":velocity+=direction.normalized()*4.0
 if health<=0.0:_die()
 return {"result":"hit","damage":damage}

func melee_execute(_attacker:Node,_profile:String)->void:_die()
func apply_hit(_point:Vector3,direction:Vector3,amount:float,_weapon_type:="ballistic",impact_force:=1.0)->void:
 if not active:return
 health=maxf(health-amount,0.0);velocity+=direction.normalized()*impact_force*0.12
 if health<=0.0:_die()
func apply_emp(duration:float)->void:
 cooldown_timer=maxf(cooldown_timer,duration);state="recovery";recovery_timer=maxf(recovery_timer,duration);combo.clear();combo_index=0;core.light_energy=0.2
func _die()->void:
 if not active:return
 active=false;remove_from_group("enemies_active");remove_from_group("tactical_enemy");died.emit(self);queue_free()
func _restore_pose(delta:float)->void:
 var a:=minf(delta*14.0,1.0);body.rotation=body.rotation.lerp(base_body_rot,a);arm_l.rotation=arm_l.rotation.lerp(base_l_rot,a);arm_r.rotation=arm_r.rotation.lerp(base_r_rot,a);core.light_color=Color(0.92,0.12,1.0);core.light_energy=lerpf(core.light_energy,1.5,a)
func current_attack_line()->String:return attack_line if state=="windup" or state=="feint" else ""
func is_telegraphing()->bool:return state=="windup" or state=="feint"
func is_feinting()->bool:return state=="feint"
func current_combo_step()->int:return combo_index
