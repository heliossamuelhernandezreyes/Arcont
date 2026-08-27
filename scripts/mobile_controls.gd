extends Control

@export var force_visible := false
@export var joystick_radius := 92.0
@export var button_radius := 52.0

var player: Node = null
var move_touch := -1
var look_touch := -1
var fire_touch := -1
var jump_touch := -1
var sprint_touch := -1
var reload_touch := -1
var move_origin := Vector2.ZERO
var move_vector := Vector2.ZERO
var touch_enabled := false

func _ready() -> void:
	touch_enabled = force_visible or DisplayServer.is_touchscreen_available()
	visible = touch_enabled
	set_process_input(touch_enabled)
	call_deferred("_bind_player")
	queue_redraw()

func _bind_player() -> void:
	player = get_tree().get_first_node_in_group("player")
	if player == null:
		var scene := get_tree().current_scene
		if scene:
			player = scene.get_node_or_null("Player")

func _input(event: InputEvent) -> void:
	if not touch_enabled:
		return
	if player == null or not is_instance_valid(player):
		_bind_player()
		if player == null:
			return
	if event is InputEventScreenTouch:
		_handle_touch(event)
	elif event is InputEventScreenDrag:
		_handle_drag(event)

func _handle_touch(event: InputEventScreenTouch) -> void:
	if event.pressed:
		_assign_touch(event.index, event.position)
	else:
		_release_touch(event.index)
	queue_redraw()

func _assign_touch(index: int, position: Vector2) -> void:
	if position.distance_to(_fire_center()) <= button_radius * 1.25 and fire_touch == -1:
		fire_touch = index
		if player.has_method("set_mobile_fire"):
			player.set_mobile_fire(true)
		return
	if position.distance_to(_jump_center()) <= button_radius * 1.2 and jump_touch == -1:
		jump_touch = index
		if player.has_method("request_mobile_jump"):
			player.request_mobile_jump()
		return
	if position.distance_to(_reload_center()) <= button_radius and reload_touch == -1:
		reload_touch = index
		if player.has_method("request_reload"):
			player.request_reload()
		return
	if position.distance_to(_sprint_center()) <= button_radius * 1.15 and sprint_touch == -1:
		sprint_touch = index
		if player.has_method("set_mobile_sprint"):
			player.set_mobile_sprint(true)
		return

	var size := get_viewport_rect().size
	if position.x < size.x * 0.45 and move_touch == -1:
		move_touch = index
		move_origin = position
		move_vector = Vector2.ZERO
		if player.has_method("set_mobile_move"):
			player.set_mobile_move(move_vector)
	elif look_touch == -1:
		look_touch = index

func _handle_drag(event: InputEventScreenDrag) -> void:
	if event.index == move_touch:
		move_vector = ((event.position - move_origin) / joystick_radius).limit_length(1.0)
		if player.has_method("set_mobile_move"):
			player.set_mobile_move(move_vector)
		queue_redraw()
	elif event.index == look_touch and player.has_method("add_mobile_look"):
		player.add_mobile_look(event.relative)

func _release_touch(index: int) -> void:
	if index == move_touch:
		move_touch = -1
		move_vector = Vector2.ZERO
		if player and player.has_method("set_mobile_move"):
			player.set_mobile_move(Vector2.ZERO)
	elif index == look_touch:
		look_touch = -1
	elif index == fire_touch:
		fire_touch = -1
		if player and player.has_method("set_mobile_fire"):
			player.set_mobile_fire(false)
	elif index == jump_touch:
		jump_touch = -1
	elif index == sprint_touch:
		sprint_touch = -1
		if player and player.has_method("set_mobile_sprint"):
			player.set_mobile_sprint(false)
	elif index == reload_touch:
		reload_touch = -1

func _draw() -> void:
	if not touch_enabled:
		return
	var size := get_viewport_rect().size
	var default_stick := Vector2(128.0, size.y - 138.0)
	var stick_center := move_origin if move_touch != -1 else default_stick
	var knob := stick_center + move_vector * joystick_radius * 0.62
	draw_circle(stick_center, joystick_radius, Color(0.15, 0.18, 0.22, 0.32))
	draw_circle(stick_center, joystick_radius * 0.68, Color(0.55, 0.62, 0.72, 0.10), false, 4.0)
	draw_circle(knob, joystick_radius * 0.34, Color(0.85, 0.9, 1.0, 0.42))
	_draw_button(_fire_center(), button_radius, "FIRE")
	_draw_button(_jump_center(), button_radius * 0.86, "JUMP")
	_draw_button(_reload_center(), button_radius * 0.72, "RLD")
	_draw_button(_sprint_center(), button_radius * 0.78, "RUN")

func _draw_button(center: Vector2, radius: float, label: String) -> void:
	draw_circle(center, radius, Color(0.20, 0.24, 0.30, 0.38))
	draw_arc(center, radius, 0.0, TAU, 36, Color(0.86, 0.91, 1.0, 0.55), 3.0)
	var font := ThemeDB.fallback_font
	var font_size := 15
	var width := font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	draw_string(font, center + Vector2(-width * 0.5, 5.0), label, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, Color(0.95, 0.97, 1.0, 0.9))

func _fire_center() -> Vector2:
	var size := get_viewport_rect().size
	return Vector2(size.x - 98.0, size.y - 132.0)

func _jump_center() -> Vector2:
	var size := get_viewport_rect().size
	return Vector2(size.x - 210.0, size.y - 90.0)

func _reload_center() -> Vector2:
	var size := get_viewport_rect().size
	return Vector2(size.x - 218.0, size.y - 192.0)

func _sprint_center() -> Vector2:
	var size := get_viewport_rect().size
	return Vector2(225.0, size.y - 245.0)
