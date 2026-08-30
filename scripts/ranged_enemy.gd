extends CharacterBody3D

signal died(enemy: Node)
@export var max_health := 120.0
@export var move_speed := 3.6
@export var preferred_distance := 13.0
@export var fire_range := 24.0
@export var fire_interval := 1.15
@export var shot_damage := 16.0
@export var accuracy_spread := 0.04
@export var penetration_energy := 0.72
@export var suppression_radius := 1.65
@export var decision_interval := 0.85
@export var visual_memory_seconds := 7.0
@export var hearing_age_seconds := 3.0
var health := 120.0
var player: Node3D
var awareness: Node
var navigation: Node
var fire_timer := 0.0
var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var active := true
var role := "suppress"
var decision_timer := 0.0
var tactical_target := Vector3.ZERO
var has_tactical_target := false
var last_known_position := Vector3.ZERO
var memory_remaining := 0.0
var has_visual_contact := false
var awareness_state := "idle"

func _ready() -> void:
	health = max_health
	player = get_tree().get_first_node_in_group("player") as Node3D
	var scene := get_tree().current_scene
	if scene:
		awareness = scene.get_node_or_null("AwarenessDirector")
		navigation = scene.get_node_or_null("NavigationGraph")
	add_to_group("ranged_enemy"); add_to_group("tactical_enemy"); add_to_group("enemies_active")
	role = TacticalAI.squad_role(self)
	decision_timer = randf_range(0.05, decision_interval)

func _physics_process(delta: float) -> void:
	if not active:return
	if player==null or not is_instance_valid(player):
		player=get_tree().get_first_node_in_group("player") as Node3D
		return
	_update_awareness(delta)
	fire_timer=maxf(fire_timer-delta,0.0)
	decision_timer-=delta
	if decision_timer<=0.0:
		decision_timer=decision_interval+randf_range(-0.18,0.24)
		_choose_tactic()
	if not is_on_floor():velocity.y-=gravity*delta
	var desired:=_movement_velocity()
	velocity.x=move_toward(velocity.x,desired.x,8.0*delta)
	velocity.z=move_toward(velocity.z,desired.z,8.0*delta)
	var face_target:=player.global_position if has_visual_contact else last_known_position
	var flat:=face_target-global_position;flat.y=0.0
	if flat.length_squared()>0.1:look_at(global_position+flat,Vector3.UP)
	move_and_slide()
	if has_visual_contact and global_position.distance_to(player.global_position)<=fire_range and fire_timer<=0.0:_try_fire()

func _update_awareness(delta: float) -> void:
	has_visual_contact=TacticalAI.has_line_of_sight(self,player)
	if has_visual_contact:
		last_known_position=player.global_position
		memory_remaining=visual_memory_seconds
		awareness_state="contact"
		return
	memory_remaining=maxf(memory_remaining-delta,0.0)
	if awareness and awareness.has_method("recent_sound_for"):
		var heard:Dictionary=awareness.recent_sound_for(global_position,hearing_age_seconds)
		if not heard.is_empty() and float(heard.get("age",99.0))<0.35:
			last_known_position=heard.get("position",player.global_position)
			memory_remaining=maxf(memory_remaining,4.5)
			awareness_state="investigate"
			return
	if awareness and awareness.has_method("shared_intel_for"):
		var intel:Dictionary=awareness.shared_intel_for("armed",5.5)
		if not intel.is_empty() and float(intel.get("age",99.0))<1.8:
			last_known_position=intel.get("position",last_known_position)
			memory_remaining=maxf(memory_remaining,4.0)
			awareness_state="radio_search"
			return
	if memory_remaining>0.0:
		awareness_state="search"
	else:
		awareness_state="idle"
		has_tactical_target=false

func _choose_tactic() -> void:
	if player==null:return
	role=TacticalAI.squad_role(self)
	if awareness_state=="idle":
		has_tactical_target=false
		return
	var target_reference:=player.global_position if has_visual_contact else last_known_position
	if not has_visual_contact:
		tactical_target=target_reference
		has_tactical_target=true
		return
	if role=="suppress":
		if global_position.distance_to(player.global_position)<=fire_range*0.95:
			has_tactical_target=false
			return
		var cover:=TacticalAI.best_cover(self,player,preferred_distance,26.0)
		if cover!=Vector3.INF:
			tactical_target=cover;has_tactical_target=true
		return
	if role=="anchor":
		_choose_anchor_tactic()
		return
	var side:=-1.0 if role=="flank_left" else 1.0
	var flank:=TacticalAI.flank_point(self,player,side,preferred_distance*0.9)
	var flank_cover:=TacticalAI.best_cover_near(self,player,flank,preferred_distance,30.0)
	tactical_target=flank_cover if flank_cover!=Vector3.INF else flank
	has_tactical_target=true

func _choose_anchor_tactic()->void:
	var distance:=global_position.distance_to(player.global_position)
	if distance>=preferred_distance-2.5 and distance<=preferred_distance+4.0 and TacticalAI.point_has_cover(self,player,global_position):
		has_tactical_target=false
		return
	var anchor_cover:=TacticalAI.best_cover_near(self,player,global_position,preferred_distance,18.0)
	if anchor_cover!=Vector3.INF and anchor_cover.distance_to(global_position)>0.9:
		tactical_target=anchor_cover
		has_tactical_target=true
	else:
		has_tactical_target=false

