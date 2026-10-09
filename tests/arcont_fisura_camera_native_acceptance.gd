extends SceneTree
## ARCONT P2: execute the pinned external FISURA scene (not a synthetic scene).
## The native runtime camera and cinematic meshes are exported as read-only
## geometry evidence. Never mutate game collision, asset definitions or mission.
const SCENE_PATH := "res://scenes/reactivo_13.tscn"
const OUTPUT := "res://arcont-fisura-camera-native.json"
const ADAPTER = preload("res://arcont_camera_shot_exporter.gd")

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed: PackedScene = load(SCENE_PATH) as PackedScene
    if packed == null:
        _fail("pinned game scene could not be loaded")
        return
    var world: Node3D = packed.instantiate()
    root.add_child(world)
    world.testing_disable_spawns = true
    if world.player == null or world.camera == null or world.cinematic_stage == null:
        _fail("actual playable world/camera/cinematic stage missing")
        return
    world.player.global_position = Vector3(-32.0, 1.0, 13.5)
    world.player.velocity = Vector3.ZERO
    world.camera_yaw = 0.0
    world.camera_pitch = 0.0
    for enemy in get_nodes_in_group("enemies"):
        enemy.set_physics_process(false)
    for _frame in range(8):
        await physics_frame
    world.set_process(false)
    world.set_physics_process(false)
    world.player.set_process(false)
    world.player.set_physics_process(false)
    world.cinematic_stage.set_process(false)
    world.camera.global_position = world._camera_position()
    world.camera.look_at(world._camera_target(), Vector3.UP)
    var camera: Camera3D = world.camera
    var physical_before: int = _collision_count(world)
    var lights_before: int = _lights(world)
    # The stage is a bounded camera-relevant scenery subset. The P2 camera
    # contract imposes <= 512 meshes; gameplay is not excluded from FISURA,
    # only from this first cinematic-dressing probe.
    var report: Dictionary = ADAPTER.capture(camera, world.cinematic_stage, OUTPUT,
        Vector2i(1280,720))
    if not report.get("ok",false):
        _fail(str(report.get("error", "native camera exporter failed")))
        return
    var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(OUTPUT))
    if typeof(data) != TYPE_DICTIONARY or data.get("protocol") != "arcont-camera-shot":
        _fail("native camera snapshot not persisted")
        return
    var meshes: Array = data.get("objects", [])
    if meshes.size() < 30 or meshes.size() > 512:
        _fail("expected real authored cinematic stage meshes 30..512, got %d" % meshes.size())
        return
    if data.get("capture_source") != "native-godot-self-reported":
        _fail("native camera source unmarked")
        return
    for mesh in meshes:
        if not str(mesh["id"]).contains("cinematic industrial dressing"):
            _fail("a mesh outside the original game-authored cinematic stage was exported")
            return
    if _collision_count(world) != physical_before or _lights(world) != lights_before:
        _fail("read-only diagnostic mutated gameplay physics or illumination")
        return
    print("ARCONT REAL FISURA CAMERA P2 PASS meshes=%d lights_unchanged=%d colliders_unchanged=%d source_commit=%s" %
        [meshes.size(),lights_before,physical_before, OS.get_environment("FISURA_PINNED_SHA")])
    quit(0)

func _collision_count(node: Node) -> int:
    var n := 1 if node is CollisionObject3D or node is CollisionShape3D else 0
    for child in node.get_children():
        n += _collision_count(child)
    return n

func _lights(node: Node) -> int:
    var n := 1 if node is Light3D else 0
    for child in node.get_children():
        n += _lights(child)
    return n

func _fail(reason: String) -> void:
    printerr("ARCONT REAL FISURA CAMERA P2 FAIL ", reason)
    quit(1)
