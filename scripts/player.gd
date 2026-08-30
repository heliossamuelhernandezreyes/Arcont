extends CharacterBody3D

signal health_changed(current: float, maximum: float)
signal died
signal injury_changed(zone: String, severity: float)
signal suppression_changed(value: float)
signal camera_mode_changed(mode: String)
signal shoulder_changed(side: float)

@export var walk_speed := 5.5
@export var sprint_speed := 8.5
@export var acceleration := 18.0
@export var air_acceleration := 5.0
@export var jump_velocity := 5.2
@export var mouse_sensitivity := 0.0022
@export var mobile_look_sensitivity := 0.0040
@export var mobile_invert_y := false
@export var body_turn_speed := 11.0
@export var aim_turn_speed := 17.0
@export var max_health := 100.0

@onready var camera_rig: Node3D = $CameraRig
@onready var weapon: Node = $Weapon
@onready var body_visual: Node3D = $BodyVisual
@onready var mobility: Node = $TacticalMobility

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var camera_yaw := 0.0
var pitch := -0.12
var camera_mode := 0
var shoulder_side := 1.0
var mobile_move := Vector2.ZERO
var mobile_sprint := false
var mobile_jump_requested := false
var health := 100.0
var dead := false
var injuries := {"head":0.0,"torso":0.0,"left_arm":0.0,"right_arm":0.0,"left_leg":0.0,"right_leg":0.0}
var suppression := 0.0
var was_on_floor := true

func _ready() -> void:
 add_to_group("player")
 health = max_health
 camera_rig.rotation = Vector3(pitch, camera_yaw, 0.0)
 if weapon and weapon.has_signal("recoil_requested"):
  weapon.recoil_requested.connect(_on_weapon_recoil)
 if not DisplayServer.is_touchscreen_available():
  Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
 call_deferred("_emit_initial_state")

func _emit_initial_state() -> void:
 health_changed.emit(health, max_health)
 shoulder_changed.emit(shoulder_side)

func _unhandled_input(event: InputEvent) -> void:
 if dead:
  return
 if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
  _apply_look(event.relative * mouse_sensitivity)
 if event.is_action_pressed("reload"):
  request_reload()
 if event is InputEventKey and event.pressed and not event.echo:
  if event.keycode == KEY_V:
   cycle_camera_mode()
  elif event.keycode == KEY_Q:
   switch_shoulder()

func _physics_process(delta: float) -> void:
 if dead:
  return
 suppression = maxf(suppression - delta * 0.42, 0.0)

 var currently_on_floor := is_on_floor()
 if mobility and mobility.has_method("record_vertical_speed") and not currently_on_floor:
  mobility.record_vertical_speed(velocity.y)
 if currently_on_floor and not was_on_floor and mobility and mobility.has_method("handle_landing"):
  mobility.handle_landing()
 was_on_floor = currently_on_floor

 if mobility and mobility.has_method("blocks_normal_movement") and bool(mobility.blocks_normal_movement()):
  velocity = Vector3.ZERO
  return

 if not is_on_floor():
  velocity.y -= gravity * delta
 elif Input.is_action_just_pressed("jump") or mobile_jump_requested:
  var traversed := false
  if mobility and mobility.has_method("try_contextual_jump"):
   traversed = bool(mobility.try_contextual_jump())
  if not traversed and not (mobility and mobility.has_method("blocks_jump") and bool(mobility.blocks_jump())):
   velocity.y = jump_velocity * clampf(1.0 - _leg_injury_load() * 0.18, 0.62, 1.0)
 mobile_jump_requested = false

 var input_vec := _movement_input()
 var direction := _world_direction(input_vec)
 var sprinting := Input.is_action_pressed("sprint") or mobile_sprint
 var target_speed := (sprint_speed if sprinting else walk_speed) * clampf(1.0 - _leg_injury_load() * 0.22, 0.45, 1.0)
 if mobility and mobility.has_method("movement_speed_multiplier"):
  target_speed *= float(mobility.movement_speed_multiplier())
 var target := direction * target_speed
 var accel := acceleration if is_on_floor() else air_acceleration
 velocity.x = move_toward(velocity.x, target.x, accel * delta)
 velocity.z = move_toward(velocity.z, target.z, accel * delta)
 if mobility and mobility.has_method("apply_motion_override"):
  mobility.apply_motion_override()
 _update_body_orientation(direction, delta)
 move_and_slide()

func _update_body_orientation(direction: Vector3, delta: float) -> void:
 var aiming := weapon != null and bool(weapon.get("aiming"))
 var target_yaw := body_visual.rotation.y
 var turn_speed := body_turn_speed
 if aiming:
  target_yaw = camera_yaw
  turn_speed = aim_turn_speed
 elif direction.length_squared() > 0.02:
  target_yaw = atan2(-direction.x, -direction.z)
 body_visual.rotation.y = lerp_angle(body_visual.rotation.y, target_yaw, clampf(delta * turn_speed, 0.0, 1.0))

