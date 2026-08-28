extends Node

signal ammo_changed(current:int,reserve:int,magazine_size:int)
signal reload_state_changed(active:bool)
signal recoil_requested(pitch:float,yaw:float)
signal shot_fired
signal impact_feedback(hit_point:Vector3,hit_normal:Vector3,organic:bool)
signal weapon_changed(name:String,slot:int)
signal ads_changed(active:bool)
signal active_reload_feedback(result:String,stage:int)

@onready var player:CharacterBody3D=get_parent() as CharacterBody3D
@onready var camera:Camera3D=player.get_node_or_null("CameraRig/SpringArm3D/Camera3D") as Camera3D
@onready var gun:MeshInstance3D=player.get_node_or_null("BodyVisual/WeaponMount/Gun") as MeshInstance3D
@onready var muzzle:Node3D=player.get_node_or_null("BodyVisual/WeaponMount/MuzzleFlash") as Node3D

var profiles:=[
 {"name":"12G SHOTGUN","mag":8,"reserve":48,"damage":18.0,"interval":0.72,"reload":1.9,"recoil_pitch":0.055,"recoil_yaw":0.016,"pellets":8,"spread":5.2,"range":55.0,"impact":8.5,"energy":0.95,"penetrations":2,"noise":34.0,"ads_fov":58.0,"automatic":false,"active":[[0.42,0.13,0.22],[0.78,0.12,0.24]]},
 {"name":"AR-5 RIFLE","mag":30,"reserve":150,"damage":27.0,"interval":0.105,"reload":2.15,"recoil_pitch":0.020,"recoil_yaw":0.008,"pellets":1,"spread":1.15,"range":92.0,"impact":3.8,"energy":1.20,"penetrations":3,"noise":30.0,"ads_fov":48.0,"automatic":true,"active":[[0.30,0.11,0.30],[0.66,0.10,0.34],[0.88,0.09,0.26]]},
 {"name":"P9 PISTOL","mag":15,"reserve":75,"damage":34.0,"interval":0.24,"reload":1.45,"recoil_pitch":0.028,"recoil_yaw":0.010,"pellets":1,"spread":1.65,"range":72.0,"impact":3.0,"energy":0.82,"penetrations":1,"noise":24.0,"ads_fov":52.0,"automatic":false,"active":[[0.38,0.12,0.28],[0.82,0.10,0.24]]},
 {"name":"M90 BOLT SNIPER","mag":5,"reserve":30,"damage":118.0,"interval":1.35,"reload":2.0,"recoil_pitch":0.075,"recoil_yaw":0.012,"pellets":1,"spread":0.34,"range":180.0,"impact":10.5,"energy":1.85,"penetrations":4,"noise":42.0,"ads_fov":28.0,"automatic":false,"active":[[0.30,0.095,0.68],[0.72,0.085,0.72]]},
 {"name":"BR-7 BAYONET RIFLE","mag":20,"reserve":100,"damage":38.0,"interval":0.16,"reload":2.25,"recoil_pitch":0.030,"recoil_yaw":0.009,"pellets":1,"spread":0.82,"range":105.0,"impact":4.8,"energy":1.38,"penetrations":3,"noise":32.0,"ads_fov":44.0,"automatic":false,"active":[[0.34,0.11,0.34],[0.76,0.10,0.40]]}
]
var slot:=0
var ammo_by_slot:=[8,30,15,5,20]
var reserve_by_slot:=[48,150,75,30,100]
var fire_timer:=0.0
var reload_timer:=0.0
var reload_total:=0.0
var reload_elapsed:=0.0
var reloading:=false
var active_stage:=0
var active_savings:=0.0
var aiming:=false
var base_fov:=72.0
var trigger_held:=false
var bolt_pending:=false
var bolt_timer:=0.0

var weapon_name:String:
 get:return String(profiles[slot]["name"])
var magazine_size:int:
 get:return int(profiles[slot]["mag"])
var reserve_ammo:int:
 get:return reserve_by_slot[slot]
 set(value):reserve_by_slot[slot]=value
var ammo_in_mag:int:
 get:return ammo_by_slot[slot]
 set(value):ammo_by_slot[slot]=value

func _ready()->void:
 base_fov=camera.fov if camera else 72.0
 _build_weapon_visual();_emit_state()

