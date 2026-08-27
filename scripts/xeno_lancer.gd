extends CharacterBody3D

signal died(enemy: Node)

@export var max_health := 180.0
@export var move_speed := 3.0
@export var preferred_distance := 17.0
@export var fire_range := 30.0
@export var fire_interval := 2.25
@export var charge_time := 0.68
@export var energy_damage := 24.0
@export var energy_power := 1.18
@export var suppression_radius := 2.6
@export var accuracy_spread := 0.022
@export var decision_interval := 1.0
@export var visual_memory_seconds := 8.5
@export var hearing_age_seconds := 3.5

@onready var core_light: OmniLight3D = $CoreLight
var health := 180.0
var player: Node3D
var awareness: Node
var navigation: Node
var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var fire_timer := 0.8
var charging := false
var charge_remaining := 0.0
var active := true
var role := "suppress"
var decision_timer := 0.0
var tactical_target := Vector3.ZERO
var has_tactical_target := false
var last_known_position := Vector3.ZERO
var memory_remaining := 0.0
var has_visual_contact := false
var awareness_state := "idle"

func _ready()->void:
	health=max_health
	player=get_tree().get_first_node_in_group("player") as Node3D
	var scene:=get_tree().current_scene
	if scene:
		awareness=scene.get_node_or_null("AwarenessDirector")
		navigation=scene.get_node_or_null("NavigationGraph")
	add_to_group("xeno_enemy");add_to_group("tactical_enemy");add_to_group("enemies_active")
	role=TacticalAI.squad_role(self);decision_timer=randf_range(0.1,decision_interval)

func _physics_process(delta:float)->void:
	if not active:return
	if player==null or not is_instance_valid(player):player=get_tree().get_first_node_in_group("player") as Node3D;return
	_update_awareness(delta)
	if not is_on_floor():velocity.y-=gravity*delta
	fire_timer=maxf(fire_timer-delta,0.0);decision_timer-=delta
	if decision_timer<=0.0 and not charging:
		decision_timer=decision_interval+randf_range(-0.2,0.3);_choose_tactic()
	var desired:=Vector3.ZERO if charging else _movement_velocity()
	velocity.x=move_toward(velocity.x,desired.x,7.0*delta);velocity.z=move_toward(velocity.z,desired.z,7.0*delta)
	var face_target:=player.global_position if has_visual_contact else last_known_position
	var flat:=face_target-global_position;flat.y=0.0
	if flat.length_squared()>0.1:look_at(global_position+flat,Vector3.UP)
	move_and_slide()
	if charging:
		charge_remaining-=delta;core_light.light_energy=lerpf(2.2,7.0,1.0-clampf(charge_remaining/charge_time,0.0,1.0))
		if charge_remaining<=0.0:_fire_lance()
	elif has_visual_contact and global_position.distance_to(player.global_position)<=fire_range and fire_timer<=0.0:_begin_charge()

func _update_awareness(delta:float)->void:
	has_visual_contact=TacticalAI.has_line_of_sight(self,player,1.35,0.72)
	if has_visual_contact:
		last_known_position=player.global_position;memory_remaining=visual_memory_seconds;awareness_state="contact";return
	memory_remaining=maxf(memory_remaining-delta,0.0)
	if awareness and awareness.has_method("recent_sound_for"):
		var heard:Dictionary=awareness.recent_sound_for(global_position,hearing_age_seconds)
		if not heard.is_empty() and float(heard.get("age",99.0))<0.4:
			last_known_position=heard.get("position",player.global_position);memory_remaining=maxf(memory_remaining,5.5);awareness_state="investigate";return
	if awareness and awareness.has_method("shared_intel_for"):
		var intel:Dictionary=awareness.shared_intel_for("armed",6.0)
		if not intel.is_empty() and float(intel.get("age",99.0))<2.0:
			last_known_position=intel.get("position",last_known_position);memory_remaining=maxf(memory_remaining,5.0);awareness_state="radio_search";return
	if memory_remaining>0.0:awareness_state="search"
	else:
		awareness_state="idle";has_tactical_target=false
		if charging:charging=false;core_light.light_energy=1.4

func _choose_tactic()->void:
	if player==null:return
	role=TacticalAI.squad_role(self)
	if awareness_state=="idle":has_tactical_target=false;return
	if not has_visual_contact:
		tactical_target=last_known_position;has_tactical_target=true;return
	if role=="suppress":
		var cover:=TacticalAI.best_cover(self,player,preferred_distance,30.0)
		if cover!=Vector3.INF and global_position.distance_to(player.global_position)>fire_range*0.82:tactical_target=cover;has_tactical_target=true
		else:has_tactical_target=false
		return
	var side:=-1.0 if role=="flank_left" else 1.0
	var flank:=TacticalAI.flank_point(self,player,side,preferred_distance)
	var cover:=TacticalAI.best_cover_near(self,player,flank,preferred_distance,32.0)
	tactical_target=cover if cover!=Vector3.INF else flank;has_tactical_target=true

func _movement_velocity()->Vector3:
	if player==null or awareness_state=="idle":return Vector3.ZERO
	if has_tactical_target:
		var waypoint:=_next_navigation_point(tactical_target);var to_target:=waypoint-global_position;to_target.y=0.0
		if global_position.distance_to(tactical_target)<1.1:
			has_tactical_target=false
			if not has_visual_contact:memory_remaining=minf(memory_remaining,1.5)
			return Vector3.ZERO
		return to_target.normalized()*move_speed if to_target.length_squared()>0.01 else Vector3.ZERO
	if not has_visual_contact:return _velocity_to(last_known_position)
	var flat:=player.global_position-global_position;flat.y=0.0;var distance:=flat.length()
	if distance>preferred_distance+3.0:return _velocity_to(player.global_position)
	if distance<preferred_distance-3.0:return -flat.normalized()*move_speed*0.75
	return Vector3.ZERO

