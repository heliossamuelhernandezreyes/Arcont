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
 if state=="hunt":
  _restore_pose(delta)
  velocity.x=move_toward(velocity.x,flat.normalized().x*move_speed if distance>1.55 else 0.0,14.0*delta);velocity.z=move_toward(velocity.z,flat.normalized().z*move_speed if distance>1.55 else 0.0,14.0*delta)
  if distance<=attack_range and cooldown_timer<=0.0:_begin_attack()
 elif state=="windup":
  velocity.x=move_toward(velocity.x,0.0,18.0*delta);velocity.z=move_toward(velocity.z,0.0,18.0*delta);attack_timer=maxf(attack_timer-delta,0.0);_telegraph_pose()
  if attack_timer<=0.0:_resolve_attack()
 elif state=="recovery":
  recovery_timer=maxf(recovery_timer-delta,0.0);_restore_pose(delta)
  if recovery_timer<=0.0:state="hunt"
 move_and_slide()

func _begin_attack()->void:
 var roll:=randf();attack_line="mid" if roll<0.44 else ("high" if roll<0.72 else "low")
 state="windup";attack_timer=_windup();cooldown_timer=attack_cooldown;core.light_energy=4.5

func _windup()->float:
 if attack_line=="high":return high_windup
 if attack_line=="low":return low_windup
 return mid_windup

func _telegraph_pose()->void:
 var a:=smoothstep(0.0,1.0,1.0-attack_timer/maxf(_windup(),0.01));var br:=base_body_rot;var lr:=base_l_rot;var rr:=base_r_rot
 if attack_line=="high":br.x+=deg_to_rad(-22.0);lr.x=deg_to_rad(-58.0);rr.x=deg_to_rad(-42.0);lr.z-=deg_to_rad(32.0)
 elif attack_line=="mid":br.y+=deg_to_rad(-18.0);lr.x=deg_to_rad(98.0);rr.x=deg_to_rad(108.0);rr.z+=deg_to_rad(34.0)
 else:br.x+=deg_to_rad(24.0);lr.x=deg_to_rad(138.0);rr.x=deg_to_rad(130.0)
 body.rotation=base_body_rot.lerp(br,a);arm_l.rotation=base_l_rot.lerp(lr,a);arm_r.rotation=base_r_rot.lerp(rr,a)
 core.light_color=Color(1.0,0.12,0.28) if attack_line=="high" else (Color(1.0,0.72,0.12) if attack_line=="mid" else Color(0.28,0.42,1.0))

func _resolve_attack()->void:
 if player and global_position.distance_to(player.global_position)<=attack_range+0.25:
  var damage:=high_damage if attack_line=="high" else (low_damage if attack_line=="low" else mid_damage)
  var result:Dictionary={"result":"hit","damage":damage};var melee:=player.get_node_or_null("MeleeCombat")
  if melee and melee.has_method("receive_melee_attack"):result=melee.receive_melee_attack(attack_line,self,damage)
  var outcome:=String(result.get("result","hit"))
  if outcome=="hit" and player.has_method("apply_damage"):
   var push:=player.global_position-global_position;push.y=0.0;player.apply_damage(float(result.get("damage",damage)),push.normalized())
  elif outcome=="block" and player.has_method("apply_damage"):
   var push:=player.global_position-global_position;push.y=0.0;player.apply_damage(float(result.get("damage",damage*0.28)),push.normalized())
  elif outcome=="parry":state="recovery";recovery_timer=0.78;core.light_energy=0.3;return
  elif outcome=="mid_parry":state="recovery";recovery_timer=float(result.get("advantage",0.20))+0.20;core.light_energy=0.3;return
 state="recovery";recovery_timer=0.28;core.light_energy=1.5

func receive_melee_attack(line:String,_profile:String,attacker:Node,direction:Vector3)->Dictionary:
 if not active:return {"result":"dead"}
 # Stalker sí puede defenderse, pero cambia guardia por ráfagas: no lee mágicamente la entrada del jugador.
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
 cooldown_timer=maxf(cooldown_timer,duration);state="recovery";recovery_timer=maxf(recovery_timer,duration);core.light_energy=0.2
func _die()->void:
 if not active:return
 active=false;remove_from_group("enemies_active");remove_from_group("tactical_enemy");died.emit(self);queue_free()
func _restore_pose(delta:float)->void:
 var a:=minf(delta*14.0,1.0);body.rotation=body.rotation.lerp(base_body_rot,a);arm_l.rotation=arm_l.rotation.lerp(base_l_rot,a);arm_r.rotation=arm_r.rotation.lerp(base_r_rot,a);core.light_color=Color(0.92,0.12,1.0);core.light_energy=lerpf(core.light_energy,1.5,a)
func current_attack_line()->String:return attack_line if state=="windup" else ""
func is_telegraphing()->bool:return state=="windup"