func _unhandled_input(event:InputEvent)->void:
 if DisplayServer.is_touchscreen_available():return
 if event is InputEventMouseButton:
  if event.button_index==MOUSE_BUTTON_LEFT:set_trigger(event.pressed)
  elif event.button_index==MOUSE_BUTTON_RIGHT:set_ads(event.pressed)
  elif event.pressed and event.button_index==MOUSE_BUTTON_WHEEL_UP:switch_weapon((slot+profiles.size()-1)%profiles.size())
  elif event.pressed and event.button_index==MOUSE_BUTTON_WHEEL_DOWN:cycle_weapon()
 if event is InputEventKey and event.pressed and not event.echo and event.keycode>=KEY_1 and event.keycode<=KEY_5:switch_weapon(event.keycode-KEY_1)

func _process(delta:float)->void:
 fire_timer=maxf(fire_timer-delta,0.0);bolt_timer=maxf(bolt_timer-delta,0.0)
 if bolt_pending and bolt_timer<=0.0:bolt_pending=false
 if reloading:
  reload_timer-=delta;reload_elapsed+=delta;_advance_missed_windows()
  if reload_timer<=0.0:_finish_reload()
 if trigger_held and bool(profiles[slot]["automatic"]):try_fire()
 if camera:camera.fov=lerpf(camera.fov,float(profiles[slot]["ads_fov"]) if aiming else base_fov,minf(delta*11.0,1.0))

func set_trigger(active:bool)->void:
 if active and not trigger_held:try_fire()
 trigger_held=active
func set_ads(active:bool)->void:
 if aiming==active:return
 aiming=active;ads_changed.emit(aiming)
func cycle_weapon()->void:switch_weapon((slot+1)%profiles.size())
func switch_weapon(next_slot:int)->void:
 var target:=clampi(next_slot,0,profiles.size()-1)
 if target==slot:return
 cancel_reload();slot=target;trigger_held=false;fire_timer=0.18;bolt_pending=false;_build_weapon_visual();_emit_state()

func try_fire()->bool:
 if reloading or fire_timer>0.0 or bolt_pending or camera==null:return false
 if ammo_in_mag<=0:request_reload();return false
 var p:Dictionary=profiles[slot];fire_timer=float(p["interval"]);ammo_in_mag-=1
 if slot==3:bolt_pending=true;bolt_timer=float(p["interval"])
 ammo_changed.emit(ammo_in_mag,reserve_ammo,magazine_size);shot_fired.emit();_report_weapon_sound()
 var recoil_mult:=float(player.get_recoil_multiplier()) if player and player.has_method("get_recoil_multiplier") else 1.0
 var ads_recoil:=0.78 if aiming else 1.0
 recoil_requested.emit(float(p["recoil_pitch"])*recoil_mult*ads_recoil,randf_range(-float(p["recoil_yaw"]),float(p["recoil_yaw"]))*recoil_mult*ads_recoil)
 _fire_weapon();return true

func _report_weapon_sound()->void:
 var scene:=get_tree().current_scene
 if scene==null:return
 var awareness:=scene.get_node_or_null("AwarenessDirector")
 if awareness and awareness.has_method("report_sound"):awareness.report_sound(player.global_position,float(profiles[slot]["noise"]),weapon_name.to_lower())

func _camera_aim_point(space_state:PhysicsDirectSpaceState3D,max_range:float,exclude:Array[RID])->Vector3:
 var camera_origin:=camera.global_position
 var camera_forward:=-camera.global_transform.basis.z
 var query:=PhysicsRayQueryParameters3D.create(camera_origin,camera_origin+camera_forward*max_range)
 query.exclude=exclude
 query.collide_with_areas=false
 var result:=space_state.intersect_ray(query)
 if result.is_empty():return camera_origin+camera_forward*max_range
 return result.get("position",camera_origin+camera_forward*max_range)

func _fire_weapon()->void:
 if camera==null:return
 var world:=camera.get_world_3d();if world==null:return
 var p:Dictionary=profiles[slot]
 var exclude:Array[RID]=[]
 if player:exclude.append(player.get_rid())
 var space_state:=world.direct_space_state
 var aim_point:=_camera_aim_point(space_state,float(p["range"]),exclude)
 var origin:=muzzle.global_position if muzzle else (gun.global_position if gun else camera.global_position)
 var base_direction:=(aim_point-origin).normalized()
 if base_direction.length_squared()<0.001:base_direction=-camera.global_transform.basis.z
 var right:=camera.global_transform.basis.x
 var up:=camera.global_transform.basis.y
 var spread_mult:=1.0
 if player and player.has_method("get_weapon_spread_multiplier"):spread_mult=float(player.get_weapon_spread_multiplier())
 if aiming:spread_mult*=0.48
 var spread:=tan(deg_to_rad(float(p["spread"])*spread_mult))
 for _i in int(p["pellets"]):
  var direction:=(base_direction+right*randf_range(-spread,spread)+up*randf_range(-spread,spread)).normalized()
  _trace_round(space_state,origin,direction,exclude,p)

