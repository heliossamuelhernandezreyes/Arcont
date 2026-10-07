#!/usr/bin/env python3
"""Live acceptance for ARCONT Development Session v1.

The acceptance starts from an empty directory, bootstraps a Godot project,
creates a two-milestone development session through the Universal Bridge,
executes two separate bounded plans with a persisted session revision between
them, then runs Godot to prove the resulting Player actually moves.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def bridge(arcont: Path, project: Path, operation: str, arguments: dict, *, allow_write: bool = False) -> dict:
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
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    if not proc.stdout.strip():
        raise RuntimeError({"operation": operation, "code": proc.returncode, "stderr": proc.stderr[-4000:]})
    payload = json.loads(proc.stdout)
    if proc.returncode != 0 or payload.get("ok") is not True:
        raise RuntimeError({"operation": operation, "code": proc.returncode, "payload": payload, "stderr": proc.stderr[-4000:]})
    return payload


def writer_child(envelope: dict) -> dict:
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


def direct_child(envelope: dict) -> dict:
    tool = envelope.get("result")
    if not isinstance(tool, dict) or tool.get("ok") is not True:
        raise RuntimeError({"direct_tool_failed": tool})
    result = tool.get("result")
    if not isinstance(result, dict):
        raise RuntimeError({"direct_result_missing": tool})
    return result


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
                "project_id": "development_session_ci",
                "title": "Development Session CI",
                "genre": "third-person action",
                "targets": ["Windows"],
                "goals": ["Create and verify bounded player movement over multiple development milestones."],
                "priorities": ["movement", "evidence", "bounded iteration"],
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

    capabilities = bridge(arcont, project, "development.session.capabilities", {})
    cap_result = direct_child(capabilities)
    if "godot.structured.control" not in cap_result["eligible_capabilities"]:
        raise RuntimeError("structured control missing from development session eligible capabilities")
    (evidence / "02-capabilities.json").write_text(json.dumps(capabilities, indent=2), encoding="utf-8")

    session_create = bridge(
        arcont,
        project,
        "development.session.create",
        {
            "spec": {
                "id": "prototype",
                "goal": "Create a tiny playable third-person movement prototype through bounded milestones.",
                "capability_allowlist": ["godot.structured.control"],
                "permissions": {"project_write": True},
                "budgets": {
                    "max_plan_runs": 4,
                    "max_execution_steps": 24,
                    "max_write_steps": 16,
                    "max_failed_runs": 2,
                },
                "milestones": [
                    {
                        "id": "movement",
                        "goal": "Create WASD input, player movement code and the Player scene node.",
                        "acceptance": [
                            "All four movement input actions are written through Godot.",
                            "Player GDScript validates.",
                            "Player exists in the main scene with the script attached.",
                        ],
                    },
                    {
                        "id": "verification",
                        "goal": "Inspect and refine the generated movement implementation.",
                        "acceptance": [
                            "Player script inspection reports CharacterBody3D.",
                            "Main scene inspection succeeds.",
                            "The movement function can be revision-patched and revalidated.",
                        ],
                    },
                ],
            }
        },
        allow_write=True,
    )
    created = writer_child(session_create)
    state1 = created["session"]
    (evidence / "03-session-create.json").write_text(json.dumps(session_create, indent=2), encoding="utf-8")

    movement_source = """extends CharacterBody3D

@export var speed: float = 4.0

func _physics_process(_delta):
    var input_vector := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    velocity = Vector3(input_vector.x, 0.0, input_vector.y) * speed
    move_and_slide()
