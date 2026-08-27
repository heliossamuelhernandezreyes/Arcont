extends Node3D

const ENEMY_SCENE:=preload("res://scenes/enemy.tscn")
const RANGED_SCENE:=preload("res://scenes/ranged_enemy.tscn")
const XENO_LANCER_SCENE:=preload("res://scenes/xeno_lancer.tscn")
const XENO_STALKER_SCENE:=preload("res://scenes/xeno_stalker.tscn")
@export var first_wave_size:=8
@export var wave_growth:=4
@export var time_between_waves:=2.5
@export var mobile_enemy_cap:=36
@export var desktop_enemy_cap:=64
var wave:=0
var alive:=0
var waiting_for_next_wave:=false
var game_over:=false
var mission_complete:=false
var enemy_pool:Array[Node]=[]
var spawn_points:Array[Node3D]=[]
@onready var player:Node3D=$Player
@onready var weapon:Node=$Player/CameraRig/Camera3D/Weapon
@onready var budget:Node=$PerformanceBudget
@onready var feedback:Node=$CombatFeedback
@onready var mission:Node=$MissionDirector
@onready var wave_label:Label=$HUD/Wave
@onready var alive_label:Label=$HUD/Alive
@onready var health_label:Label=$HUD/Health
@onready var ammo_label:Label=$HUD/Ammo
@onready var reload_label:Label=$HUD/Reload
@onready var weapon_label:Label=$HUD/WeaponName
@onready var info_label:Label=$HUD/Info
func _ready()->void:
 player.add_to_group("player");player.health_changed.connect(_on_player_health_changed);player.died.connect(_on_player_died)
 weapon.ammo_changed.connect(_on_ammo_changed);weapon.reload_state_changed.connect(_on_reload_state_changed);weapon.weapon_changed.connect(_on_weapon_changed)
 weapon.shot_fired.connect(feedback.on_shot_fired);weapon.impact_feedback.connect(feedback.on_hit_feedback);budget.profile_changed.connect(_on_performance_profile_changed)
 if mission.has_signal("mission_completed"):mission.mission_completed.connect(_on_mission_completed)
 _collect_spawn_points();_on_player_health_changed(player.health,player.max_health);_on_ammo_changed(weapon.ammo_in_mag,weapon.reserve_ammo,weapon.magazine_size);_on_weapon_changed(weapon.weapon_name,weapon.slot);_start_next_wave()
func _collect_spawn_points()->void:
 spawn_points.clear()
 for node in get_tree().get_nodes_in_group("enemy_spawn"):
  if node is Node3D:spawn_points.append(node as Node3D)
func _enemy_cap()->int:return mobile_enemy_cap if OS.has_feature("mobile") else desktop_enemy_cap
func _start_next_wave()->void:
 if waiting_for_next_wave or game_over or mission_complete:return
 wave+=1;var count:=mini(first_wave_size+(wave-1)*wave_growth,_enemy_cap());alive=count
 for i in count:_spawn_enemy(i,count)
 _update_hud()
func spawn_reinforcements(requested_count:int)->void:
 if requested_count<=0 or game_over or mission_complete:return
 var count:=mini(requested_count,maxi(_enemy_cap()-alive,0));var start:=alive;alive+=count
 for i in count:_spawn_enemy(start+i,maxi(alive,1))
 _update_hud()
func spawn_ranged_enemies(requested_count:int)->void:
 if requested_count<=0 or game_over or mission_complete:return
 var count:=mini(requested_count,maxi(_enemy_cap()-alive,0))
 for i in count:
  var ranged:=RANGED_SCENE.instantiate();ranged.died.connect(_on_special_enemy_died);$Enemies.add_child(ranged);ranged.global_position=_spawn_position_for(alive+i+5,maxi(alive+count,1))
 alive+=count;_update_hud()
func spawn_xeno_lancers(requested_count:int)->void:
 if requested_count<=0 or game_over or mission_complete:return
 var count:=mini(requested_count,maxi(_enemy_cap()-alive,0))
 for i in count:
  var lancer:=XENO_LANCER_SCENE.instantiate();lancer.died.connect(_on_special_enemy_died);$Enemies.add_child(lancer);lancer.global_position=_spawn_position_for(alive+i+7,maxi(alive+count,1))
 alive+=count;_update_hud()
