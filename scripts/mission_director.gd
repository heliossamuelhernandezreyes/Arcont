extends Node
signal mission_completed
const STAGE_GENERATOR:=0
const STAGE_DEFEND:=1
const STAGE_SUPPLIES:=2
const STAGE_EVAC:=3
const STAGE_COMPLETE:=4
@export var generator_position:=Vector3(-10.0,0.0,14.5)
@export var supply_position:=Vector3(13.0,0.0,-13.0)
@export var evac_position:=Vector3(-0.5,0.0,-29.0)
@export var interact_radius:=2.4
@export var generator_activate_time:=2.2
@export var defend_duration:=28.0
@export var defend_radius:=7.0
@export var reinforcement_interval:=8.0
var stage:=STAGE_GENERATOR
var generator_progress:=0.0
var defend_remaining:=28.0
var reinforcement_timer:=0.0
var blackout_triggered:=false
var radio_warning_triggered:=false
var brute_triggered:=false
var xeno_pulse_triggered:=false
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
var moon_light:DirectionalLight3D
var emergency_light:OmniLight3D
var moon_base_energy:=1.65
var emergency_base_energy:=2.1
func _ready()->void:
 player=get_parent().get_node("Player") as Node3D
 weapon=player.get_node_or_null("Weapon")
 companion=get_parent().get_node_or_null("CompanionRobot")
 objective_label=get_parent().get_node("HUD/Objective") as Label
 info_label=get_parent().get_node("HUD/Info") as Label
 moon_light=get_parent().get_node_or_null("MoonLight") as DirectionalLight3D
 emergency_light=get_parent().get_node_or_null("EmergencyLight") as OmniLight3D
 if moon_light:moon_base_energy=moon_light.light_energy
 if emergency_light:emergency_base_energy=emergency_light.light_energy
 defend_remaining=defend_duration;_build_objective_props();_set_stage(STAGE_GENERATOR)
func _process(delta:float)->void:
 if player==null or not is_instance_valid(player):return
 match stage:
  STAGE_GENERATOR:_update_generator(delta)
  STAGE_DEFEND:_update_defense(delta)
  STAGE_SUPPLIES:_update_supplies()
  STAGE_EVAC:_update_evac()
func _update_generator(delta:float)->void:
 var distance:=player.global_position.distance_to(generator_position)
 if distance<=interact_radius:
  generator_progress=minf(generator_progress+delta,generator_activate_time);objective_label.text="OBJETIVO // REACTIVANDO GENERADOR %d%%"%roundi(generator_progress/generator_activate_time*100.0)
  if generator_progress>=generator_activate_time:_generator_activated()
 else:generator_progress=maxf(generator_progress-delta*0.35,0.0);objective_label.text="OBJETIVO // REACTIVA EL GENERADOR  •  %.0f m"%distance
func _generator_activated()->void:
 generator_light.light_color=Color(0.18,0.85,0.38);generator_light.light_energy=3.0
 if companion and companion.has_method("activate_unit"):companion.activate_unit()
 info_label.text="RADIO // ENERGIA RESTAURADA\nR-3 CUSTODIO REACTIVADO · FIRMA HOSTIL EN AUMENTO";_request_reinforcements(10);_set_stage(STAGE_DEFEND)
func _update_defense(delta:float)->void:
 var distance:=player.global_position.distance_to(generator_position)
 if distance>defend_radius:objective_label.text="OBJETIVO // REGRESA AL GENERADOR  •  %.0f m"%distance;return
 defend_remaining=maxf(defend_remaining-delta,0.0);reinforcement_timer+=delta
 if reinforcement_timer>=reinforcement_interval:reinforcement_timer=0.0;_request_reinforcements(4)
 _trigger_defense_events();objective_label.text="OBJETIVO // DEFIENDE EL GENERADOR  •  %02d s"%ceili(defend_remaining)
 if defend_remaining<=0.0:_defense_complete()
func _trigger_defense_events()->void:
 var elapsed:=defend_duration-defend_remaining
 if elapsed>=4.0 and not blackout_triggered:blackout_triggered=true;_trigger_blackout()
 if elapsed>=8.0 and not ranged_triggered:ranged_triggered=true;info_label.text="R-3 // CONTACTOS ARMADOS\nTIRADORES TOMAN POSICIONES";_request_ranged(2)
 if elapsed>=11.0 and not radio_warning_triggered:radio_warning_triggered=true;info_label.text="RADIO // FUEGO DE SUPRESION EN EJE NORTE\nUSE COBERTURA, NO QUEDE FIJO"
 if elapsed>=15.0 and not brute_triggered:brute_triggered=true;_spawn_brute_event()
 if elapsed>=18.0 and not lancer_triggered:lancer_triggered=true;_spawn_lancer_event()
 if elapsed>=20.5 and not stalker_triggered:stalker_triggered=true;_spawn_stalker_event()
 if elapsed>=22.0 and not xeno_pulse_triggered:xeno_pulse_triggered=true;_trigger_xeno_pulse()
