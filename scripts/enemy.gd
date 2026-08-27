extends CharacterBody3D
signal died(enemy:Node)
signal limb_lost(enemy:Node,limb:String)
signal staggered(enemy:Node,duration:float)
signal knocked_down(enemy:Node,duration:float)
signal crawl_started(enemy:Node)
@export var max_health:=100.0
@export var move_speed:=2.4
@export var acceleration:=10.0
@export var contact_damage:=8.0
@export var attack_cooldown:=0.8
@export var separation_radius:=1.15
@export var separation_strength:=1.35
@export var head_health:=42.0
@export var leg_health:=44.0
@export var knockback_decay:=9.0
@export var max_knockback_speed:=7.5
var health:=100.0
var target:Node3D
var gravity:float=ProjectSettings.get_setting("physics/3d/default_gravity")
var attack_timer:=0.0
var dead:=false
var active:=true
var desired_direction:=Vector3.ZERO
var external_velocity:=Vector3.ZERO
var stagger_timer:=0.0
var knockdown_timer:=0.0
var crawling:=false
var leg_l_disabled:=false
var leg_r_disabled:=false
@onready var collision:CollisionShape3D=$Collision
@onready var body_mesh:MeshInstance3D=$Body
@onready var head_mesh:MeshInstance3D=$Head
@onready var arm_l_mesh:MeshInstance3D=$ArmL
@onready var arm_r_mesh:MeshInstance3D=$ArmR
func _ready()->void:health=max_health;target=get_tree().get_first_node_in_group("player") as Node3D;add_to_group("enemies_active")
func activate(at_position:Vector3,new_target:Node3D,_new_ai_interval:=0.08,_new_gore_parts:=6)->void:global_position=at_position;target=new_target;dead=false;active=true;visible=true;health=max_health;velocity=Vector3.ZERO;external_velocity=Vector3.ZERO;stagger_timer=0.0;knockdown_timer=0.0;crawling=false;leg_l_disabled=false;leg_r_disabled=false;collision.set_deferred("disabled",false);set_physics_process(true);if not is_in_group("enemies_active"):add_to_group("enemies_active")
func deactivate()->void:active=false;dead=true;visible=false;velocity=Vector3.ZERO;if is_in_group("enemies_active"):remove_from_group("enemies_active");collision.set_deferred("disabled",true);set_physics_process(false)
func set_performance_profile(_new_ai_interval:float,_new_gore_parts:int)->void:pass
func _physics_process(delta:float)->void:
 if dead or not active:return
 attack_timer=maxf(attack_timer-delta,0.0);stagger_timer=maxf(stagger_timer-delta,0.0);knockdown_timer=maxf(knockdown_timer-delta,0.0)
 if not is_on_floor():velocity.y-=gravity*delta
 _update_ai_direction()
 var locomotion:=Vector3.ZERO
 if stagger_timer<=0.0 and knockdown_timer<=0.0:locomotion=desired_direction*move_speed*(0.25 if crawling else (0.58 if leg_l_disabled or leg_r_disabled else 1.0))
 velocity.x=move_toward(velocity.x,locomotion.x+external_velocity.x,acceleration*delta);velocity.z=move_toward(velocity.z,locomotion.z+external_velocity.z,acceleration*delta);external_velocity=external_velocity.move_toward(Vector3.ZERO,knockback_decay*delta);move_and_slide()
func _update_ai_direction()->void:
 if target==null or not is_instance_valid(target):target=get_tree().get_first_node_in_group("player") as Node3D;return
 var to_target:=target.global_position-global_position;to_target.y=0.0;desired_direction=to_target.normalized() if to_target.length()>0.05 else Vector3.ZERO
 if desired_direction.length_squared()>0.001:look_at(global_position+desired_direction,Vector3.UP)
 if to_target.length()<(1.05 if crawling else 1.25) and attack_timer<=0.0 and stagger_timer<=0.0 and knockdown_timer<=0.0:
  attack_timer=attack_cooldown
  if target.has_method("apply_damage"):target.apply_damage(contact_damage,to_target.normalized())
func receive_melee_attack(line:String,profile:String,attacker:Node,direction:Vector3)->Dictionary:
 if dead:return {"result":"dead"}
 # Zombies never guard or parry: player attacks always resolve.
 if line=="high":_die(direction,"head");return {"result":"kill","zone":"head"}
 if line=="low":
  leg_l_disabled=true;knockdown_timer=2.2;stagger_timer=1.0;external_velocity+=direction.normalized()*3.0
  if attacker and attacker.has_node("MeleeCombat"):attacker.get_node("MeleeCombat").call("open_execution",self)
  return {"result":"knockdown","zone":"legs"}
 var damage:=42.0 if "BAYONET" in profile else 34.0;health-=damage;stagger_timer=0.45;external_velocity+=direction.normalized()*4.0
 if health<=0.0:_die(direction,"torso")
 return {"result":"hit","zone":"torso","damage":damage}
func force_knockdown(duration:=1.35)->void:knockdown_timer=maxf(knockdown_timer,duration);stagger_timer=maxf(stagger_timer,duration*0.5)
func melee_execute(_attacker:Node,profile:String)->void:
 if dead:return
 _die(Vector3.FORWARD,"head" if "BAYONET" in profile else "torso")
func apply_hit(hit_point:Vector3,shot_direction:Vector3,base_damage:=34.0,damage_type:="ballistic",impact_force:=1.0)->void:
 if dead or not active:return
 var local_hit:=to_local(hit_point);var zone:="head" if local_hit.y>1.38 else ("leg_l" if local_hit.y<0.52 and local_hit.x<0.0 else ("leg_r" if local_hit.y<0.52 else "torso"));var mult:=2.4 if zone=="head" else (0.75 if zone.begins_with("leg") else 1.0);var damage:=base_damage*mult;health-=damage
 stagger_timer=maxf(stagger_timer,0.3 if zone=="head" else 0.18);var horizontal:=shot_direction;horizontal.y=0.0;if horizontal.length_squared()>0.01:external_velocity+=horizontal.normalized()*clampf((damage/24.0)*impact_force,0.35,max_knockback_speed)
 if zone=="leg_l" and damage>=leg_health:leg_l_disabled=true;force_knockdown()
 if zone=="leg_r" and damage>=leg_health:leg_r_disabled=true;force_knockdown()
 if leg_l_disabled and leg_r_disabled:crawling=true
 if health<=0.0:_die(shot_direction,zone)
func _die(_shot_direction:Vector3,_zone:String)->void:
 if dead:return
 dead=true;active=false;velocity=Vector3.ZERO;died.emit(self);collision.set_deferred("disabled",true);set_physics_process(false);visible=false
