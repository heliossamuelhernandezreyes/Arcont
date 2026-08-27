extends Node

var weapon: Node
var player: Node
var gun: Node3D
var pump: Node3D
var slide: Node3D
var magazine: Node3D
var bolt: Node3D
var round_visual: MeshInstance3D
var melee: Node
var base_gun_pos := Vector3.ZERO
var base_gun_rot := Vector3.ZERO
var base_pump_pos := Vector3.ZERO
var base_slide_pos := Vector3.ZERO
var base_mag_pos := Vector3.ZERO
var base_bolt_pos := Vector3.ZERO
var base_bolt_rot := Vector3.ZERO
var detail_bases: Dictionary = {}
var recoil_time := 0.0
var recoil_duration := 0.20
var bolt_cycle_time := 0.0
var bolt_cycle_duration := 1.35
var reload_feedback_stage := -1
var reload_feedback_strength := 0.0
var guard_line := "mid"
var guard_active := false
var melee_anim_time := 0.0
var melee_anim_duration := 0.0
var melee_anim_kind := ""
var melee_anim_line := "mid"

func _ready() -> void:
	weapon = get_parent()
	player = weapon.get_parent()
	call_deferred("_bind_visual")
	call_deferred("_bind_melee")
	if weapon.has_signal("shot_fired"):
		weapon.shot_fired.connect(_on_shot)
	if weapon.has_signal("reload_state_changed"):
		weapon.reload_state_changed.connect(_on_reload_state)
	if weapon.has_signal("weapon_changed"):
		weapon.weapon_changed.connect(_on_weapon_changed)
	if weapon.has_signal("active_reload_feedback"):
		weapon.active_reload_feedback.connect(_on_active_reload_feedback)

func _process(delta: float) -> void:
	recoil_time = maxf(recoil_time - delta, 0.0)
	bolt_cycle_time = maxf(bolt_cycle_time - delta, 0.0)
	reload_feedback_strength = maxf(reload_feedback_strength - delta * 4.5, 0.0)
	melee_anim_time = maxf(melee_anim_time - delta, 0.0)
	if gun == null:
		return
	if int(weapon.get("slot")) == 3:
		_animate_m90()
	else:
		_restore_detail_bases()
	_animate_melee_pose()

func _bind_visual() -> void:
	if player == null:
		return
	gun = player.get_node_or_null("BodyVisual/WeaponMount/Gun") as Node3D
	if gun == null:
		return
	pump = gun.get_node_or_null("DetailPump") as Node3D
	slide = gun.get_node_or_null("DetailSlide") as Node3D
	magazine = gun.get_node_or_null("DetailMagazine") as Node3D
	bolt = gun.get_node_or_null("DetailBolt") as Node3D
	base_gun_pos = gun.position
	base_gun_rot = gun.rotation
	if pump:
		base_pump_pos = pump.position
	if slide:
		base_slide_pos = slide.position
	if magazine:
		base_mag_pos = magazine.position
	if bolt:
		base_bolt_pos = bolt.position
		base_bolt_rot = bolt.rotation
	_capture_detail_bases()
	if int(weapon.get("slot")) == 3:
		_ensure_round_visual()

func _bind_melee() -> void:
	if player == null:
		return
	melee = player.get_node_or_null("MeleeCombat")
	if melee == null:
		return
	if melee.has_signal("guard_changed") and not melee.guard_changed.is_connected(_on_guard_changed):
		melee.guard_changed.connect(_on_guard_changed)
	if melee.has_signal("attack_visual") and not melee.attack_visual.is_connected(_on_melee_attack):
		melee.attack_visual.connect(_on_melee_attack)
	if melee.has_signal("parry_visual") and not melee.parry_visual.is_connected(_on_parry_visual):
		melee.parry_visual.connect(_on_parry_visual)
	if melee.has_signal("execute_visual") and not melee.execute_visual.is_connected(_on_execute_visual):
		melee.execute_visual.connect(_on_execute_visual)

func _capture_detail_bases() -> void:
	detail_bases.clear()
	if gun == null:
		return
	for child in gun.get_children():
		if child is Node3D:
			var part := child as Node3D
			detail_bases[part.get_instance_id()] = {"node": part, "position": part.position, "rotation": part.rotation}