func _trigger_blackout()->void:
 info_label.text="RADIO // FALLO DE RED\nAPAGON LOCAL · INTERFERENCIA XENOLOGICA"
 if moon_light:moon_light.light_energy=maxf(moon_base_energy*0.20,0.28)
 if emergency_light:emergency_light.light_energy=maxf(emergency_base_energy*0.20,0.28)
 await get_tree().create_timer(3.2).timeout
 if moon_light:moon_light.light_energy=moon_base_energy
 if emergency_light:emergency_light.light_energy=emergency_base_energy
func _spawn_brute_event()->void:
 info_label.text="R-3 // ALERTA DE MASA\nCONTACTO PESADO · CLASIFICACION BRUTE"
 if get_parent().has_method("spawn_brute"):get_parent().spawn_brute()
func _spawn_lancer_event()->void:info_label.text="R-3 // FIRMA NO HUMANA CONFIRMADA\nXENO LANCER CARGANDO ARMA ENERGETICA";_request_xeno(1)
func _spawn_stalker_event()->void:info_label.text="R-3 // CONTACTO XENO CERCANO\nSTALKER ENTRANDO A DISTANCIA DE CUERPO A CUERPO";_request_stalker(1)
func _trigger_xeno_pulse()->void:
 info_label.text="RADIO // PULSO XENOLOGICO\nINFECTADOS Y UNIDADES XENO CONVERGIENDO";_request_reinforcements(6);_request_xeno(1);_request_stalker(1)
 if generator_light:generator_light.light_color=Color(0.64,0.12,1.0);generator_light.light_energy=4.0
 await get_tree().create_timer(1.4).timeout
 if generator_light and stage==STAGE_DEFEND:generator_light.light_color=Color(0.18,0.85,0.38);generator_light.light_energy=3.0
func _defense_complete()->void:
 generator_light.light_energy=1.7
 if supply_root:supply_root.visible=true
 info_label.text="RADIO // SEÑAL ESTABILIZADA\nSUMINISTROS LOCALIZADOS";_set_stage(STAGE_SUPPLIES)
func _update_supplies()->void:
 var distance:=player.global_position.distance_to(supply_position);objective_label.text="OBJETIVO // RECUPERA SUMINISTROS  •  %.0f m"%distance
 if distance<=interact_radius:_collect_supplies()
func _collect_supplies()->void:
 if weapon and weapon.has_method("add_ammo"):weapon.add_ammo(32)
 if player and player.has_method("heal"):player.heal(35.0)
 if companion and companion.has_method("heal"):companion.heal(70.0)
 if supply_root:supply_root.visible=false
 if evac_root:evac_root.visible=true
 if evac_light:evac_light.visible=true
 _request_reinforcements(8);_request_ranged(1);_request_xeno(1);_request_stalker(1);info_label.text="RADIO // PAQUETE RECUPERADO\nVENTANA DE EXTRACCION ABIERTA";_set_stage(STAGE_EVAC)
func _update_evac()->void:
 var distance:=player.global_position.distance_to(evac_position);objective_label.text="OBJETIVO // ALCANZA LA EXTRACCION  •  %.0f m"%distance
 if distance<=interact_radius+0.8:_complete_mission()
func _complete_mission()->void:stage=STAGE_COMPLETE;objective_label.text="MISION COMPLETADA // EXTRACCION CONFIRMADA";info_label.text="RADIO // OPERADOR Y R-3 EXTRAIDOS\nDISTRITO 07 PERDIDO";mission_completed.emit()
func _set_stage(next_stage:int)->void:
 stage=next_stage
 if stage==STAGE_DEFEND:defend_remaining=defend_duration;reinforcement_timer=0.0;blackout_triggered=false;radio_warning_triggered=false;brute_triggered=false;xeno_pulse_triggered=false;ranged_triggered=false;lancer_triggered=false;stalker_triggered=false
func _request_reinforcements(count:int)->void:
 if get_parent().has_method("spawn_reinforcements"):get_parent().spawn_reinforcements(count)
func _request_ranged(count:int)->void:
 if get_parent().has_method("spawn_ranged_enemies"):get_parent().spawn_ranged_enemies(count)
func _request_xeno(count:int)->void:
 if get_parent().has_method("spawn_xeno_lancers"):get_parent().spawn_xeno_lancers(count)
func _request_stalker(count:int)->void:
 if get_parent().has_method("spawn_xeno_stalkers"):get_parent().spawn_xeno_stalkers(count)
func _build_objective_props()->void:
 generator_root=Node3D.new();generator_root.name="GeneratorObjective";generator_root.position=generator_position;get_parent().add_child.call_deferred(generator_root)
 generator_light=OmniLight3D.new();generator_light.light_color=Color(0.65,0.12,0.08);generator_light.light_energy=1.8;generator_light.omni_range=8.0;generator_root.add_child(generator_light)
 supply_root=Node3D.new();supply_root.name="SupplyObjective";supply_root.position=supply_position;supply_root.visible=false;get_parent().add_child.call_deferred(supply_root)
 evac_root=Node3D.new();evac_root.name="EvacObjective";evac_root.position=evac_position;evac_root.visible=false;get_parent().add_child.call_deferred(evac_root)
 evac_light=OmniLight3D.new();evac_light.light_color=Color(0.12,0.55,1.0);evac_light.light_energy=2.4;evac_light.omni_range=10.0;evac_light.visible=false;evac_root.add_child(evac_light)
