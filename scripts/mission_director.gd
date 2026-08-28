extends Node
signal mission_completed
const STAGE_GENERATOR:=0
const STAGE_DEFEND:=1
const STAGE_SUPPLIES:=2
const STAGE_EVAC:=3
const STAGE_COMPLETE:=4
@export var generator_position:=Vector3(-8.0,0.0,28.0)
@export var supply_position:=Vector3(10.0,0.0,-34.0)
@export var evac_position:=Vector3(0.0,0.0,-64.0)
@export var interact_radius:=2.4
@export var generator_activate_time:=2.2
@export var defend_duration:=28.0
@export var defend_radius:=7.0
@export var reinforcement_interval:=8.0
var stage:=STAGE_GENERATOR
var generator_progress:=0.0
var defend_remaining:=28.0
var reinforcement_timer:=0.0
var brute_triggered:=false
var ranged_triggered:=false
var lancer_triggered:=false
var stalker_triggered:=false
var player:Node3D
var weapon:Node
var companion:Node
var objective_label:Label
var info_label:Label
var generator_root:Node3D
var supply_root:Node3D
var evac_root:Node3D
var generator_light:OmniLight3D
var evac_light:OmniLight3D

func _ready()->void:
 player=get_parent().get_node("Player") as Node3D
 weapon=player.get_node_or_null("Weapon")
 companion=get_parent().get_node_or_null("CompanionRobot")
 objective_label=get_parent().get_node("HUD/Objective") as Label
 info_label=get_parent().get_node("HUD/Info") as Label
 defend_remaining=defend_duration
 _build_objective_props()
 _set_stage(STAGE_GENERATOR)

func _process(delta:float)->void:
 if player==null or not is_instance_valid(player):return
 match stage:
  STAGE_GENERATOR:_update_generator(delta)
  STAGE_DEFEND:_update_defense(delta)
  STAGE_SUPPLIES:_update_supplies()
  STAGE_EVAC:_update_evac()
  STAGE_COMPLETE:pass

func _objective_world_position(local_position:Vector3)->Vector3:
 var parent_3d:=get_parent() as Node3D
 return parent_3d.to_global(local_position) if parent_3d else local_position
func _objective_distance(local_position:Vector3)->float:
 if player==null:return 0.0
 var distance:=player.global_position.distance_to(_objective_world_position(local_position))
 if is_nan(distance) or is_inf(distance):return 0.0
 return clampf(distance,0.0,9999.0)

func _update_generator(delta:float)->void:
 var distance:=_objective_distance(generator_position)
 if distance<=interact_radius:
  generator_progress=minf(generator_progress+delta,generator_activate_time)
  objective_label.text="OBJETIVO // REACTIVANDO GENERADOR %d%%"%roundi(generator_progress/generator_activate_time*100.0)
  if generator_progress>=generator_activate_time:_generator_activated()
 else:
  generator_progress=maxf(generator_progress-delta*0.35,0.0)
  objective_label.text="OBJETIVO // REACTIVA EL GENERADOR  •  %.0f m"%distance

func _generator_activated()->void:
 generator_light.light_color=Color(0.18,0.85,0.38);generator_light.light_energy=3.0
 if companion and companion.has_method("activate_unit"):companion.activate_unit()
 info_label.text="RADIO // ENERGIA RESTAURADA\nR-3 CUSTODIO REACTIVADO"
 _request_reinforcements(6);_set_stage(STAGE_DEFEND)

func _update_defense(delta:float)->void:
 var distance:=_objective_distance(generator_position)
 if distance>defend_radius:
  objective_label.text="OBJETIVO // REGRESA AL GENERADOR  •  %.0f m"%distance;return
 defend_remaining=maxf(defend_remaining-delta,0.0);reinforcement_timer+=delta
 if reinforcement_timer>=reinforcement_interval:
  reinforcement_timer=0.0;_request_reinforcements(3)
 _trigger_defense_events();objective_label.text="OBJETIVO // DEFIENDE EL GENERADOR  •  %02d s"%ceili(defend_remaining)
 if defend_remaining<=0.0:_defense_complete()

func _trigger_defense_events()->void:
 var elapsed:=defend_duration-defend_remaining
 if elapsed>=8.0 and not ranged_triggered:ranged_triggered=true;_request_ranged(2)
 if elapsed>=15.0 and not brute_triggered:brute_triggered=true;_spawn_brute_event()
 if elapsed>=18.0 and not lancer_triggered:lancer_triggered=true;_request_xeno(1)
 if elapsed>=20.5 and not stalker_triggered:stalker_triggered=true;_request_stalker(1)
func _spawn_brute_event()->void:
 if get_parent().has_method("spawn_brute"):get_parent().spawn_brute()
func _defense_complete()->void:
 generator_light.light_energy=1.7
 if supply_root:supply_root.visible=true
 _set_stage(STAGE_SUPPLIES)
func _update_supplies()->void:
 var distance:=_objective_distance(supply_position);objective_label.text="OBJETIVO // RECUPERA SUMINISTROS  •  %.0f m"%distance
 if distance<=interact_radius:_collect_supplies()
func _collect_supplies()->void:
 if weapon and weapon.has_method("add_ammo"):weapon.add_ammo(32)
 if player and player.has_method("heal"):player.heal(35.0)
 if supply_root:supply_root.visible=false
 if evac_root:evac_root.visible=true
 if evac_light:evac_light.visible=true
 _set_stage(STAGE_EVAC)
func _update_evac()->void:
 var distance:=_objective_distance(evac_position);objective_label.text="OBJETIVO // ALCANZA LA EXTRACCION  •  %.0f m"%distance
 if distance<=interact_radius+0.8:_complete_mission()
func _complete_mission()->void:
 stage=STAGE_COMPLETE;objective_label.text="MISION COMPLETADA // EXTRACCION CONFIRMADA";mission_completed.emit()
func _set_stage(next_stage:int)->void:stage=next_stage
func _request_reinforcements(count:int)->void:
 if get_parent().has_method("spawn_reinforcements"):get_parent().spawn_reinforcements(count)
func _request_ranged(count:int)->void:
 if get_parent().has_method("spawn_ranged_enemies"):get_parent().spawn_ranged_enemies(count)
func _request_xeno(count:int)->void:
 if get_parent().has_method("spawn_xeno_lancers"):get_parent().spawn_xeno_lancers(count)
func _request_stalker(count:int)->void:
 if get_parent().has_method("spawn_xeno_stalkers"):get_parent().spawn_xeno_stalkers(count)

func _build_objective_props()->void:
 generator_root=Node3D.new();generator_root.position=generator_position;get_parent().add_child.call_deferred(generator_root)
 generator_light=OmniLight3D.new();generator_light.light_color=Color(1,0.25,0.12);generator_light.light_energy=2.5;generator_light.omni_range=9.0;generator_root.add_child(generator_light)
 supply_root=Node3D.new();supply_root.position=supply_position;supply_root.visible=false;get_parent().add_child.call_deferred(supply_root)
 evac_root=Node3D.new();evac_root.position=evac_position;evac_root.visible=false;get_parent().add_child.call_deferred(evac_root)
 evac_light=OmniLight3D.new();evac_light.light_color=Color(0.15,0.55,1);evac_light.light_energy=3.0;evac_light.omni_range=10.0;evac_root.add_child(evac_light)