func _movement_input() -> Vector2:
 var keyboard := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
 if mobile_move.length_squared() > keyboard.length_squared():
  return mobile_move
 return keyboard

func _world_direction(input_vec: Vector2) -> Vector3:
 var yaw_basis := Basis(Vector3.UP, camera_yaw)
 return (yaw_basis.x * input_vec.x + yaw_basis.z * input_vec.y).normalized()

func _leg_injury_load() -> float:
 return float(injuries["left_leg"]) + float(injuries["right_leg"])

func _arm_injury_load() -> float:
 return (float(injuries["left_arm"]) + float(injuries["right_arm"])) * 0.5

func get_weapon_spread_multiplier() -> float:
 return 1.0 + _arm_injury_load() * 0.72 + suppression * 0.62

func get_recoil_multiplier() -> float:
 return 1.0 + _arm_injury_load() * 0.58 + suppression * 0.48

func get_reload_time_multiplier() -> float:
 return 1.0 + _arm_injury_load() * 0.55

func apply_suppression(intensity: float, _hold_time := 0.55) -> void:
 if intensity > 0.0:
  suppression = clampf(maxf(suppression, intensity), 0.0, 1.0)
  suppression_changed.emit(suppression)

func apply_damage(amount: float, source_direction := Vector3.ZERO, zone := "torso", penetration := 1.0) -> void:
 if dead or amount <= 0.0:
  return
 var normalized_zone: String = zone if injuries.has(zone) else "torso"
 var armor_effect := 0.28 if normalized_zone == "torso" else 0.10
 var final_damage := amount * maxf(0.2, penetration) * (1.0 - armor_effect)
 if normalized_zone == "head":
  final_damage *= 1.75
 health = maxf(health - final_damage, 0.0)
 injuries[normalized_zone] = clampf(float(injuries[normalized_zone]) + final_damage / 70.0, 0.0, 1.0)
 injury_changed.emit(normalized_zone, float(injuries[normalized_zone]))
 health_changed.emit(health, max_health)
 if source_direction.length_squared() > 0.0:
  velocity += source_direction.normalized() * 0.35
 if health <= 0.0:
  _die()

func heal(amount: float) -> void:
 if not dead and amount > 0.0:
  health = minf(health + amount, max_health)
  health_changed.emit(health, max_health)

func _die() -> void:
 if not dead:
  dead = true
  velocity = Vector3.ZERO
  died.emit()

func respawn(at_position: Vector3) -> void:
 global_position = at_position
 health = max_health
 dead = false
 suppression = 0.0
 for key in injuries.keys():
  injuries[key] = 0.0
 health_changed.emit(health, max_health)
 suppression_changed.emit(0.0)

func set_mobile_move(value: Vector2) -> void:
 mobile_move = value.limit_length(1.0)

func add_mobile_look(delta: Vector2) -> void:
 if dead:
  return
 var adjusted := delta
 if mobile_invert_y:
  adjusted.y = -adjusted.y
 _apply_look(adjusted * mobile_look_sensitivity)

func set_mobile_sprint(active: bool) -> void:
 mobile_sprint = active

func request_mobile_jump() -> void:
 mobile_jump_requested = true

func request_crouch() -> void:
 if not dead and mobility and mobility.has_method("request_crouch_or_slide"):
  mobility.request_crouch_or_slide()

func request_dodge() -> void:
 if not dead and mobility and mobility.has_method("request_dodge"):
  mobility.request_dodge(_world_direction(_movement_input()))

func request_reload() -> void:
 if not dead and weapon and weapon.has_method("request_reload"):
  weapon.request_reload()

func _try_fire() -> void:
 if not dead and weapon and weapon.has_method("try_fire"):
  weapon.try_fire()

func switch_shoulder() -> void:
 shoulder_side *= -1.0
 shoulder_changed.emit(shoulder_side)

func cycle_camera_mode() -> void:
 camera_mode = (camera_mode + 1) % 3
 camera_mode_changed.emit(camera_mode_name())

func camera_mode_name() -> String:
 var names: Array[String] = ["TACTICAL", "CLOSE", "WIDE"]
 return names[camera_mode]

func camera_distance_scale() -> float:
 var scales: Array[float] = [1.0, 0.72, 1.42]
 return scales[camera_mode]

func set_mobile_look_sensitivity(value: float) -> void:
 mobile_look_sensitivity = clampf(value, 0.0015, 0.0090)

func _on_weapon_recoil(recoil_pitch_value: float, recoil_yaw_value: float) -> void:
 camera_yaw += recoil_yaw_value
 pitch = clampf(pitch + recoil_pitch_value, deg_to_rad(-65.0), deg_to_rad(55.0))
 camera_rig.rotation = Vector3(pitch, camera_yaw, 0.0)

func _apply_look(amount: Vector2) -> void:
 camera_yaw -= amount.x
 pitch = clampf(pitch - amount.y, deg_to_rad(-65.0), deg_to_rad(55.0))
 camera_rig.rotation = Vector3(pitch, camera_yaw, 0.0)