func _trace_round(space_state:PhysicsDirectSpaceState3D,origin:Vector3,direction:Vector3,exclude:Array[RID],p:Dictionary)->void:
 var energy:=float(p["energy"]);var start_energy:=energy;var current_origin:=origin;var travelled:=0.0;var penetrations:=0;var local_exclude:=exclude.duplicate();var max_range:=float(p["range"])
 while energy>0.05 and travelled<max_range:
  var remaining:=max_range-travelled;var query:=PhysicsRayQueryParameters3D.create(current_origin,current_origin+direction*remaining);query.exclude=local_exclude;query.collide_with_areas=false;var result:=space_state.intersect_ray(query)
  if result.is_empty():return
  var collider:Object=result.get("collider");var hit_point:Vector3=result.get("position",current_origin);var hit_normal:Vector3=result.get("normal",-direction);travelled+=current_origin.distance_to(hit_point);var organic:=bool(collider!=null and collider.has_method("apply_hit"));impact_feedback.emit(hit_point,hit_normal,organic)
  if organic:
   var scale:=Ballistics.damage_scale(energy,start_energy);collider.apply_hit(hit_point,direction,float(p["damage"])*scale,weapon_name.to_lower(),float(p["impact"])*scale);return
  Ballistics.apply_surface_damage(collider,float(p["damage"]),energy,hit_point,direction);var new_energy:=Ballistics.energy_after_surface(energy,collider)
  if new_energy<=0.05 or penetrations>=int(p["penetrations"]):return
  energy=new_energy;penetrations+=1
  if collider is CollisionObject3D:local_exclude.append((collider as CollisionObject3D).get_rid())
  var skip:=Ballistics.thickness_for(collider)+0.08;current_origin=hit_point+direction*skip;travelled+=skip

func request_reload()->bool:
 if reloading:return active_reload_tap()
 if ammo_in_mag>=magazine_size or reserve_ammo<=0:return false
 var reload_mult:=float(player.get_reload_time_multiplier()) if player and player.has_method("get_reload_time_multiplier") else 1.0
 reloading=true;reload_total=float(profiles[slot]["reload"])*maxf(reload_mult,0.1);reload_timer=reload_total;reload_elapsed=0.0;active_stage=0;active_savings=0.0;reload_state_changed.emit(true);return true
func active_reload_tap()->bool:
 if not reloading:return false
 var windows:Array=profiles[slot].get("active",[])
 if active_stage>=windows.size():return false
 var data:Array=windows[active_stage];var center:=float(data[0])*reload_total;var half:=float(data[1])*reload_total;var distance:=absf(reload_elapsed-center)
 if distance<=half:
  var perfect:=distance<=half*0.42;var saving:=float(data[2])*(1.0 if perfect else 0.52);reload_timer=maxf(0.05,reload_timer-saving);active_savings+=saving;active_reload_feedback.emit("PERFECT" if perfect else "GOOD",active_stage);active_stage+=1;return true
 if reload_elapsed>center+half:active_reload_feedback.emit("MISS",active_stage);active_stage+=1
 return false
func _advance_missed_windows()->void:
 var windows:Array=profiles[slot].get("active",[])
 while active_stage<windows.size():
  var data:Array=windows[active_stage];var center:=float(data[0])*reload_total;var half:=float(data[1])*reload_total
  if reload_elapsed<=center+half:return
  active_reload_feedback.emit("MISS",active_stage);active_stage+=1
func get_active_reload_state()->Dictionary:
 var windows:Array=profiles[slot].get("active",[]);var next_center:=-1.0;var tolerance:=0.0
 if active_stage<windows.size():next_center=float(windows[active_stage][0]);tolerance=float(windows[active_stage][1])
 return {"active":reloading,"stage":active_stage,"stages":windows.size(),"progress":clampf(reload_elapsed/maxf(reload_total,0.01),0.0,1.0),"next":next_center,"tolerance":tolerance,"saved":active_savings,"weapon":weapon_name}
func _finish_reload()->void:
 var moved:=mini(magazine_size-ammo_in_mag,reserve_ammo);ammo_in_mag+=moved;reserve_ammo-=moved;reloading=false;reload_timer=0.0;reload_state_changed.emit(false);ammo_changed.emit(ammo_in_mag,reserve_ammo,magazine_size)
