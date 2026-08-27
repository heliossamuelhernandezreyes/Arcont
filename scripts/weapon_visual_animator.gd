extends Node

var weapon:Node
var gun:Node3D
var pump:Node3D
var slide:Node3D
var magazine:Node3D
var base_gun_pos:=Vector3.ZERO
var base_gun_rot:=Vector3.ZERO
var base_pump_pos:=Vector3.ZERO
var base_slide_pos:=Vector3.ZERO
var base_mag_pos:=Vector3.ZERO

func _ready()->void:
	weapon=get_parent();call_deferred("_bind_visual")
	if weapon.has_signal("shot_fired"):weapon.shot_fired.connect(_on_shot)
	if weapon.has_signal("reload_state_changed"):weapon.reload_state_changed.connect(_on_reload_state)
	if weapon.has_signal("weapon_changed"):weapon.weapon_changed.connect(_on_weapon_changed)

func _bind_visual()->void:
	var camera:=weapon.get_parent();gun=camera.get_node_or_null("Gun") as Node3D
	if gun==null:return
	pump=gun.get_node_or_null("DetailPump") as Node3D;slide=gun.get_node_or_null("DetailSlide") as Node3D;magazine=gun.get_node_or_null("DetailMagazine") as Node3D
	base_gun_pos=gun.position;base_gun_rot=gun.rotation
	if pump:base_pump_pos=pump.position
	if slide:base_slide_pos=slide.position
	if magazine:base_mag_pos=magazine.position

func _on_weapon_changed(_name:String,_slot:int)->void:call_deferred("_bind_visual")

func _on_shot()->void:
	if gun==null:_bind_visual()
	if gun==null:return
	var tween:=create_tween()
	if pump:
		tween.tween_property(pump,"position:z",base_pump_pos.z+0.18,0.075);tween.tween_property(pump,"position:z",base_pump_pos.z,0.12)
	elif slide:
		tween.tween_property(slide,"position:z",base_slide_pos.z+0.10,0.035);tween.tween_property(slide,"position:z",base_slide_pos.z,0.065)
	else:tween.tween_interval(0.08)
	tween.parallel().tween_property(gun,"rotation:x",base_gun_rot.x+deg_to_rad(3.5),0.055);tween.tween_property(gun,"rotation:x",base_gun_rot.x,0.11)

func _on_reload_state(active:bool)->void:
	if gun==null:_bind_visual()
	if gun==null:return
	var tween:=create_tween()
	if active:
		tween.tween_property(gun,"rotation:z",base_gun_rot.z+deg_to_rad(18.0),0.16);tween.parallel().tween_property(gun,"position:y",base_gun_pos.y-0.08,0.16)
		if magazine:tween.parallel().tween_property(magazine,"position:y",base_mag_pos.y-0.20,0.20)
	else:
		tween.tween_property(gun,"rotation",base_gun_rot,0.16);tween.parallel().tween_property(gun,"position",base_gun_pos,0.16)
		if magazine:tween.parallel().tween_property(magazine,"position",base_mag_pos,0.16)