func _on_weapon_changed(_name: String, _slot: int) -> void:
	recoil_time = 0.0
	bolt_cycle_time = 0.0
	reload_feedback_stage = -1
	reload_feedback_strength = 0.0
	melee_anim_time = 0.0
	guard_active = false
	call_deferred("_bind_visual")

func _on_shot() -> void:
	if gun == null:
		_bind_visual()
	if gun == null:
		return
	recoil_time = recoil_duration
	if int(weapon.get("slot")) == 3:
		bolt_cycle_time = bolt_cycle_duration
		return
	var tween := create_tween()
	if pump:
		tween.tween_property(pump, "position:z", base_pump_pos.z + 0.18, 0.075)
		tween.tween_property(pump, "position:z", base_pump_pos.z, 0.12)
	elif slide:
		tween.tween_property(slide, "position:z", base_slide_pos.z + 0.10, 0.035)
		tween.tween_property(slide, "position:z", base_slide_pos.z, 0.065)
	else:
		tween.tween_interval(0.08)

func _on_reload_state(active: bool) -> void:
	if gun == null:
		_bind_visual()
	if gun == null:
		return
	reload_feedback_stage = -1
	reload_feedback_strength = 0.0
	if int(weapon.get("slot")) == 3:
		if round_visual:
			round_visual.visible = active
		if not active:
			_restore_detail_bases()
		return
	var tween := create_tween()
	if active:
		tween.tween_property(gun, "rotation:z", base_gun_rot.z + deg_to_rad(18.0), 0.16)
		tween.parallel().tween_property(gun, "position:y", base_gun_pos.y - 0.08, 0.16)
		if magazine:
			tween.parallel().tween_property(magazine, "position:y", base_mag_pos.y - 0.20, 0.20)
	else:
		tween.tween_property(gun, "rotation", base_gun_rot, 0.16)
		tween.parallel().tween_property(gun, "position", base_gun_pos, 0.16)
		if magazine:
			tween.parallel().tween_property(magazine, "position", base_mag_pos, 0.16)

func _on_active_reload_feedback(result: String, stage: int) -> void:
	if int(weapon.get("slot")) != 3:
		return
	reload_feedback_stage = stage
	if result == "PERFECT":
		reload_feedback_strength = 1.0
	elif result == "GOOD":
		reload_feedback_strength = 0.62
	else:
		reload_feedback_strength = 0.28

func _on_guard_changed(line: String) -> void:
	guard_line = line
	guard_active = true

func _on_melee_attack(line: String, _profile: String) -> void:
	guard_active = false
	melee_anim_line = line
	melee_anim_kind = _melee_kind_for_weapon()
	melee_anim_duration = 0.34 if melee_anim_kind == "bayonet" else 0.40
	melee_anim_time = melee_anim_duration

func _on_parry_visual(line: String, result: String) -> void:
	guard_active = true
	guard_line = line
	melee_anim_line = line
	if result == "mid_parry":
		melee_anim_kind = "mid_parry"
	elif result == "parry":
		melee_anim_kind = "parry"
	else:
		melee_anim_kind = "block"
	melee_anim_duration = 0.22
	melee_anim_time = melee_anim_duration

func _on_execute_visual(_profile: String) -> void:
	guard_active = false
	melee_anim_line = "high"
	melee_anim_kind = "execute"
	melee_anim_duration = 0.42
	melee_anim_time = melee_anim_duration

func _melee_kind_for_weapon() -> String:
	var current_slot := int(weapon.get("slot"))
	match current_slot:
		4:
			return "bayonet"
		3:
			return "hammer"
		0:
			return "shotgun_bash"
		1:
			return "rifle_bash"
		_:
			return "pistol_strike"