func cancel_reload()->void:
 if not reloading:return
 reloading=false;reload_timer=0.0;reload_state_changed.emit(false)
func add_ammo(amount:int)->void:
 if amount<=0:return
 reserve_ammo+=amount;ammo_changed.emit(ammo_in_mag,reserve_ammo,magazine_size)
func _emit_state()->void:ammo_changed.emit(ammo_in_mag,reserve_ammo,magazine_size);weapon_changed.emit(weapon_name,slot)
func _player_controller()->Node:return player

func _build_weapon_visual()->void:
 if gun==null:return
 gun.mesh=null
 for child in gun.get_children():child.queue_free()
 var steel:=_mat(Color(0.09,0.105,0.12),0.7,0.42);var dark:=_mat(Color(0.025,0.03,0.036),0.75,0.36);var polymer:=_mat(Color(0.11,0.125,0.115),0.08,0.78);var accent:=_mat(Color(0.34,0.17,0.06),0.12,0.64);var blade:=_mat(Color(0.45,0.49,0.52),0.85,0.22)
 match slot:
  0:
   _add_box(gun,"DetailReceiver",Vector3.ZERO,Vector3(0.24,0.18,0.54),steel);_add_box(gun,"DetailStock",Vector3(0,-0.01,0.40),Vector3(0.22,0.16,0.34),polymer);_add_cylinder(gun,"DetailBarrel",Vector3(0,0.03,-0.58),0.05,0.92,dark);_add_box(gun,"DetailPump",Vector3(0,-0.07,-0.32),Vector3(0.19,0.14,0.28),accent)
  1:
   _add_box(gun,"DetailReceiver",Vector3.ZERO,Vector3(0.22,0.17,0.50),steel);_add_box(gun,"DetailMagazine",Vector3(0,-0.18,-0.04),Vector3(0.14,0.32,0.18),dark);_add_cylinder(gun,"DetailBarrel",Vector3(0,0.03,-0.56),0.035,0.80,dark)
  2:
   _add_box(gun,"DetailSlide",Vector3(0,0.03,-0.10),Vector3(0.17,0.12,0.40),steel);_add_box(gun,"DetailGrip",Vector3(0,-0.15,0.07),Vector3(0.14,0.28,0.17),polymer)
  3:
   _add_box(gun,"DetailReceiver",Vector3.ZERO,Vector3(0.20,0.16,0.60),steel);_add_box(gun,"DetailStock",Vector3(0,-0.02,0.46),Vector3(0.20,0.16,0.46),accent);_add_cylinder(gun,"DetailLongBarrel",Vector3(0,0.03,-0.80),0.032,1.20,dark);_add_cylinder(gun,"DetailScope",Vector3(0,0.15,-0.12),0.052,0.40,dark);_add_box(gun,"DetailBolt",Vector3(0.14,0.04,0.02),Vector3(0.17,0.05,0.06),steel)
  _:
   _add_box(gun,"DetailReceiver",Vector3.ZERO,Vector3(0.21,0.17,0.54),steel);_add_box(gun,"DetailStock",Vector3(0,-0.01,0.42),Vector3(0.20,0.16,0.40),polymer);_add_cylinder(gun,"DetailBarrel",Vector3(0,0.03,-0.62),0.034,0.90,dark);_add_box(gun,"DetailBlade",Vector3(0,-0.035,-1.02),Vector3(0.035,0.08,0.46),blade)

func _mat(color:Color,metallic:float,roughness:float)->StandardMaterial3D:
 var m:=StandardMaterial3D.new();m.albedo_color=color;m.metallic=metallic;m.roughness=roughness;return m
func _add_box(parent:Node3D,name:String,pos:Vector3,size:Vector3,mat:Material)->void:
 var n:=MeshInstance3D.new();n.name=name;var mesh:=BoxMesh.new();mesh.size=size;n.mesh=mesh;n.material_override=mat;n.position=pos;parent.add_child(n)
func _add_cylinder(parent:Node3D,name:String,pos:Vector3,radius:float,height:float,mat:Material)->void:
 var n:=MeshInstance3D.new();n.name=name;var mesh:=CylinderMesh.new();mesh.top_radius=radius;mesh.bottom_radius=radius;mesh.height=height;mesh.radial_segments=12;n.mesh=mesh;n.material_override=mat;n.position=pos;n.rotation_degrees.x=90.0;parent.add_child(n)
