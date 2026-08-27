extends Node

signal mission_completed

const STAGE_GENERATOR := 0
const STAGE_DEFEND := 1
const STAGE_SUPPLIES := 2
const STAGE_EVAC := 3
const STAGE_COMPLETE := 4

@export var generator_position := Vector3(-10.0, 0.0, 14.5)
@export var supply_position := Vector3(13.0, 0.0, -13.0)
@export var evac_position := Vector3(-0.5, 0.0, -29.0)
@export var interact_radius := 2.4
@export var generator_activate_time := 2.2
@export var defend_duration := 28.0
@export var defend_radius := 7.0
@export var reinforcement_interval := 8.0

var stage := STAGE_GENERATOR
var generator_progress := 0.0
var defend_remaining := 28.0
var reinforcement_timer := 0.0
var blackout_triggered := false
var radio_warning_triggered := false
var brute_triggered := false
var xeno_pulse_triggered := false
var player: Node3D
var weapon: Node
var companion: Node
var objective_label: Label
var info_label: Label
var generator_root: Node3D
var supply_root: Node3D
var evac_root: Node3D
var generator_light: OmniLight3D
var evac_light: OmniLight3D
var moon_light: DirectionalLight3D
var emergency_light: OmniLight3D

func _ready() -> void:
	player = get_parent().get_node("Player") as Node3D
	weapon = get_parent().get_node("Player/Head/Camera3D/Weapon")
	companion = get_parent().get_node_or_null("CompanionRobot")
	objective_label = get_parent().get_node("HUD/Objective") as Label
	info_label = get_parent().get_node("HUD/Info") as Label
	moon_light = get_parent().get_node_or_null("MoonLight") as DirectionalLight3D
	emergency_light = get_parent().get_node_or_null("EmergencyLight") as OmniLight3D
	defend_remaining = defend_duration
	_build_objective_props()
	_set_stage(STAGE_GENERATOR)

func _process(delta: float) -> void:
	if player == null or not is_instance_valid(player):
		return
	match stage:
		STAGE_GENERATOR:
			_update_generator(delta)
		STAGE_DEFEND:
			_update_defense(delta)
		STAGE_SUPPLIES:
			_update_supplies()
		STAGE_EVAC:
			_update_evac()

func _update_generator(delta: float) -> void:
	var distance := player.global_position.distance_to(generator_position)
	if distance <= interact_radius:
		generator_progress = minf(generator_progress + delta, generator_activate_time)
		var pct := roundi((generator_progress / generator_activate_time) * 100.0)
		objective_label.text = "OBJETIVO // REACTIVANDO GENERADOR %d%%" % pct
		if generator_progress >= generator_activate_time:
			_generator_activated()
	else:
		generator_progress = maxf(generator_progress - delta * 0.35, 0.0)
		objective_label.text = "OBJETIVO // REACTIVA EL GENERADOR  •  %.0f m" % distance

func _generator_activated() -> void:
	generator_light.light_color = Color(0.18, 0.85, 0.38)
	generator_light.light_energy = 3.0
	if companion and companion.has_method("activate_unit"):
		companion.activate_unit()
	info_label.text = "RADIO // ENERGIA RESTAURADA\nR-3 CUSTODIO REACTIVADO · FIRMA HOSTIL EN AUMENTO"
	_request_reinforcements(10)
	_set_stage(STAGE_DEFEND)

func _update_defense(delta: float) -> void:
	var distance := player.global_position.distance_to(generator_position)
	if distance <= defend_radius:
		defend_remaining = maxf(defend_remaining - delta, 0.0)
		reinforcement_timer += delta
		if reinforcement_timer >= reinforcement_interval:
			reinforcement_timer = 0.0
			_request_reinforcements(4)
		_trigger_defense_events()
		objective_label.text = "OBJETIVO // DEFIENDE EL GENERADOR  •  %02d s" % ceili(defend_remaining)
		if defend_remaining <= 0.0:
			_defense_complete()
	else:
		objective_label.text = "OBJETIVO // REGRESA AL GENERADOR  •  %.0f m" % distance