func _animate_melee_pose() -> void:
	if gun == null:
		return
	var pos := base_gun_pos
	var rot := base_gun_rot
	if guard_active:
		match guard_line:
			"high":
				pos += Vector3(-0.03, 0.12, -0.08)
				rot += Vector3(deg_to_rad(-18.0), deg_to_rad(8.0), deg_to_rad(-10.0))
			"low":
				pos += Vector3(0.02, -0.13, -0.05)
				rot += Vector3(deg_to_rad(18.0), deg_to_rad(-6.0), deg_to_rad(8.0))
			_:
				pos += Vector3(-0.02, 0.02, -0.10)
				rot += Vector3(deg_to_rad(-2.0), deg_to_rad(12.0), deg_to_rad(-6.0))
	if melee_anim_time > 0.0:
		var t := 1.0 - melee_anim_time / maxf(melee_anim_duration, 0.01)
		var pulse := sin(clampf(t, 0.0, 1.0) * PI)
		match melee_anim_kind:
			"bayonet":
				pos += Vector3(0.0, 0.02, -0.62 * pulse)
			"execute":
				pos += Vector3(0.0, 0.08, -0.70 * pulse)
				rot.x += deg_to_rad(-24.0 * pulse)
			"parry":
				rot.y += deg_to_rad(-34.0 * pulse)
			"mid_parry":
				pos.z += 0.22 * pulse
			_:
				pos.z -= 0.24 * pulse
				rot.y += deg_to_rad(18.0 * pulse)
	if recoil_time > 0.0:
		var recoil_alpha := sin((1.0 - recoil_time / maxf(recoil_duration, 0.01)) * PI)
		pos.z += 0.08 * recoil_alpha
		rot.x += deg_to_rad(3.5 * recoil_alpha)
	gun.position = gun.position.lerp(pos, 0.42)
	gun.rotation = gun.rotation.lerp(rot, 0.42)

func _animate_m90() -> void:
	_restore_detail_bases()
	if bolt_cycle_time > 0.0 and bolt:
		var cycle := 1.0 - bolt_cycle_time / maxf(bolt_cycle_duration, 0.01)
		var lift := smoothstep(0.08, 0.23, cycle) * (1.0 - smoothstep(0.72, 0.88, cycle))
		var pull := smoothstep(0.22, 0.42, cycle) * (1.0 - smoothstep(0.62, 0.82, cycle))
		bolt.rotation = base_bolt_rot + Vector3(0.0, 0.0, deg_to_rad(-58.0 * lift))
		bolt.position = base_bolt_pos + Vector3(0.0, 0.0, 0.22 * pull)
	if bool(weapon.get("reloading")):
		_animate_m90_reload()

func _animate_m90_reload() -> void:
	var state: Dictionary = weapon.get_active_reload_state() if weapon.has_method("get_active_reload_state") else {}
	var progress := float(state.get("progress", 0.0))
	var phase1 := smoothstep(0.08, 0.30, progress) * (1.0 - smoothstep(0.47, 0.58, progress))
	var phase2 := smoothstep(0.55, 0.72, progress)
	if bolt:
		var open_amount := maxf(phase1, 1.0 - phase2)
		bolt.rotation = base_bolt_rot + Vector3(0.0, 0.0, deg_to_rad(-62.0 * open_amount))
		bolt.position = base_bolt_pos + Vector3(0.0, 0.0, 0.24 * open_amount)
	if round_visual:
		round_visual.visible = true
		var insert := smoothstep(0.50, 0.74, progress)
		round_visual.position = Vector3(0.0, 0.12 - 0.10 * insert, 0.02 - 0.16 * insert)
		round_visual.scale = Vector3.ONE * (1.0 - 0.72 * insert)

func _apply_detail_offset(position_offset: Vector3, rotation_offset: Vector3, exclude_names: Array[String] = []) -> void:
	for data in detail_bases.values():
		var part := data.get("node") as Node3D
		if part == null or not is_instance_valid(part) or part.name in exclude_names:
			continue
		part.position = (data.get("position") as Vector3) + position_offset
		part.rotation = (data.get("rotation") as Vector3) + rotation_offset

func _restore_detail_bases() -> void:
	for data in detail_bases.values():
		var part := data.get("node") as Node3D
		if part == null or not is_instance_valid(part):
			continue
		part.position = data.get("position") as Vector3
		part.rotation = data.get("rotation") as Vector3

func _ensure_round_visual() -> void:
	if gun == null:
		return
	round_visual = gun.get_node_or_null("DetailRound") as MeshInstance3D
	if round_visual:
		return
	round_visual = MeshInstance3D.new()
	round_visual.name = "DetailRound"
	var mesh := CylinderMesh.new()
	mesh.top_radius = 0.022
	mesh.bottom_radius = 0.025
	mesh.height = 0.12
	mesh.radial_segments = 10
	round_visual.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.62, 0.38, 0.12)
	material.metallic = 0.72
	material.roughness = 0.28
	round_visual.material_override = material
	round_visual.position = Vector3(0.0, 0.12, 0.02)
	round_visual.rotation_degrees = Vector3(88.0, 0.0, 0.0)
	round_visual.visible = false
	gun.add_child(round_visual)
	_capture_detail_bases()
