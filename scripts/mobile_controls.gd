extends Control

@export var force_visible:=false
@export var joystick_radius:=92.0
@export var button_radius:=52.0
var player:Node=null
var companion:Node=null
var throwables:Node=null
var weapon:Node=null
var move_touch:=-1
var look_touch:=-1
var fire_touch:=-1
var ads_touch:=-1
var weapon_touch:=-1
var jump_touch:=-1
var crouch_touch:=-1
var dodge_touch:=-1
var sprint_touch:=-1
var reload_touch:=-1
var cover_touch:=-1
var command_touch:=-1
var throwable_touch:=-1
var throwable_cycle_touch:=-1
var move_origin:=Vector2.ZERO
var move_vector:=Vector2.ZERO
var touch_enabled:=false

func _ready()->void:
	touch_enabled=force_visible or DisplayServer.is_touchscreen_available()
	visible=touch_enabled
	set_process_input(touch_enabled)
	call_deferred("_bind_player")
	queue_redraw()

func _bind_player()->void:
	player=get_tree().get_first_node_in_group("player")
	companion=get_tree().get_first_node_in_group("friendly_companion")
	throwables=get_tree().get_first_node_in_group("throwable_controller")
	if player==null:
		var scene:=get_tree().current_scene
		if scene:player=scene.get_node_or_null("Player")
	if player:weapon=player.get_node_or_null("CameraRig/Camera3D/Weapon")

func _input(event:InputEvent)->void:
	if not touch_enabled:return
	if player==null or not is_instance_valid(player):
		_bind_player()
		if player==null:return
	if companion==null or not is_instance_valid(companion):companion=get_tree().get_first_node_in_group("friendly_companion")
	if throwables==null or not is_instance_valid(throwables):throwables=get_tree().get_first_node_in_group("throwable_controller")
	if weapon==null or not is_instance_valid(weapon):weapon=player.get_node_or_null("CameraRig/Camera3D/Weapon")
	if event is InputEventScreenTouch:_handle_touch(event)
	elif event is InputEventScreenDrag:_handle_drag(event)

func _handle_touch(event:InputEventScreenTouch)->void:
	if event.pressed:_assign_touch(event.index,event.position)
	else:_release_touch(event.index)
	queue_redraw()

func _assign_touch(index:int,position:Vector2)->void:
	if position.distance_to(_fire_center())<=button_radius*1.25 and fire_touch==-1:
		fire_touch=index
		if weapon and weapon.has_method("set_trigger"):weapon.set_trigger(true)
		elif player.has_method("set_mobile_fire"):player.set_mobile_fire(true)
		return
	if position.distance_to(_ads_center())<=button_radius*0.82 and ads_touch==-1:
		ads_touch=index
		if weapon and weapon.has_method("set_ads"):weapon.set_ads(true)
		return
	if position.distance_to(_weapon_center())<=button_radius*0.72 and weapon_touch==-1:
		weapon_touch=index
		if weapon and weapon.has_method("cycle_weapon"):weapon.cycle_weapon()
		return
	if position.distance_to(_jump_center())<=button_radius*1.2 and jump_touch==-1:
		jump_touch=index
		if player.has_method("request_mobile_jump"):player.request_mobile_jump()
		return
	if position.distance_to(_crouch_center())<=button_radius*0.76 and crouch_touch==-1:
		crouch_touch=index
		if player.has_method("request_crouch"):player.request_crouch()
		return
	if position.distance_to(_dodge_center())<=button_radius*0.78 and dodge_touch==-1:
		dodge_touch=index
		if player.has_method("request_dodge"):player.request_dodge()
		return
	if position.distance_to(_reload_center())<=button_radius and reload_touch==-1:
		reload_touch=index
		if player.has_method("request_reload"):player.request_reload()
		return
	if position.distance_to(_cover_center())<=button_radius and cover_touch==-1:
		cover_touch=index
		if player.has_method("_toggle_cover"):player.call("_toggle_cover")
		return
	if position.distance_to(_command_center())<=button_radius and command_touch==-1:
		command_touch=index
		if companion and companion.has_method("cycle_command"):companion.cycle_command()
		return
	if position.distance_to(_throw_center())<=button_radius and throwable_touch==-1:
		throwable_touch=index
		if throwables and throwables.has_method("mobile_throw"):throwables.mobile_throw()
		return
	if position.distance_to(_throw_cycle_center())<=button_radius and throwable_cycle_touch==-1:
		throwable_cycle_touch=index
		if throwables and throwables.has_method("mobile_cycle"):throwables.mobile_cycle()
		return
	if position.distance_to(_sprint_center())<=button_radius*1.15 and sprint_touch==-1:
		sprint_touch=index
		if player.has_method("set_mobile_sprint"):player.set_mobile_sprint(true)
		return
	var size:=get_viewport_rect().size
	if position.x<size.x*0.45 and move_touch==-1:
		move_touch=index
		move_origin=position
		move_vector=Vector2.ZERO
		if player.has_method("set_mobile_move"):player.set_mobile_move(move_vector)
	elif look_touch==-1:
		look_touch=index