func _movement_velocity()->Vector3:
	if player==null or awareness_state=="idle":return Vector3.ZERO
	if has_tactical_target:
		var waypoint:=_next_navigation_point(tactical_target)
		var to_target:=waypoint-global_position;to_target.y=0.0
		if global_position.distance_to(tactical_target)<1.0:
			has_tactical_target=false
			if not has_visual_contact and awareness_state!="contact":memory_remaining=minf(memory_remaining,1.2)
			return Vector3.ZERO
		return to_target.normalized()*move_speed if to_target.length_squared()>0.01 else Vector3.ZERO
	if not has_visual_contact:return _velocity_to(last_known_position)
	var flat:=player.global_position-global_position;flat.y=0.0
	var distance:=flat.length()
	if role=="anchor":
		if distance>preferred_distance+5.0:return _velocity_to(player.global_position)*0.72
		if distance<preferred_distance-4.0:return -flat.normalized()*move_speed*0.55
		return Vector3.ZERO
	if distance>preferred_distance+3.0:return _velocity_to(player.global_position)
	if distance<preferred_distance-3.0:return -flat.normalized()*move_speed*0.7
	return Vector3.ZERO

func _velocity_to(target_position:Vector3)->Vector3:
	var waypoint:=_next_navigation_point(target_position)
	var delta:=waypoint-global_position;delta.y=0.0
	return delta.normalized()*move_speed if delta.length_squared()>0.01 else Vector3.ZERO

func _next_navigation_point(target_position:Vector3)->Vector3:
	if navigation and navigation.has_method("next_waypoint"):return navigation.next_waypoint(global_position,target_position,1.15)
	return target_position

func _try_fire()->void:
	var world:=get_world_3d()
	if world==null or player==null:return
	var cadence:=0.78 if role=="suppress" else (1.12 if role=="anchor" else 1.0)
	fire_timer=fire_interval*cadence
	var origin:=global_position+Vector3.UP*1.25
	var aim:=player.global_position+Vector3.UP*0.65
	var spread:=accuracy_spread*(0.82 if role=="suppress" else (0.88 if role=="anchor" else 1.0))
	aim+=Vector3(randf_range(-spread,spread),randf_range(-spread,spread),randf_range(-spread,spread))*origin.distance_to(aim)
	var direction:=(aim-origin).normalized()
	_trace_round(world.direct_space_state,origin,direction)
	_apply_near_miss_suppression(origin,origin+direction*fire_range)

func _trace_round(space_state:PhysicsDirectSpaceState3D,origin:Vector3,direction:Vector3)->void:
	var energy:=penetration_energy;var current_origin:=origin;var exclude:Array[RID]=[get_rid()]
	for _pass in 2:
		var query:=PhysicsRayQueryParameters3D.create(current_origin,current_origin+direction*fire_range);query.exclude=exclude;query.collide_with_areas=false
		var result:=space_state.intersect_ray(query)
		if result.is_empty():return
		var collider:Object=result.get("collider");var hit_point:Vector3=result.get("position",current_origin)
		if collider==player and player.has_method("apply_damage"):
			var scale:=Ballistics.damage_scale(energy,penetration_energy)
			player.apply_damage(shot_damage*scale,direction,_pick_hit_zone(),scale)
			if player.has_method("apply_suppression"):player.apply_suppression(0.72,0.85)
			return
		Ballistics.apply_surface_damage(collider,shot_damage,energy,hit_point,direction)
		var new_energy:=Ballistics.energy_after_surface(energy,collider)
		if new_energy<=0.05:return
		energy=new_energy
		if collider is CollisionObject3D:exclude.append((collider as CollisionObject3D).get_rid())
		current_origin=hit_point+direction*(Ballistics.thickness_for(collider)+0.08)

func _apply_near_miss_suppression(from:Vector3,to:Vector3)->void:
	if player==null or not player.has_method("apply_suppression"):return
	var point:=player.global_position+Vector3.UP*0.7;var segment:=to-from;var denom:=segment.length_squared()
	if denom<=0.001:return
	var t:=clampf((point-from).dot(segment)/denom,0.0,1.0);var closest:=from+segment*t;var distance:=closest.distance_to(point)
	if distance<=suppression_radius:
		var intensity:=lerpf(0.18,0.58,1.0-distance/suppression_radius)
		if role=="suppress":intensity*=1.18
		player.apply_suppression(intensity,0.55)

func _pick_hit_zone()->String:
	var roll:=randf()
	if roll<0.08:return "head"
	if roll<0.58:return "torso"
	if roll<0.73:return "left_arm"
	if roll<0.88:return "right_arm"
	return "left_leg" if randf()<0.5 else "right_leg"

func apply_hit(_hit_point:Vector3,direction:Vector3,amount:float,_weapon_type:="shotgun",impact_force:=1.0)->void:
	if not active:return
	health=maxf(health-amount,0.0);velocity+=direction.normalized()*impact_force*0.12
	last_known_position=player.global_position if player else global_position
	memory_remaining=visual_memory_seconds
	awareness_state="search"
	if health<=0.0:
		active=false;remove_from_group("enemies_active");remove_from_group("tactical_enemy");died.emit(self);queue_free()