"""

    plan1 = {
        "protocol": "arcont-agent-plan",
        "version": 1,
        "id": "movement_core",
        "goal": "Create bounded WASD player movement and attach it to the main scene.",
        "permissions": {"project_write": True},
        "capability_allowlist": ["godot.structured.control"],
        "steps": [
            {
                "id": "validate",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {"protocol_version": 1, "operation": "validate"},
                "expect": [{"pointer": "/result/ok", "op": "equals", "value": True}],
            },
            {
                "id": "forward",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {
                    "protocol_version": 1,
                    "operation": "input.action.set",
                    "if_revision": {"$from": "validate", "pointer": "/result/result/project_revision"},
                    "action": "move_forward",
                    "deadzone": 0.2,
                    "events": [{"type": "key", "keycode": "W", "physical": True}],
                },
            },
            {
                "id": "back",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {
                    "protocol_version": 1,
                    "operation": "input.action.set",
                    "if_revision": {"$from": "forward", "pointer": "/result/result/revision"},
                    "action": "move_back",
                    "deadzone": 0.2,
                    "events": [{"type": "key", "keycode": "S", "physical": True}],
                },
            },
            {
                "id": "left",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {
                    "protocol_version": 1,
                    "operation": "input.action.set",
                    "if_revision": {"$from": "back", "pointer": "/result/result/revision"},
                    "action": "move_left",
                    "deadzone": 0.2,
                    "events": [{"type": "key", "keycode": "A", "physical": True}],
                },
            },
            {
                "id": "right",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {
                    "protocol_version": 1,
                    "operation": "input.action.set",
                    "if_revision": {"$from": "left", "pointer": "/result/result/revision"},
                    "action": "move_right",
                    "deadzone": 0.2,
                    "events": [{"type": "key", "keycode": "D", "physical": True}],
                },
            },
            {
                "id": "script",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {
                    "protocol_version": 1,
                    "operation": "script.create",
                    "path": "scripts/player.gd",
                    "if_revision": None,
                    "source": movement_source,
                },
                "expect": [{"pointer": "/result/result/revision", "op": "exists"}],
            },
            {
                "id": "scene_before",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {
                    "protocol_version": 1,
                    "operation": "scene.inspect",
                    "scene": "scenes/main.tscn",
                },
                "expect": [{"pointer": "/result/result/revision", "op": "exists"}],
            },
            {
                "id": "scene_edit",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {
                    "protocol_version": 1,
                    "operation": "scene.edit",
                    "scene": "scenes/main.tscn",
                    "if_revision": {"$from": "scene_before", "pointer": "/result/result/revision"},
                    "changes": [
                        {"op": "add", "parent": ".", "name": "Player", "type": "CharacterBody3D"},
                        {"op": "attach_script", "path": "Player", "script": "res://scripts/player.gd"},
                    ],
                },
                "expect": [{"pointer": "/result/result/revision", "op": "exists"}],
            },
        ],
    }

    run1 = bridge(
        arcont,
        project,
        "development.session.execute",
        {
            "session_id": "prototype",
            "if_session_revision": state1["revision"],
            "milestone_id": "movement",
            "plan": plan1,
            "complete_milestone": True,
            "completion_note": "Movement scaffold plan completed with all machine-readable expectations.",
        },
        allow_write=True,
    )
    result1 = writer_child(run1)
    state2 = result1["session"]
    if state2["milestones"][0]["status"] != "completed" or state2["milestones"][1]["status"] != "active":
        raise RuntimeError({"unexpected_milestone_transition": state2["milestones"]})
    if state2["revision"] == state1["revision"]:
        raise RuntimeError("session revision did not advance after first plan")
    (evidence / "04-run-movement.json").write_text(json.dumps(run1, indent=2), encoding="utf-8")

    patch_source = """func _physics_process(_delta):
    var input_vector := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    var direction := Vector3(input_vector.x, 0.0, input_vector.y)
    velocity = direction * speed
    move_and_slide()