func _handle_drag(event:InputEventScreenDrag)->void:
	if event.index==move_touch:
		move_vector=((event.position-move_origin)/joystick_radius).limit_length(1.0)
		if player.has_method("set_mobile_move"):player.set_mobile_move(move_vector)
		queue_redraw()
	elif event.index==look_touch and player.has_method("add_mobile_look"):
		player.add_mobile_look(event.relative)

func _release_touch(index:int)->void:
	if index==move_touch:
		move_touch=-1
		move_vector=Vector2.ZERO
		if player and player.has_method("set_mobile_move"):player.set_mobile_move(Vector2.ZERO)
	elif index==look_touch:look_touch=-1
	elif index==fire_touch:
		fire_touch=-1
		if weapon and weapon.has_method("set_trigger"):weapon.set_trigger(false)
		elif player and player.has_method("set_mobile_fire"):player.set_mobile_fire(false)
	elif index==ads_touch:
		ads_touch=-1
		if weapon and weapon.has_method("set_ads"):weapon.set_ads(false)
	elif index==weapon_touch:weapon_touch=-1
	elif index==jump_touch:jump_touch=-1
	elif index==crouch_touch:crouch_touch=-1
	elif index==dodge_touch:dodge_touch=-1
	elif index==sprint_touch:
		sprint_touch=-1
		if player and player.has_method("set_mobile_sprint"):player.set_mobile_sprint(false)
	elif index==reload_touch:reload_touch=-1
	elif index==cover_touch:cover_touch=-1
	elif index==command_touch:command_touch=-1
	elif index==throwable_touch:throwable_touch=-1
	elif index==throwable_cycle_touch:throwable_cycle_touch=-1

func _draw()->void:
	if not touch_enabled:return
	var size:=get_viewport_rect().size
	var default_stick:=Vector2(128.0,size.y-138.0)
	var stick_center:=move_origin if move_touch!=-1 else default_stick
	var knob:=stick_center+move_vector*joystick_radius*0.62
	draw_circle(stick_center,joystick_radius,Color(0.15,0.18,0.22,0.32))
	draw_circle(stick_center,joystick_radius*0.68,Color(0.55,0.62,0.72,0.10),false,4.0)
	draw_circle(knob,joystick_radius*0.34,Color(0.85,0.9,1.0,0.42))
	_draw_button(_fire_center(),button_radius,"FIRE")
	_draw_button(_ads_center(),button_radius*0.70,"ADS")
	_draw_button(_weapon_center(),button_radius*0.62,"WPN")
	_draw_button(_jump_center(),button_radius*0.86,"JUMP")
	_draw_button(_crouch_center(),button_radius*0.68,"CRCH")
	_draw_button(_dodge_center(),button_radius*0.70,"DODGE")
	_draw_button(_reload_center(),button_radius*0.72,"RLD")
	_draw_button(_cover_center(),button_radius*0.72,"COV")
	_draw_button(_command_center(),button_radius*0.72,"R3")
	_draw_button(_throw_center(),button_radius*0.72,"THR")
	_draw_button(_throw_cycle_center(),button_radius*0.64,"TYPE")
	_draw_button(_sprint_center(),button_radius*0.78,"RUN")

func _draw_button(center:Vector2,radius:float,label:String)->void:
	draw_circle(center,radius,Color(0.20,0.24,0.30,0.38))
	draw_arc(center,radius,0.0,TAU,36,Color(0.86,0.91,1.0,0.55),3.0)
	var font:=ThemeDB.fallback_font
	var font_size:=15
	var width:=font.get_string_size(label,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size).x
	draw_string(font,center+Vector2(-width*0.5,5.0),label,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size,Color(0.95,0.97,1.0,0.9))

func _fire_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(size.x-98.0,size.y-132.0)
func _ads_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(size.x-92.0,size.y-250.0)
func _weapon_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(size.x-170.0,size.y-270.0)
func _jump_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(size.x-210.0,size.y-90.0)
func _crouch_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(size.x-294.0,size.y-82.0)
func _dodge_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(size.x-302.0,size.y-235.0)
func _reload_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(size.x-218.0,size.y-192.0)
func _cover_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(size.x-382.0,size.y-150.0)
func _command_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(size.x-450.0,size.y-78.0)
func _throw_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(size.x-454.0,size.y-190.0)
func _throw_cycle_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(size.x-542.0,size.y-138.0)
func _sprint_center()->Vector2:var size:=get_viewport_rect().size;return Vector2(225.0,size.y-245.0)
