extends Control

@export var force_visible:=false
@export var joystick_radius:=86.0
@export var button_radius:=46.0
var player:Node=null
var companion:Node=null
var throwables:Node=null
var weapon:Node=null
var melee:Node=null
var move_touch:=-1
var look_touch:=-1
var fire_touch:=-1
var ads_touch:=-1
var jump_touch:=-1
var crouch_touch:=-1
var dodge_touch:=-1
var reload_touch:=-1
var weapon_touch:=-1
var throw_touch:=-1
var command_touch:=-1
var melee_touch:=-1
var move_origin:=Vector2.ZERO
var move_vector:=Vector2.ZERO
var touch_enabled:=false
var reload_feedback_text:=""
var reload_feedback_timer:=0.0

func _ready()->void:
 touch_enabled=force_visible or DisplayServer.is_touchscreen_available();visible=touch_enabled;mouse_filter=Control.MOUSE_FILTER_IGNORE;set_process_input(touch_enabled);set_process(touch_enabled);call_deferred("_bind_player");queue_redraw()
func _process(delta:float)->void:
 if reload_feedback_timer>0.0:reload_feedback_timer=maxf(0.0,reload_feedback_timer-delta);queue_redraw()
func _bind_player()->void:
 player=get_tree().get_first_node_in_group("player");companion=get_tree().get_first_node_in_group("friendly_companion");throwables=get_tree().get_first_node_in_group("throwable_controller")
 if player==null and get_tree().current_scene:player=get_tree().current_scene.get_node_or_null("Player")
 if player:weapon=player.get_node_or_null("Weapon");melee=player.get_node_or_null("MeleeCombat")
 _bind_weapon_feedback()
func _bind_weapon_feedback()->void:
 if weapon==null:return
 var cb:=Callable(self,"_on_active_reload_feedback")
 if weapon.has_signal("active_reload_feedback") and not weapon.is_connected("active_reload_feedback",cb):weapon.connect("active_reload_feedback",cb)
func _on_active_reload_feedback(result:String,_stage:int)->void:reload_feedback_text=result;reload_feedback_timer=0.52;queue_redraw()
func _input(event:InputEvent)->void:
 if not touch_enabled:return
 if player==null or not is_instance_valid(player):_bind_player();if player==null:return
 if event is InputEventScreenTouch:_handle_touch(event)
 elif event is InputEventScreenDrag:_handle_drag(event)
func _handle_touch(event:InputEventScreenTouch)->void:
 if event.pressed:_assign_touch(event.index,event.position)
 else:_release_touch(event.index)
 queue_redraw()
func _assign_touch(index:int,p:Vector2)->void:
 if p.distance_to(_fire_center())<=button_radius*1.25 and fire_touch<0:fire_touch=index;if weapon and weapon.has_method("set_trigger"):weapon.set_trigger(true);return
 if p.distance_to(_ads_center())<=button_radius and ads_touch<0:ads_touch=index;if weapon and weapon.has_method("set_ads"):weapon.set_ads(true);return
 if p.distance_to(_jump_center())<=button_radius and jump_touch<0:jump_touch=index;if player.has_method("request_mobile_jump"):player.request_mobile_jump();return
 if p.distance_to(_crouch_center())<=button_radius and crouch_touch<0:crouch_touch=index;if player.has_method("request_crouch"):player.request_crouch();return
 if p.distance_to(_dodge_center())<=button_radius and dodge_touch<0:dodge_touch=index;if player.has_method("request_dodge"):player.request_dodge();return
 if p.distance_to(_melee_center())<=button_radius and melee_touch<0:melee_touch=index;if melee and melee.has_method("begin_guard"):melee.begin_guard(p);return
 if p.distance_to(_reload_center())<=button_radius*0.72 and reload_touch<0:reload_touch=index;if player.has_method("request_reload"):player.request_reload();return
 if p.distance_to(_weapon_center())<=button_radius*0.72 and weapon_touch<0:weapon_touch=index;if weapon and weapon.has_method("cycle_weapon"):weapon.cycle_weapon();return
 if p.distance_to(_throw_center())<=button_radius*0.72 and throw_touch<0:throw_touch=index;if throwables and throwables.has_method("mobile_throw"):throwables.mobile_throw();return
 if p.distance_to(_command_center())<=button_radius*0.72 and command_touch<0:command_touch=index;if companion and companion.has_method("cycle_command"):companion.cycle_command();return
 var size:=get_viewport_rect().size
 if p.x<size.x*0.36 and p.y>size.y*0.40 and move_touch<0:move_touch=index;move_origin=p;move_vector=Vector2.ZERO;if player.has_method("set_mobile_move"):player.set_mobile_move(move_vector);return
 if p.x>=size.x*0.36 and look_touch<0:look_touch=index
func _handle_drag(event:InputEventScreenDrag)->void:
 if event.index==move_touch:
  move_vector=((event.position-move_origin)/joystick_radius).limit_length(1.0);if player.has_method("set_mobile_move"):player.set_mobile_move(move_vector);queue_redraw()
 elif event.index==melee_touch:
  if melee and melee.has_method("update_guard_drag"):melee.update_guard_drag(event.position)
 elif event.index==look_touch and player.has_method("add_mobile_look"):player.add_mobile_look(event.relative)
