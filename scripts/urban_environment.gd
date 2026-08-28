extends Node3D

@export var district_size := Vector2(58.0, 72.0)
@export var road_width := 11.0
@export var sidewalk_height := 0.16

const CAR_MODELS := [
	"res://assets/provisional/city/car_hatchback.fbx",
	"res://assets/provisional/city/car_police.fbx",
	"res://assets/provisional/city/car_sedan.fbx",
	"res://assets/provisional/city/car_stationwagon.fbx"
]
const PROP_MODELS := {
	"bench": "res://assets/provisional/city/bench.fbx",
	"box_a": "res://assets/provisional/city/box_A.fbx",
	"box_b": "res://assets/provisional/city/box_B.fbx",
	"bush": "res://assets/provisional/city/bush.fbx"
}

var mat_asphalt: StandardMaterial3D
var mat_concrete: StandardMaterial3D
var mat_building_dark: StandardMaterial3D
var mat_building_mid: StandardMaterial3D
var mat_window: StandardMaterial3D
var mat_lane: StandardMaterial3D
var mat_rubble: StandardMaterial3D
var mat_military: StandardMaterial3D
var mat_alien: StandardMaterial3D
var mat_glow: StandardMaterial3D
var vehicle_index := 0

func _ready() -> void:
	_make_materials()
	_build_ground()
	_build_city_blocks()
	_build_centerpiece()
	_build_barricades()
	_build_abandoned_vehicles()
	_build_provisional_props()
	_build_alien_incursion()
	_build_spawn_points()
	_build_tactical_points()
	_build_landmarks()

func _make_materials() -> void:
	# Keep dark-night mood, but avoid the near-black values that collapsed on Android.
	mat_asphalt = _mat(Color(0.105, 0.115, 0.13), 0.96)
	mat_concrete = _mat(Color(0.34, 0.35, 0.37), 0.90)
	mat_building_dark = _mat(Color(0.20, 0.225, 0.26), 0.88)
	mat_building_mid = _mat(Color(0.27, 0.29, 0.32), 0.82)
	mat_rubble = _mat(Color(0.23, 0.20, 0.18), 1.0)
	mat_military = _mat(Color(0.24, 0.31, 0.22), 0.82)
	mat_alien = _mat(Color(0.14, 0.11, 0.18), 0.58)
	mat_lane = _mat(Color(0.66, 0.62, 0.39), 0.84)
	mat_window = _mat(Color(0.12, 0.19, 0.25), 0.42)
	mat_window.emission_enabled = true
	mat_window.emission = Color(0.045, 0.085, 0.12)
	mat_window.emission_energy_multiplier = 0.7
	mat_glow = _mat(Color(0.20, 0.04, 0.29), 0.42)
	mat_glow.emission_enabled = true
	mat_glow.emission = Color(0.72, 0.09, 1.0)
	mat_glow.emission_energy_multiplier = 3.2

