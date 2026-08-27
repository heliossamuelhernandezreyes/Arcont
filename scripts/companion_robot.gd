extends CharacterBody3D
signal health_changed(current:float,maximum:float)
signal downed
signal rebooted
signal command_changed(command:String)
@export var max_health:=140.0
@export var move_speed:=5.0
@export var acceleration:=12.0
@export var follow_distance:=3.6
@export var teleport_distance:=22.0
@export var scan_range:=18.0
@export var fire_range:=16.0
@export var fire_interval:=0.32
@export var shot_damage:=11.0
@export var impact_force:=2.5
@export var reboot_delay:=10.0
@export var robot_fire_noise_radius:=10.0
var health:=140.0
var active:=false
var down:=false
var emp_remaining:=0.0
var fire_timer:=0.0
var reboot_timer:=0.0
var gravity:float=ProjectSettings.get_setting("physics/3d/default_gravity")
var player:Node3D
var target:Node3D
var awareness:Node
var command:="FOLLOW"
var hold_position:=Vector3.ZERO
@onready var body_mesh:MeshInstance3D=$Body
@onready var turret:Node3D=$Turret
@onready var status_light:OmniLight3D=$StatusLight
@onready var collision:CollisionShape3D=$Collision
func _ready()->void:
	health=max_health;player=get_tree().get_first_node_in_group("player") as Node3D;var scene:=get_tree().current_scene;if scene:awareness=scene.get_node_or_null("AwarenessDirector");add_to_group("friendly_companion");collision.set_deferred("disabled",true);_set_active_visual(false)
func _unhandled_input(event:InputEvent)->void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode==KEY_G:cycle_command()
func activate_unit()->void:
	active=true;down=false;emp_remaining=0.0;health=max_health;reboot_timer=0.0;collision.set_deferred("disabled",false);_set_active_visual(true);set_command("FOLLOW");health_changed.emit(health,max_health);rebooted.emit()
func set_command(next_command:String)->void:
	var normalized:=next_command.to_upper();if normalized not in ["FOLLOW","HOLD","ASSAULT"]:return
	command=normalized;if command=="HOLD":hold_position=global_position;status_light.light_color=_command_color(command);command_changed.emit(command)
func cycle_command()->void:
	match command:
		"FOLLOW":set_command("HOLD")
		"HOLD":set_command("ASSAULT")
		_:set_command("FOLLOW")
func apply_emp(duration:float)->void:
	if down or not active:return
	emp_remaining=maxf(emp_remaining,duration);fire_timer=maxf(fire_timer,duration);velocity=Vector3.ZERO;status_light.light_color=Color(0.2,0.65,1.0);status_light.light_energy=0.25
func _physics_process(delta:float)->void:
	if down:reboot_timer-=delta;if reboot_timer<=0.0:activate_unit();return
	if not active:return
	if emp_remaining>0.0:
		emp_remaining=maxf(emp_remaining-delta,0.0)
		if not is_on_floor():velocity.y-=gravity*delta
		move_and_slide()
		if emp_remaining<=0.0:status_light.light_color=_command_color(command);status_light.light_energy=1.2
		return
	fire_timer=maxf(fire_timer-delta,0.0);if not is_on_floor():velocity.y-=gravity*delta;_update_combat();_update_follow(delta);move_and_slide()
func _update_follow(delta:float)->void:
	if player==null or not is_instance_valid(player):player=get_tree().get_first_node_in_group("player") as Node3D;return
	var desired:=Vector3.ZERO
	if command=="HOLD":var to_hold:=hold_position-global_position;to_hold.y=0.0;if to_hold.length()>0.55:desired=to_hold.normalized()*move_speed*0.8
	elif command=="ASSAULT" and target!=null and is_instance_valid(target):var to_enemy:=target.global_position-global_position;to_enemy.y=0.0;if to_enemy.length()>fire_range*0.62:desired=to_enemy.normalized()*move_speed
	else:
		var offset:=player.global_position-global_position;offset.y=0.0;var distance:=offset.length()
		if distance>teleport_distance and command=="FOLLOW":global_position=player.global_position+Vector3(-2.0,0.2,2.0);velocity=Vector3.ZERO;return
		if distance>follow_distance:desired=offset.normalized()*move_speed
	velocity.x=move_toward(velocity.x,desired.x,acceleration*delta);velocity.z=move_toward(velocity.z,desired.z,acceleration*delta);if desired.length_squared()>0.01:look_at(global_position+Vector3(desired.x,0.0,desired.z),Vector3.UP)
func _update_combat()->void:
	target=_nearest_enemy();if target==null:return
	var distance:=global_position.distance_to(target.global_position);if distance>fire_range:return
	var aim_position:=target.global_position+Vector3.UP*0.95;turret.look_at(aim_position,Vector3.UP)
	if fire_timer<=0.0 and _has_line_of_sight(target,aim_position):fire_timer=fire_interval;_fire_at(target,aim_position)
func _nearest_enemy()->Node3D:
	var best:Node3D;var best_distance:=scan_range*(1.35 if command=="ASSAULT" else 1.0)
	for node in get_tree().get_nodes_in_group("enemies_active"):
		if not node is Node3D:continue
		var candidate:=node as Node3D;var distance:=global_position.distance_to(candidate.global_position);if distance<best_distance:best_distance=distance;best=candidate
	return best
func _has_line_of_sight(candidate:Node3D,aim_position:Vector3)->bool:
	var world:=get_world_3d();if world==null:return false
	var query:=PhysicsRayQueryParameters3D.create(turret.global_position,aim_position);query.exclude=[get_rid()];query.collide_with_areas=false;var result:=world.direct_space_state.intersect_ray(query);return result.is_empty() or result.get("collider")==candidate
func _fire_at(candidate:Node3D,aim_position:Vector3)->void:
	var direction:=(aim_position-turret.global_position).normalized();if candidate.has_method("apply_hit"):candidate.apply_hit(aim_position,direction,shot_damage,"robot",impact_force)
	if awareness and awareness.has_method("report_sound"):awareness.report_sound(global_position,robot_fire_noise_radius,"robot_fire")
	status_light.light_energy=3.2;get_tree().create_timer(0.045).timeout.connect(_restore_status_light)
func _restore_status_light()->void:
	if is_instance_valid(status_light):status_light.light_energy=1.2 if active and not down and emp_remaining<=0.0 else 0.15
func apply_damage(amount:float,_push_direction:=Vector3.ZERO)->void:
	if down or not active:return
	health=maxf(health-amount,0.0);health_changed.emit(health,max_health);if health<=0.0:_down_unit()
func heal(amount:float)->void:
	if down:return
	health=minf(health+amount,max_health);health_changed.emit(health,max_health)
func _down_unit()->void:
	down=true;active=false;reboot_timer=reboot_delay;velocity=Vector3.ZERO;collision.set_deferred("disabled",true);status_light.light_color=Color(1.0,0.08,0.04);status_light.light_energy=0.4;body_mesh.rotation_degrees.z=80.0;downed.emit()
func _set_active_visual(value:bool)->void:
	body_mesh.rotation=Vector3.ZERO;status_light.light_color=_command_color(command) if value else Color(0.18,0.20,0.22);status_light.light_energy=1.2 if value else 0.15
func _command_color(value:String)->Color:
	match value:
		"HOLD":return Color(1.0,0.68,0.10)
		"ASSAULT":return Color(1.0,0.18,0.08)
		_:return Color(0.12,0.75,1.0)
