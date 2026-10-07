#!/usr/bin/env python3
"""Live acceptance for ARCONT structured Godot editing.

Starts from an empty directory, bootstraps Godot, creates gameplay input,
GDScript, a mesh resource and a Player node through the Universal Bridge, then
runs a headless runtime probe that proves the generated player moves when an
input action is pressed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bridge(arcont: Path, project: Path, operation: str, arguments: dict, allow_write: bool = False) -> dict:
    request = {
        "protocol": "arcont-bridge",
        "version": 1,
        "request_id": operation.replace(".", "-"),
        "operation": operation,
        "arguments": arguments,
    }
    command = [
        sys.executable,
        str(arcont / "tools/arcont_bridge.py"),
        "--project",
        str(project),
        "--request",
        "-",
    ]
    if allow_write:
        command.append("--allow-project-write")
    proc = subprocess.run(
        command,
        cwd=arcont,
        input=json.dumps(request),
        text=True,
        capture_output=True,
        timeout=900,
        check=False,
    )
    if not proc.stdout.strip():
        raise RuntimeError({"operation": operation, "code": proc.returncode, "stderr": proc.stderr[-4000:]})
    payload = json.loads(proc.stdout)
    if proc.returncode != 0 or payload.get("ok") is not True:
        raise RuntimeError({"operation": operation, "code": proc.returncode, "payload": payload, "stderr": proc.stderr[-4000:]})
    return payload


def writer_result(envelope: dict) -> dict:
    invocation = envelope["result"]
    if invocation.get("ok") is not True:
        raise RuntimeError({"invoke_failed": invocation})
    child = invocation.get("result")
    if not isinstance(child, dict) or child.get("ok") is not True:
        raise RuntimeError({"child_failed": child})
    result = child.get("result")
    if not isinstance(result, dict):
        raise RuntimeError({"child_result_missing": child})
    return result


def direct_result(envelope: dict) -> dict:
    result = envelope.get("result")
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise RuntimeError({"direct_result_failed": result})
    child = result.get("result")
    return child if isinstance(child, dict) else result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arcont", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()

    arcont = args.arcont.resolve()
    project = args.project.resolve()
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=True)

    bootstrap = bridge(
        arcont,
        project,
        "project.bootstrap",
        {
            "template": "godot-3d-minimal",
            "intent": {
                "protocol": "arcont-project-intent",
                "version": 1,
                "project_id": "structured_gameplay_ci",
                "title": "Structured Gameplay CI",
                "genre": "third-person action",
                "targets": ["Windows"],
                "goals": ["Prove fresh-project gameplay creation through structured ARCONT operations"],
                "priorities": ["input", "movement", "revision safety"],
                "asset_policy": {
                    "user_assets": True,
                    "public_assets": False,
                    "commercial_use_required": True,
                    "allow_network_discovery": False,
                },
            },
        },
        allow_write=True,
    )
    (evidence / "01-bootstrap.json").write_text(json.dumps(bootstrap, indent=2), encoding="utf-8")

    validate = bridge(arcont, project, "godot.structured.validate", {})
    (evidence / "02-validate.json").write_text(json.dumps(validate, indent=2), encoding="utf-8")

    input_specs = [
        ("move_forward", "W"),
        ("move_back", "S"),
        ("move_left", "A"),
        ("move_right", "D"),
    ]
    input_receipts = []
    for action, key in input_specs:
        revision = sha(project / "project.godot")
        receipt = bridge(
            arcont,
            project,
            "godot.input.action.set",
            {
                "if_revision": revision,
                "action": action,
                "deadzone": 0.2,
                "events": [{"type": "key", "keycode": key, "physical": True}],
            },
            allow_write=True,
        )
        input_receipts.append(receipt)
    (evidence / "03-input.json").write_text(json.dumps(input_receipts, indent=2), encoding="utf-8")

    player_source = """extends CharacterBody3D

@export var speed: float = 4.0

func _physics_process(_delta):
    var input_vector := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    velocity = Vector3(input_vector.x, 0.0, input_vector.y) * speed
    move_and_slide()
"""
    script_create = bridge(
        arcont,
        project,
        "godot.script.create",
        {
            "path": "scripts/player.gd",
            "if_revision": None,
            "source": player_source,
        },
        allow_write=True,
    )
    created_script = writer_result(script_create)
    (evidence / "04-script-create.json").write_text(json.dumps(script_create, indent=2), encoding="utf-8")

    resource_edit = bridge(
        arcont,
        project,
        "godot.resource.edit",
        {
            "resource": "resources/player_mesh.tres",
            "if_revision": None,
            "resource_type": "BoxMesh",
            "changes": [
                {
                    "op": "set",
                    "property": "size",
                    "value": {"$type": "Vector3", "value": [0.8, 1.8, 0.8]},
                }
            ],
        },
        allow_write=True,
    )
    created_resource = writer_result(resource_edit)
    (evidence / "05-resource.json").write_text(json.dumps(resource_edit, indent=2), encoding="utf-8")

    scene_revision = sha(project / "scenes/main.tscn")
    scene_edit = bridge(
        arcont,
        project,
        "godot.scene.edit",
        {
            "scene": "scenes/main.tscn",
            "if_revision": scene_revision,
            "changes": [
                {"op": "add", "parent": ".", "name": "Player", "type": "CharacterBody3D"},
                {"op": "attach_script", "path": "Player", "script": "res://scripts/player.gd"},
                {
                    "op": "set",
                    "path": "Player",
                    "property": "position",
                    "value": {"$type": "Vector3", "value": [0.0, 0.0, 0.0]},
                },
                {"op": "add", "parent": "Player", "name": "PlayerBody", "type": "MeshInstance3D"},
                {
                    "op": "set",
                    "path": "Player/PlayerBody",
                    "property": "mesh",
                    "value": {"$type": "Resource", "path": "res://resources/player_mesh.tres"},
                },
            ],
        },
        allow_write=True,
    )
    created_scene = writer_result(scene_edit)
    (evidence / "06-scene-edit.json").write_text(json.dumps(scene_edit, indent=2), encoding="utf-8")

    script_inspect = bridge(
        arcont,
        project,
        "godot.script.inspect",
        {"path": "scripts/player.gd"},
    )
    inspected_script = direct_result(script_inspect)
    scene_inspect = bridge(
        arcont,
        project,
        "godot.scene.inspect",
        {"scene": "scenes/main.tscn"},
        allow_write=True,
    )
    inspected_scene = writer_result(scene_inspect)
    resource_inspect = bridge(
        arcont,
        project,
        "godot.resource.inspect",
        {"resource": "resources/player_mesh.tres", "properties": ["size"]},
        allow_write=True,
    )
    inspected_resource = writer_result(resource_inspect)
    (evidence / "07-inspect.json").write_text(
        json.dumps(
            {
                "script": script_inspect,
                "scene": scene_inspect,
                "resource": resource_inspect,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    replacement = """func _physics_process(_delta):
    var input_vector := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    var direction := Vector3(input_vector.x, 0.0, input_vector.y)
    velocity = direction * speed
    move_and_slide()