func _release_touch(index:int)->void:
 if index==move_touch:move_touch=-1;move_vector=Vector2.ZERO;if player and player.has_method("set_mobile_move"):player.set_mobile_move(Vector2.ZERO)
 elif index==look_touch:look_touch=-1
 elif index==fire_touch:fire_touch=-1;if weapon and weapon.has_method("set_trigger"):weapon.set_trigger(false)
 elif index==ads_touch:ads_touch=-1;if weapon and weapon.has_method("set_ads"):weapon.set_ads(false)
 elif index==jump_touch:jump_touch=-1
 elif index==crouch_touch:crouch_touch=-1
 elif index==dodge_touch:dodge_touch=-1
 elif index==reload_touch:reload_touch=-1
 elif index==weapon_touch:weapon_touch=-1
 elif index==throw_touch:throw_touch=-1
 elif index==command_touch:command_touch=-1
 elif index==melee_touch:melee_touch=-1;if melee and melee.has_method("release_attack"):melee.release_attack()
func _draw()->void:
 if not touch_enabled:return
 var size:=get_viewport_rect().size;var stick:=move_origin if move_touch>=0 else Vector2(120,size.y-120);var knob:=stick+move_vector*joystick_radius*0.62
 draw_circle(stick,joystick_radius,Color(0.10,0.12,0.16,0.20));draw_arc(stick,joystick_radius,0,TAU,36,Color(0.8,0.85,0.95,0.30),2.0);draw_circle(knob,joystick_radius*0.28,Color(0.85,0.9,1,0.32))
 _draw_button(_fire_center(),button_radius*1.05,"FIRE");_draw_button(_ads_center(),button_radius*0.82,"ADS");_draw_button(_jump_center(),button_radius*0.78,"JUMP");_draw_button(_crouch_center(),button_radius*0.70,"CRCH");_draw_button(_dodge_center(),button_radius*0.70,"DODGE");_draw_button(_melee_center(),button_radius*0.78,_melee_label())
 _draw_button(_reload_center(),button_radius*0.58,"RLD");_draw_button(_weapon_center(),button_radius*0.58,"WPN");_draw_button(_throw_center(),button_radius*0.58,"THR");_draw_button(_command_center(),button_radius*0.58,"R3");_draw_active_reload()
func _draw_button(c:Vector2,r:float,label:String)->void:
 draw_circle(c,r,Color(0.12,0.15,0.20,0.22));draw_arc(c,r,0,TAU,30,Color(0.86,0.91,1,0.42),2.0);var f:=ThemeDB.fallback_font;var fs:=12;var w:=f.get_string_size(label,HORIZONTAL_ALIGNMENT_LEFT,-1,fs).x;draw_string(f,c+Vector2(-w*0.5,4),label,HORIZONTAL_ALIGNMENT_LEFT,-1,fs,Color(0.96,0.98,1,0.82))
func _draw_active_reload()->void:
 if weapon==null or not weapon.has_method("get_active_reload_state"):return
 var s:Dictionary=weapon.get_active_reload_state();var c:=_reload_center();var r:=button_radius*0.72
 if bool(s.get("active",false)):
  var p:=clampf(float(s.get("progress",0)),0,1);draw_arc(c,r,-PI*0.5,-PI*0.5+TAU*p,32,Color(0.72,0.88,1,0.9),4)
 if reload_feedback_timer>0 and not reload_feedback_text.is_empty():draw_string(ThemeDB.fallback_font,c+Vector2(-24,-34),reload_feedback_text,HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color.WHITE)
func _melee_label()->String:
 if melee and melee.has_method("is_guarding") and melee.is_guarding():return String(melee.current_guard()).to_upper()
 return "MELEE"
func _fire_center()->Vector2:var s:=get_viewport_rect().size;return Vector2(s.x-88,s.y-110)
func _ads_center()->Vector2:var s:=get_viewport_rect().size;return Vector2(s.x-82,s.y-215)
func _jump_center()->Vector2:var s:=get_viewport_rect().size;return Vector2(s.x-185,s.y-78)
func _crouch_center()->Vector2:var s:=get_viewport_rect().size;return Vector2(s.x-270,s.y-76)
func _dodge_center()->Vector2:var s:=get_viewport_rect().size;return Vector2(s.x-190,s.y-170)
func _melee_center()->Vector2:var s:=get_viewport_rect().size;return Vector2(s.x-82,s.y-310)
func _reload_center()->Vector2:var s:=get_viewport_rect().size;return Vector2(s.x-345,70)
func _weapon_center()->Vector2:var s:=get_viewport_rect().size;return Vector2(s.x-282,70)
func _throw_center()->Vector2:var s:=get_viewport_rect().size;return Vector2(s.x-219,70)
func _command_center()->Vector2:var s:=get_viewport_rect().size;return Vector2(s.x-156,70)
func _throw_cycle_center()->Vector2:return _throw_center()