func _velocity_to(target_position:Vector3)->Vector3:
	var waypoint:=_next_navigation_point(target_position);var delta:=waypoint-global_position;delta.y=0.0
	return delta.normalized()*move_speed if delta.length_squared()>0.01 else Vector3.ZERO

func _next_navigation_point(target_position:Vector3)->Vector3:
	if navigation and navigation.has_method("next_waypoint"):return navigation.next_waypoint(global_position,target_position,1.15)
	return target_position

func _begin_charge()->void:
	charging=true;charge_remaining=charge_time;velocity.x*=0.35;velocity.z*=0.35;core_light.light_color=Color(0.86,0.12,1.0);core_light.light_energy=2.2

func _fire_lance()->void:
	charging=false;fire_timer=fire_interval*(0.88 if role=="suppress" else 1.0);core_light.light_energy=1.4
	if player==null or not has_visual_contact:return
	var world:=get_world_3d()
	if world==null:return
	var origin:=global_position+Vector3.UP*1.35;var target_position:=player.global_position+Vector3.UP*0.72;var distance:=origin.distance_to(target_position)
	target_position+=Vector3(randf_range(-accuracy_spread,accuracy_spread),randf_range(-accuracy_spread,accuracy_spread),randf_range(-accuracy_spread,accuracy_spread))*distance
	_trace_energy(world.direct_space_state,origin,(target_position-origin).normalized())

func _trace_energy(space_state:PhysicsDirectSpaceState3D,origin:Vector3,direction:Vector3)->void:
	var energy:=energy_power;var current_origin:=origin;var exclude:Array[RID]=[get_rid()];var final_point:=origin+direction*fire_range
	for _pass in 3:
		var query:=PhysicsRayQueryParameters3D.create(current_origin,current_origin+direction*fire_range);query.exclude=exclude;query.collide_with_areas=false
		var result:=space_state.intersect_ray(query)
		if result.is_empty():break
		var collider:Object=result.get("collider");var hit_point:Vector3=result.get("position",final_point);final_point=hit_point
		if collider==player and player.has_method("apply_damage"):
			var scale:=Ballistics.damage_scale(energy,energy_power);player.apply_damage(energy_damage*scale,direction,_pick_hit_zone(),1.15*scale)
			if player.has_method("apply_suppression"):player.apply_suppression(0.92,1.05)
			break
		Ballistics.apply_energy_surface_damage(collider,energy_damage,energy,hit_point,direction)
		var next_energy:=Ballistics.xeno_energy_after_surface(energy,collider)
		if next_energy<=0.08:break
		energy=next_energy
		if collider is CollisionObject3D:exclude.append((collider as CollisionObject3D).get_rid())
		current_origin=hit_point+direction*(Ballistics.thickness_for(collider)+0.10)
	_apply_energy_suppression(origin,final_point);_spawn_lance_visual(origin,final_point)

func _apply_energy_suppression(from:Vector3,to:Vector3)->void:
	if player==null or not player.has_method("apply_suppression"):return
	var point:=player.global_position+Vector3.UP*0.7;var segment:=to-from
	if segment.length_squared()<=0.001:return
	var t:=clampf((point-from).dot(segment)/segment.length_squared(),0.0,1.0);var distance:=(from+segment*t).distance_to(point)
	if distance<=suppression_radius:
		var amount:=lerpf(0.30,0.82,1.0-distance/suppression_radius)
		if role=="suppress":amount*=1.15
		player.apply_suppression(amount,0.82)

func _spawn_lance_visual(from:Vector3,to:Vector3)->void:
	var root:=get_tree().current_scene
	if root==null:return
	var length:=from.distance_to(to)
	if length<=0.05:return
	var beam:=MeshInstance3D.new();var mesh:=BoxMesh.new();mesh.size=Vector3(0.055,0.055,length);beam.mesh=mesh
	var mat:=StandardMaterial3D.new();mat.albedo_color=Color(0.72,0.06,1.0);mat.emission_enabled=true;mat.emission=Color(0.9,0.12,1.0);mat.emission_energy_multiplier=4.5;beam.material_override=mat
	root.add_child(beam);beam.global_position=(from+to)*0.5;beam.look_at(to,Vector3.UP);root.get_tree().create_timer(0.09).timeout.connect(beam.queue_free)

func _pick_hit_zone()->String:
	var roll:=randf()
	if roll<0.10:return "head"
	if roll<0.62:return "torso"
	if roll<0.76:return "left_arm"
	if roll<0.90:return "right_arm"
	return "left_leg" if randf()<0.5 else "right_leg"

func apply_hit(_hit_point:Vector3,direction:Vector3,amount:float,_weapon_type:="shotgun",impact_force:=1.0)->void:
	if not active:return
	health=maxf(health-amount,0.0);velocity+=direction.normalized()*impact_force*0.08
	last_known_position=player.global_position if player else global_position;memory_remaining=visual_memory_seconds;awareness_state="search"
	if health<=0.0:
		active=false;remove_from_group("enemies_active");remove_from_group("tactical_enemy");died.emit(self);queue_free()