"""
    function_patch = bridge(
        arcont,
        project,
        "godot.script.function.replace",
        {
            "path": "scripts/player.gd",
            "if_revision": inspected_script["revision"],
            "function": "_physics_process",
            "source": replacement,
        },
        allow_write=True,
    )
    patched_script = writer_result(function_patch)
    (evidence / "08-function-patch.json").write_text(json.dumps(function_patch, indent=2), encoding="utf-8")

    # Runtime evidence: use Godot input injection to prove the generated gameplay
    # script actually moves the generated Player node.
    probe_path = project / ".arcont/structured-gameplay-probe.gd"
    probe_path.write_text(
        """extends SceneTree

func _initialize() -> void:
    var packed = load("res://scenes/main.tscn")
    if not (packed is PackedScene):
        print(JSON.stringify({"ok": false, "error": "main scene missing"}))
        quit(2)
        return
    var world = packed.instantiate()
    root.add_child(world)
    await process_frame
    var player = world.get_node_or_null("Player")
    if player == null:
        print(JSON.stringify({"ok": false, "error": "Player missing"}))
        quit(2)
        return
    var before = player.global_position
    Input.action_press("move_forward")
    for _i in range(12):
        await physics_frame
    Input.action_release("move_forward")
    var after = player.global_position
    var moved = after.z < before.z - 0.01
    print(JSON.stringify({
        "ok": moved,
        "before": [before.x, before.y, before.z],
        "after": [after.x, after.y, after.z],
        "delta_z": after.z - before.z
    }))
    quit(0 if moved else 1)
""",
        encoding="utf-8",
    )
    godot = os.environ.get("GODOT_BIN")
    if not godot:
        raise RuntimeError("GODOT_BIN is required for live acceptance")
    proc = subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project),
            "--script",
            "res://.arcont/structured-gameplay-probe.gd",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    (evidence / "09-runtime.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (evidence / "09-runtime.stderr.log").write_text(proc.stderr, encoding="utf-8")
    runtime_json = None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict) and "delta_z" in candidate:
                runtime_json = candidate
    if proc.returncode != 0 or not isinstance(runtime_json, dict) or runtime_json.get("ok") is not True:
        raise RuntimeError(
            {
                "runtime_probe_failed": True,
                "code": proc.returncode,
                "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-4000:],
            }
        )

    scene_nodes = inspected_scene["engine"]["result"]["nodes"]
    node_paths = {row["path"] for row in scene_nodes}
    resource_props = inspected_resource["engine"]["result"]["properties"]
    size_value = resource_props["size"]["value"]
    size_roundtripped = (
        resource_props["size"].get("$type") == "Vector3"
        and len(size_value) == 3
        and abs(float(size_value[0]) - 0.8) < 0.001
        and abs(float(size_value[1]) - 1.8) < 0.001
        and abs(float(size_value[2]) - 0.8) < 0.001
    )
    summary = {
        "ok": True,
        "script": {
            "create_revision": created_script["revision"],
            "inspect_revision": inspected_script["revision"],
            "patched_revision": patched_script["revision"],
            "functions": inspected_script["functions"],
        },
        "resource": {
            "revision": created_resource["revision"],
            "size": resource_props["size"],
        },
        "scene": {
            "revision": created_scene["revision"],
            "nodes": sorted(node_paths),
        },
        "runtime": runtime_json,
        "assertions": {
            "player_node_created": "Player" in node_paths,
            "player_mesh_created": "Player/PlayerBody" in node_paths,
            "script_attached": any(row["path"] == "Player" and row["script"] == "res://scripts/player.gd" for row in scene_nodes),
            "resource_size_roundtripped": size_roundtripped,
            "function_patch_changed_revision": patched_script["revision"] != inspected_script["revision"],
            "runtime_input_moved_player": runtime_json["ok"] is True and runtime_json["delta_z"] < -0.01,
        },
        "limits": [
            "Headless Linux runtime proves structured gameplay behavior, not Android performance or AAA feel.",
            "GDScript privileged-API denylist is defense-in-depth, not a complete language sandbox.",
            "Structured v1 intentionally excludes arbitrary shell, raw arbitrary file writes and network/editor APIs.",
        ],
    }
    if not all(summary["assertions"].values()):
        raise RuntimeError({"structured_acceptance_assertions": summary["assertions"]})
    (evidence / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