func _mat(color: Color, roughness: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = roughness
	return material

func _build_ground() -> void:
	_box("Ground", Vector3(0, -0.18, 0), Vector3(district_size.x, 0.35, district_size.y), mat_asphalt, true)
	_box("SidewalkW", Vector3(-(road_width * 0.5 + 3.2), sidewalk_height * 0.5, 0), Vector3(6.2, sidewalk_height, district_size.y - 4.0), mat_concrete, true)
	_box("SidewalkE", Vector3(road_width * 0.5 + 3.2, sidewalk_height * 0.5, 0), Vector3(6.2, sidewalk_height, district_size.y - 4.0), mat_concrete, true)
	_box("CrossW", Vector3(-20.0, sidewalk_height * 0.5, 5.0), Vector3(17.0, sidewalk_height, 9.0), mat_asphalt, true)
	_box("CrossE", Vector3(20.0, sidewalk_height * 0.5, 5.0), Vector3(17.0, sidewalk_height, 9.0), mat_asphalt, true)
	# Thin markings give the player immediate orientation without expensive geometry.
	for z in range(-30, 31, 8):
		_box("LaneDash", Vector3(0.0, 0.015, float(z)), Vector3(0.16, 0.025, 3.2), mat_lane, false)
	for x in [-4.35, 4.35]:
		_box("RoadEdge", Vector3(x, 0.012, 0.0), Vector3(0.09, 0.022, district_size.y - 5.0), mat_lane, false)

func _build_city_blocks() -> void:
	_building(Vector3(-19.5, 3.5, -24.0), Vector3(12.0, 7.0, 13.0), mat_building_dark)
	_building(Vector3(-20.5, 4.8, -7.0), Vector3(14.0, 9.6, 10.0), mat_building_mid)
	_building(Vector3(-20.0, 5.8, 22.5), Vector3(13.0, 11.6, 15.0), mat_building_dark)
	_building(Vector3(20.0, 4.2, -25.0), Vector3(13.0, 8.4, 12.0), mat_building_mid)
	_building(Vector3(21.0, 3.2, -8.2), Vector3(11.0, 6.4, 9.0), mat_building_dark)
	_building(Vector3(20.0, 5.2, 21.0), Vector3(14.0, 10.4, 16.0), mat_building_mid)
	_building(Vector3(-10.7, 1.45, 14.5), Vector3(5.0, 2.9, 8.0), mat_building_mid)
	_building(Vector3(11.0, 1.7, -16.0), Vector3(5.5, 3.4, 7.0), mat_building_dark)

func _build_centerpiece() -> void:
	_box("CheckpointBase", Vector3(0, 0.20, 4.0), Vector3(7.0, 0.4, 9.0), mat_concrete, true)
	_box("CheckpointWallA", Vector3(-2.7, 0.8, 2.8), Vector3(0.6, 1.6, 5.0), mat_military, true)
	_box("CheckpointWallB", Vector3(2.7, 0.8, 5.4), Vector3(0.6, 1.6, 4.6), mat_military, true)
	_box("CheckpointCover", Vector3(0.0, 0.55, 6.9), Vector3(3.6, 1.1, 0.65), mat_military, true, Vector3(0, 12, 0))
	for data in [
		[Vector3(-3.8, 0.32, 8.3), Vector3(1.6, 0.65, 1.0), Vector3(8, 24, 5)],
		[Vector3(3.9, 0.28, 0.0), Vector3(1.3, 0.55, 1.6), Vector3(-5, -17, 10)],
		[Vector3(-1.0, 0.25, -0.7), Vector3(1.8, 0.5, 0.7), Vector3(12, 7, -8)]
	]: _box("Rubble", data[0], data[1], mat_rubble, true, data[2])

func _build_barricades() -> void:
	_box("BarricadeN1", Vector3(-2.9, 0.55, -22.0), Vector3(4.2, 1.1, 0.55), mat_military, true, Vector3(0, -12, 0))
	_box("BarricadeN2", Vector3(3.0, 0.55, -21.3), Vector3(3.2, 1.1, 0.55), mat_military, true, Vector3(0, 15, 0))
	_box("BarricadeS1", Vector3(-3.2, 0.55, 27.0), Vector3(3.8, 1.1, 0.55), mat_military, true, Vector3(0, 10, 0))
	_box("BarricadeW", Vector3(-13.2, 0.55, 5.5), Vector3(0.55, 1.1, 4.0), mat_military, true)
	_box("BarricadeE", Vector3(13.0, 0.55, 3.2), Vector3(0.55, 1.1, 4.2), mat_military, true)

func _build_abandoned_vehicles() -> void:
	_vehicle(Vector3(-2.4, 0.18, -9.5), Vector3(0, 14, 0))
	_vehicle(Vector3(2.8, 0.18, 16.5), Vector3(0, -20, 0))
	_vehicle(Vector3(-15.5, 0.18, 4.0), Vector3(0, 82, 0))

func _vehicle(position: Vector3, rotation_deg: Vector3) -> void:
	var collision_body := StaticBody3D.new()
	collision_body.name = "CarBody"
	collision_body.position = position + Vector3(0, 0.52, 0)
	collision_body.rotation_degrees = rotation_deg
	var shape_node := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(1.9, 1.05, 3.8)
	shape_node.shape = shape
	collision_body.add_child(shape_node)
	add_child(collision_body)
	var path: String = CAR_MODELS[vehicle_index % CAR_MODELS.size()]
	vehicle_index += 1
	_spawn_asset(path, position, rotation_deg)

func _build_provisional_props() -> void:
	_spawn_asset(PROP_MODELS["bench"], Vector3(-8.8, 0.15, -3.0), Vector3(0, 90, 0))
	_spawn_asset(PROP_MODELS["box_a"], Vector3(5.2, 0.15, 7.6), Vector3.ZERO)
	_spawn_asset(PROP_MODELS["box_b"], Vector3(5.9, 0.15, 7.1), Vector3(0, 24, 0))
	_spawn_asset(PROP_MODELS["bush"], Vector3(-9.8, 0.15, 23.0), Vector3.ZERO)
	_spawn_asset(PROP_MODELS["bush"], Vector3(9.4, 0.15, -24.0), Vector3.ZERO)

func _spawn_asset(path: String, position: Vector3, rotation_deg := Vector3.ZERO, scale_value := Vector3.ONE) -> Node3D:
	var packed := load(path) as PackedScene
	if packed == null:
		return null
	var instance := packed.instantiate() as Node3D
	if instance == null:
		return null
	instance.name = "Provisional3D"
	instance.position = position
	instance.rotation_degrees = rotation_deg
	instance.scale = scale_value
	add_child(instance)
	return instance

func _build_alien_incursion() -> void:
	for data in [
		[Vector3(8.4, 1.05, 10.0), Vector3(0.65, 2.1, 0.65), Vector3(0, 0, 18)],
		[Vector3(10.0, 1.45, 11.4), Vector3(0.55, 2.9, 0.55), Vector3(14, 0, -11)],
		[Vector3(7.0, 0.85, 12.1), Vector3(0.48, 1.7, 0.48), Vector3(-12, 0, 20)],
		[Vector3(9.2, 0.62, 13.0), Vector3(1.5, 0.35, 1.5), Vector3(0, 33, 0)]
	]: _box("AlienGrowth", data[0], data[1], mat_glow, false, data[2])
	var light := OmniLight3D.new(); light.name = "AlienGlow"; light.position = Vector3(8.8,2.3,11.2); light.light_color = Color(0.66,0.12,1.0); light.light_energy = 2.4; light.omni_range = 9.0; light.shadow_enabled = false; add_child(light)

func _build_landmarks() -> void:
	var beacon := OmniLight3D.new(); beacon.position = Vector3(-0.5,4.2,-29.0); beacon.light_color = Color(0.15,0.55,1.0); beacon.light_energy = 2.0; beacon.omni_range = 8.0; beacon.shadow_enabled = false; add_child(beacon)
	_box("EvacPole", Vector3(-0.5,2.0,-29.0), Vector3(0.22,4.0,0.22), mat_military, true)
	_box("BrokenSign", Vector3(0.0,3.6,-13.0), Vector3(6.6,0.55,0.28), mat_concrete, false, Vector3(0,0,-7))

func _build_spawn_points() -> void:
	var points := [Vector3(-4,0.2,-32),Vector3(4.5,0.2,-32),Vector3(-4.2,0.2,32),Vector3(4,0.2,32),Vector3(-25,0.2,4),Vector3(-25,0.2,8),Vector3(25,0.2,2),Vector3(25,0.2,7),Vector3(-11,0.2,-29),Vector3(12,0.2,29)]
	for i in points.size():
		var marker := Marker3D.new(); marker.name = "EnemySpawn%02d" % i; marker.position = points[i]; marker.add_to_group("enemy_spawn"); add_child(marker)

func _build_tactical_points() -> void:
	var points := [Vector3(-3.0,0.2,-20.8),Vector3(3.0,0.2,-20.0),Vector3(-3.1,0.2,25.7),Vector3(-11.8,0.2,5.4),Vector3(11.7,0.2,3.2),Vector3(-1.2,0.2,6.2),Vector3(1.2,0.2,7.8),Vector3(-4.0,0.2,-9.3),Vector3(-0.8,0.2,-9.7),Vector3(1.2,0.2,16.2),Vector3(4.5,0.2,16.8),Vector3(-14.0,0.2,2.2),Vector3(-17.0,0.2,5.8),Vector3(8.2,0.2,-13.0),Vector3(13.5,0.2,-13.2)]
	for i in points.size():
		var marker := Marker3D.new(); marker.name = "TacticalCover%02d" % i; marker.position = points[i]; marker.add_to_group("tactical_cover"); add_child(marker)

func _building(position: Vector3, size: Vector3, material: Material) -> void:
	_box("Building", position, size, material, true)
	# Horizontal ledges plus window strips prevent buildings reading as giant black planes.
	for y in range(2, int(size.y), 2):
		var front := position + Vector3(0, -size.y * 0.5 + float(y), -size.z * 0.5 - 0.022)
		var back := position + Vector3(0, -size.y * 0.5 + float(y), size.z * 0.5 + 0.022)
		_box("FacadeStrip", front, Vector3(size.x * 0.78, 0.24, 0.045), mat_window, false)
		_box("FacadeStrip", back, Vector3(size.x * 0.78, 0.24, 0.045), mat_window, false)
	var roof := position + Vector3(0, size.y * 0.5 + 0.10, 0)
	_box("RoofTrim", roof, Vector3(size.x * 1.02, 0.18, size.z * 1.02), mat_concrete, false)

func _box(node_name: String, position: Vector3, size: Vector3, material: Material, collision_enabled: bool, rotation_deg := Vector3.ZERO) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.name = node_name
	body.position = position
	body.rotation_degrees = rotation_deg
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh_instance.mesh = mesh
	mesh_instance.material_override = material
	body.add_child(mesh_instance)
	if collision_enabled:
		var shape_node := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = size
		shape_node.shape = shape
		body.add_child(shape_node)
	add_child(body)
	return body