func _trigger_defense_events() -> void:
	var elapsed := defend_duration - defend_remaining
	if elapsed >= 4.0 and not blackout_triggered:
		blackout_triggered = true
		_trigger_blackout()
	if elapsed >= 9.0 and not radio_warning_triggered:
		radio_warning_triggered = true
		info_label.text = "RADIO // CONTROL A OPERADOR\nMOVIMIENTO MASIVO EN EL EJE NORTE · NO ABANDONE EL GENERADOR"
	if elapsed >= 15.0 and not brute_triggered:
		brute_triggered = true
		_spawn_brute_event()
	if elapsed >= 21.0 and not xeno_pulse_triggered:
		xeno_pulse_triggered = true
		_trigger_xeno_pulse()

func _trigger_blackout() -> void:
	info_label.text = "RADIO // FALLO DE RED\nAPAGON LOCAL · INTERFERENCIA XENOLOGICA"
	if moon_light:
		moon_light.light_energy = 0.18
	if emergency_light:
		emergency_light.light_energy = 0.15
	await get_tree().create_timer(3.2).timeout
	if moon_light:
		moon_light.light_energy = 1.05
	if emergency_light:
		emergency_light.light_energy = 1.8
	if stage == STAGE_DEFEND:
		info_label.text = "R-3 // SENSORES OPTICOS RECUPERADOS\nHOSTILES A CORTA DISTANCIA"

func _spawn_brute_event() -> void:
	info_label.text = "R-3 // ALERTA DE MASA\nCONTACTO PESADO APROXIMANDOSE · CLASIFICACION: BRUTE"
	var root := get_parent()
	if root and root.has_method("spawn_brute"):
		root.spawn_brute()

func _trigger_xeno_pulse() -> void:
	info_label.text = "RADIO // PULSO XENOLOGICO DETECTADO\nLAS SEÑALES INFECTADAS ESTAN CONVERGIENDO"
	_request_reinforcements(7)
	if generator_light:
		generator_light.light_color = Color(0.64, 0.12, 1.0)
		generator_light.light_energy = 4.0
	await get_tree().create_timer(1.4).timeout
	if generator_light and stage == STAGE_DEFEND:
		generator_light.light_color = Color(0.18, 0.85, 0.38)
		generator_light.light_energy = 3.0

func _defense_complete() -> void:
	generator_light.light_energy = 1.7
	if supply_root:
		supply_root.visible = true
	info_label.text = "RADIO // SEÑAL ESTABILIZADA\nSUMINISTROS DE EMERGENCIA LOCALIZADOS · R-3 MANTENDRA COBERTURA"
	_set_stage(STAGE_SUPPLIES)

func _update_supplies() -> void:
	var distance := player.global_position.distance_to(supply_position)
	objective_label.text = "OBJETIVO // RECUPERA SUMINISTROS  •  %.0f m" % distance
	if distance <= interact_radius:
		_collect_supplies()

func _collect_supplies() -> void:
	if weapon and weapon.has_method("add_ammo"):
		weapon.add_ammo(32)
	if player and player.has_method("heal"):
		player.heal(35.0)
	if companion and companion.has_method("heal"):
		companion.heal(70.0)
	if supply_root:
		supply_root.visible = false
	if evac_root:
		evac_root.visible = true
	if evac_light:
		evac_light.visible = true
	_request_reinforcements(8)
	info_label.text = "RADIO // PAQUETE RECUPERADO\nVENTANA DE EXTRACCION ABIERTA · MUEVASE"
	_set_stage(STAGE_EVAC)

func _update_evac() -> void:
	var distance := player.global_position.distance_to(evac_position)
	objective_label.text = "OBJETIVO // ALCANZA LA EXTRACCION  •  %.0f m" % distance
	if distance <= interact_radius + 0.8:
		_complete_mission()