"""

    plan2 = {
        "protocol": "arcont-agent-plan",
        "version": 1,
        "id": "verify_refine",
        "goal": "Inspect and revision-patch the generated movement implementation.",
        "permissions": {"project_write": True},
        "capability_allowlist": ["godot.structured.control"],
        "steps": [
            {
                "id": "script_before",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {
                    "protocol_version": 1,
                    "operation": "script.inspect",
                    "path": "scripts/player.gd",
                },
                "expect": [{"pointer": "/result/result/extends", "op": "equals", "value": "CharacterBody3D"}],
            },
            {
                "id": "scene_check",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {
                    "protocol_version": 1,
                    "operation": "scene.inspect",
                    "scene": "scenes/main.tscn",
                },
                "expect": [{"pointer": "/result/result/revision", "op": "exists"}],
            },
            {
                "id": "patch_movement",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {
                    "protocol_version": 1,
                    "operation": "script.function.replace",
                    "path": "scripts/player.gd",
                    "if_revision": {"$from": "script_before", "pointer": "/result/result/revision"},
                    "function": "_physics_process",
                    "source": patch_source,
                },
                "expect": [{"pointer": "/result/result/revision", "op": "exists"}],
            },
            {
                "id": "script_after",
                "kind": "invoke",
                "capability": "godot.structured.control",
                "request": {
                    "protocol_version": 1,
                    "operation": "script.inspect",
                    "path": "scripts/player.gd",
                },
                "expect": [{"pointer": "/result/result/extends", "op": "equals", "value": "CharacterBody3D"}],
            },
        ],
    }

    run2 = bridge(
        arcont,
        project,
        "development.session.execute",
        {
            "session_id": "prototype",
            "if_session_revision": state2["revision"],
            "milestone_id": "verification",
            "plan": plan2,
            "complete_milestone": True,
            "completion_note": "Inspection and bounded function patch passed.",
        },
        allow_write=True,
    )
    result2 = writer_child(run2)
    state3 = result2["session"]
    if state3["status"] != "completed":
        raise RuntimeError({"session_not_completed": state3})
    if state3["counters"]["plan_runs"] != 2 or state3["counters"]["milestones_completed"] != 2:
        raise RuntimeError({"unexpected_session_counters": state3["counters"]})
    (evidence / "05-run-verification.json").write_text(json.dumps(run2, indent=2), encoding="utf-8")

    inspected = bridge(arcont, project, "development.session.inspect", {"session_id": "prototype"})
    final_session = direct_child(inspected)
    if (
        not final_session["environment"]["intent_matches"]
        or not final_session["environment"]["registry_matches"]
        or not final_session["environment"]["toolchain_matches"]
    ):
        raise RuntimeError({"session_environment_drift": final_session["environment"]})
    if final_session["session"]["revision"] != state3["revision"]:
        raise RuntimeError("persisted session revision differs from final execute response")
    (evidence / "06-session-final.json").write_text(json.dumps(inspected, indent=2), encoding="utf-8")

    # Independent runtime evidence for the artifact produced by the session.
    probe = project / ".arcont/development-session-runtime-probe.gd"
    probe.write_text(
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
        raise RuntimeError("GODOT_BIN is required")
    proc = subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project),
            "--script",
            "res://.arcont/development-session-runtime-probe.gd",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    (evidence / "07-runtime.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (evidence / "07-runtime.stderr.log").write_text(proc.stderr, encoding="utf-8")
    runtime = None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict) and "delta_z" in candidate:
                runtime = candidate
    if proc.returncode != 0 or not isinstance(runtime, dict) or runtime.get("ok") is not True:
        raise RuntimeError({"runtime_failed": True, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]})

    history = final_session["session"]["history"]
    receipt_paths = [project / row["receipt"] for row in history]
    for path in receipt_paths:
        if not path.is_file():
            raise RuntimeError({"missing_receipt": str(path)})

    summary = {
        "ok": True,
        "session": {
            "id": state3["id"],
            "status": state3["status"],
            "revision": state3["revision"],
            "counters": state3["counters"],
            "remaining": final_session["remaining"],
            "history": history,
            "project_intent_sha256": state3["project_intent_sha256"],
            "registry_sha256": state3["registry_sha256"],
            "toolchain_sha256": state3["toolchain_sha256"],
        },
        "runtime": runtime,
        "assertions": {
            "two_bounded_plans_executed": state3["counters"]["plan_runs"] == 2,
            "two_milestones_completed": state3["counters"]["milestones_completed"] == 2,
            "session_completed": state3["status"] == "completed",
            "session_revision_advanced": state1["revision"] != state2["revision"] != state3["revision"],
            "receipts_persisted": len(receipt_paths) == 2 and all(path.is_file() for path in receipt_paths),
            "intent_pin_still_matches": final_session["environment"]["intent_matches"] is True,
            "registry_pin_still_matches": final_session["environment"]["registry_matches"] is True,
            "toolchain_pin_still_matches": final_session["environment"]["toolchain_matches"] is True,
            "runtime_player_moved": runtime["delta_z"] < -0.01,
        },
        "limits": [
            "The external acceptance harness supplies the two development plans; ARCONT does not call an LLM itself.",
            "Runtime movement is verified after session completion by the CI harness; Development Session v1 orchestrates existing ARCONT capabilities and does not add a generic playtest primitive.",
            "Headless Linux evidence does not establish Android performance or subjective game quality.",
        ],
    }
    if not all(summary["assertions"].values()):
        raise RuntimeError({"acceptance_assertions": summary["assertions"]})
    (evidence / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