func spawn_xeno_stalkers(requested_count:int)->void:
 if requested_count<=0 or game_over or mission_complete:return
 var count:=mini(requested_count,maxi(_enemy_cap()-alive,0))
 for i in count:
  var stalker:=XENO_STALKER_SCENE.instantiate();stalker.died.connect(_on_special_enemy_died);$Enemies.add_child(stalker);stalker.global_position=_spawn_position_for(alive+i+11,maxi(alive+count,1))
 alive+=count;_update_hud()
func spawn_brute()->Node:
 if game_over or mission_complete or alive>=_enemy_cap():return null
 var brute:=ENEMY_SCENE.instantiate();brute.name="BruteInfected";brute.set("max_health",420.0);brute.set("move_speed",3.0);brute.set("contact_damage",22.0);brute.set("head_health",125.0);brute.set("arm_health",90.0);brute.set("leg_health",110.0);brute.scale=Vector3.ONE*1.42
 brute.died.connect(_on_special_enemy_died);$Enemies.add_child(brute);brute.activate(_spawn_position_for(alive+3,maxi(alive+1,1)),player,budget.ai_interval*1.15,budget.gore_parts);alive+=1;_update_hud();return brute
func _spawn_enemy(index:int,total:int)->void:
 var enemy:Node
 if enemy_pool.is_empty():enemy=ENEMY_SCENE.instantiate();enemy.died.connect(_on_enemy_died);$Enemies.add_child(enemy)
 else:enemy=enemy_pool.pop_back()
 var pos:=_spawn_position_for(index,total)
 if enemy.has_method("activate"):enemy.activate(pos,player,budget.ai_interval,budget.gore_parts)
 else:enemy.position=pos
func _spawn_position_for(index:int,total:int)->Vector3:
 if not spawn_points.is_empty():
  var stride:=maxi(1,spawn_points.size()/maxi(mini(total,spawn_points.size()),1));var point_index:=(index*stride+wave)%spawn_points.size();return spawn_points[point_index].global_position+Vector3(randf_range(-1.1,1.1),0,randf_range(-1.1,1.1))
 var angle:=TAU*float(index)/maxf(float(total),1.0);return Vector3(cos(angle)*24.0,0.2,sin(angle)*24.0)
func _on_enemy_died(enemy:Node)->void:
 alive=maxi(alive-1,0);enemy.deactivate();if not enemy_pool.has(enemy):enemy_pool.append(enemy);_update_hud();_check_wave_clear()
func _on_special_enemy_died(enemy:Node)->void:
 alive=maxi(alive-1,0);if is_instance_valid(enemy) and not enemy.is_queued_for_deletion():enemy.queue_free();_update_hud();_check_wave_clear()
func _check_wave_clear()->void:
 if alive==0 and not waiting_for_next_wave and not game_over and not mission_complete:waiting_for_next_wave=true;await get_tree().create_timer(time_between_waves).timeout;waiting_for_next_wave=false;_start_next_wave()
func _on_mission_completed()->void:mission_complete=true;waiting_for_next_wave=false;wave_label.text="EXTRACCION"
func _on_performance_profile_changed(ai_interval:float,gore_parts:int)->void:
 for enemy in get_tree().get_nodes_in_group("enemies_active"):
  if enemy.has_method("set_performance_profile"):enemy.set_performance_profile(ai_interval,gore_parts)
func _on_player_health_changed(current:float,maximum:float)->void:health_label.text="VIDA %03d / %03d"%[roundi(current),roundi(maximum)]
func _on_player_died()->void:game_over=true;info_label.text="ARCONT // OPERADOR CAIDO\nDistrito de evacuación comprometido";reload_label.text=""
func _on_ammo_changed(current:int,reserve:int,_magazine_size:int)->void:ammo_label.text="%02d / %03d"%[current,reserve]
func _on_reload_state_changed(active:bool)->void:reload_label.text="RECARGANDO..." if active else ""
func _on_weapon_changed(name:String,slot_index:int)->void:weapon_label.text="%d // %s"%[slot_index+1,name]
func _update_hud()->void:
 if not mission_complete:wave_label.text="OLEADA %02d"%wave
 alive_label.text="HOSTILES %02d"%alive