func _complete_mission() -> void:
	stage = STAGE_COMPLETE
	objective_label.text = "MISION COMPLETADA // EXTRACCION CONFIRMADA"
	info_label.text = "RADIO // OPERADOR Y R-3 EXTRAIDOS\nDISTRITO 07 PERDIDO · DATOS XENOLOGICOS RECUPERADOS"
	if evac_light:
		evac_light.light_energy = 4.0
	mission_completed.emit()

func _set_stage(next_stage: int) -> void:
	stage = next_stage
	match stage:
		STAGE_GENERATOR:
			objective_label.text = "OBJETIVO // REACTIVA EL GENERADOR"
		STAGE_DEFEND:
			defend_remaining = defend_duration
			reinforcement_timer = 0.0
			blackout_triggered = false
			radio_warning_triggered = false
			brute_triggered = false
			xeno_pulse_triggered = false
			objective_label.text = "OBJETIVO // DEFIENDE EL GENERADOR"
		STAGE_SUPPLIES:
			objective_label.text = "OBJETIVO // RECUPERA SUMINISTROS"
		STAGE_EVAC:
			objective_label.text = "OBJETIVO // ALCANZA LA EXTRACCION"

func _request_reinforcements(count: int) -> void:
	var root := get_parent()
	if root and root.has_method("spawn_reinforcements"):
		root.spawn_reinforcements(count)

func _build_objective_props() -> void:
	generator_root = Node3D.new()
	generator_root.name = "MissionGenerator"
	generator_root.position = generator_position
	get_parent().add_child.call_deferred(generator_root)
	_build_generator.call_deferred()

	supply_root = Node3D.new()
	supply_root.name = "MissionSupplies"
	supply_root.position = supply_position
	supply_root.visible = false
	get_parent().add_child.call_deferred(supply_root)
	_build_supplies.call_deferred()

	evac_root = Node3D.new()
	evac_root.name = "MissionEvac"
	evac_root.position = evac_position
	evac_root.visible = false
	get_parent().add_child.call_deferred(evac_root)
	_build_evac.call_deferred()

func _build_generator() -> void:
	if generator_root == null:
		return
	_prop_box(generator_root, Vector3(0, 0.55, 0), Vector3(1.5, 1.1, 1.15), Color(0.12, 0.16, 0.12))
	_prop_box(generator_root, Vector3(0, 1.18, 0), Vector3(1.0, 0.18, 0.72), Color(0.24, 0.28, 0.22))
	generator_light = OmniLight3D.new()
	generator_light.position = Vector3(0, 1.55, 0)
	generator_light.light_color = Color(1.0, 0.22, 0.06)
	generator_light.light_energy = 2.2
	generator_light.omni_range = 5.0
	generator_light.shadow_enabled = false
	generator_root.add_child(generator_light)

func _build_supplies() -> void:
	if supply_root == null:
		return
	_prop_box(supply_root, Vector3(0, 0.35, 0), Vector3(1.25, 0.7, 0.9), Color(0.16, 0.25, 0.16))
	_prop_box(supply_root, Vector3(0, 0.72, 0), Vector3(1.28, 0.08, 0.93), Color(0.48, 0.52, 0.18))

func _build_evac() -> void:
	if evac_root == null:
		return
	_prop_box(evac_root, Vector3(0, 0.08, 0), Vector3(4.8, 0.16, 4.8), Color(0.06, 0.14, 0.20))
	_prop_box(evac_root, Vector3(0, 1.5, 0), Vector3(0.18, 3.0, 0.18), Color(0.18, 0.28, 0.34))
	evac_light = OmniLight3D.new()
	evac_light.position = Vector3(0, 3.2, 0)
	evac_light.light_color = Color(0.14, 0.58, 1.0)
	evac_light.light_energy = 2.8
	evac_light.omni_range = 8.0
	evac_light.shadow_enabled = false
	evac_root.add_child(evac_light)

func _prop_box(parent: Node3D, local_position: Vector3, size: Vector3, color: Color) -> void:
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh_instance.mesh = mesh
	mesh_instance.position = local_position
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = 0.78
	mesh_instance.material_override = mat
	parent.add_child(mesh_instance)
