extends RefCounted
## Optional external-project adapter for ARCONT P2 camera-projection evidence.
## This script is a TEMPLATE: copy into a Godot game and invoke explicitly.
## It never modifies scene physics, navigation, materials or player controls.
## Caller/CI must bind scene+commit and verify the output provenance separately.
const MAX_SCAN := 12000
const MAX_OBJECTS := 512
const ALLOWED := ["structure", "functional", "dressing", "player",
                  "enemy", "objective", "cover"]

static func capture(camera: Camera3D, game_root: Node, path: String = "user://arcont-camera-shot.json", viewport_override: Vector2i = Vector2i.ZERO) -> Dictionary:
    if camera == null or not camera.is_inside_tree():
        return {"ok": false, "error": "A native in-tree Camera3D is required"}
    if camera.keep_aspect != Camera3D.KEEP_HEIGHT:
        return {"ok": false, "error": "Only vertical-FOV KEEP_HEIGHT camera is supported"}
    # Dedicated headless CI can have no window dimensions; an explicitly
    # recorded synthetic viewport is permitted, never labelled measured.
    var is_override: bool = viewport_override.x >= 128 and viewport_override.y >= 128
    var viewport: Vector2 = Vector2(viewport_override) if is_override else camera.get_viewport().get_visible_rect().size
    if viewport.x < 128 or viewport.y < 128:
        return {"ok": false, "error": "Native viewport invalid"}
    var eye: Vector3 = camera.global_position
    var forward: Vector3 = -camera.global_transform.basis.z.normalized()
    var camera_up: Vector3 = camera.global_transform.basis.y.normalized()
    var records: Array[Dictionary] = []
    var pending: Array[Node] = [game_root]
    var visited := 0
    while not pending.is_empty():
        if visited >= MAX_SCAN:
            return {"ok": false, "error": "Scene tree exceeds bounded node scan"}
        var node: Node = pending.pop_back()
        visited += 1
        if node is MeshInstance3D and node.is_visible_in_tree():
            var m: MeshInstance3D = node as MeshInstance3D
            if m.mesh != null:
                var aabb: AABB = m.get_aabb()
                var lo: Vector3 = m.global_transform * aabb.get_endpoint(0)
                var hi: Vector3 = lo
                for n in range(1, 8):
                    var pt: Vector3 = m.global_transform * aabb.get_endpoint(n)
                    lo = lo.min(pt)
                    hi = hi.max(pt)
                var bounds: Vector3 = hi - lo
                if bounds.x > 0.0001 and bounds.y > 0.0001 and bounds.z > 0.0001:
                    var role: String = str(m.get_meta("arcont_visual_role", "structure"))
                    if not ALLOWED.has(role):
                        role = "structure"
                    records.append({
                        "id": _bounded_identifier(str(m.get_path())),
                        "center": _vector((hi + lo) * 0.5),
                        "size": _vector(bounds),
                        "role": role
                    })
                    if records.size() > MAX_OBJECTS:
                        return {"ok": false, "error": "Scene contains more than 512 visible meshes; choose a bounded gameplay area"}
        for child in node.get_children():
            pending.push_back(child)
    var data := {
        "protocol": "arcont-camera-shot",
        "version": 1,
        "capture_source": "native-godot-self-reported",
        "camera": {
            "position": _vector(eye),
            "target": _vector(eye + forward),
            "up": _vector(camera_up),
            "fov_y_degrees": camera.fov,
            "viewport": [int(viewport.x), int(viewport.y)],
            "viewport_source": "explicit-headless-fixture" if is_override else "native-camera-viewport"
        },
        "objects": records
    }
    var file := FileAccess.open(path, FileAccess.WRITE)
    if file == null:
        return {"ok": false, "error": "Cannot write requested shot path"}
    file.store_string(JSON.stringify(data, "  ") + "\n")
    file.close()
    return {"ok": true, "path": path, "objects": records.size(),
            "limitations": "Self-reported native camera; external CI must attest frame, build, renderer and source revision"}

static func _bounded_identifier(original: String) -> String:
    # Deep, source-imported GLB node paths can exceed the diagnostic protocol's
    # 128-character ID bound. Preserve a recognizable prefix plus stable SHA-256,
    # avoiding lossy truncation collisions across sibling imported meshes.
    if original.length() <= 128:
        return original
    return original.substr(0, 56) + "#" + original.sha256_text()

static func _vector(v: Vector3) -> Array:
    return [v.x, v.y, v.z]
