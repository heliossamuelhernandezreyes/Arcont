#!/usr/bin/env python3
"""Create a minimal external Godot project from an empty directory.

ARCONT remains free of embedded production projects: this tool only writes to
an explicitly authorized external project root. The bootstrap is intentionally
small and deterministic; it creates a valid Godot shell, persistent project
intent, authoring directories and an ARCONT receipt, but no network content.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = 1
OPERATIONS = ("capabilities", "bootstrap")
TEMPLATES = ("godot-3d-minimal", "godot-2d-minimal")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_intent(intent: Any) -> dict[str, Any]:
    try:
        from tools.arcont_bridge import validate_intent
    except ModuleNotFoundError:
        from arcont_bridge import validate_intent
    return validate_intent(intent)


def _godot_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _project_godot(intent: dict[str, Any]) -> str:
    title = _godot_string(intent["title"])
    return f'''config_version=5

[application]

config/name={title}
run/main_scene="res://scenes/main.tscn"

[display]

window/size/viewport_width=1280
window/size/viewport_height=720
window/size/window_width_override=1280
window/size/window_height_override=720

[rendering]

renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
textures/default_filters/use_nearest_mipmap_filter=false
'''


def _scene_3d() -> str:
    return '''[gd_scene load_steps=2 format=3]

[sub_resource type="BoxMesh" id="BoxMesh_bootstrap"]
size = Vector3(2, 2, 2)

[node name="Main" type="Node3D"]

[node name="DirectionalLight3D" type="DirectionalLight3D" parent="."]
rotation_degrees = Vector3(-55, -25, 0)
shadow_enabled = true

[node name="Camera3D" type="Camera3D" parent="."]
position = Vector3(0, 1.5, 6)
rotation_degrees = Vector3(-8, 0, 0)
current = true

[node name="BootstrapMesh" type="MeshInstance3D" parent="."]
mesh = SubResource("BoxMesh_bootstrap")
'''


def _scene_2d() -> str:
    return '''[gd_scene format=3]

[node name="Main" type="Node2D"]

[node name="Camera2D" type="Camera2D" parent="."]
position = Vector2(640, 360)
enabled = true

[node name="BootstrapShape" type="Polygon2D" parent="."]
position = Vector2(640, 360)
polygon = PackedVector2Array(-80, -80, 80, -80, 80, 80, -80, 80)
color = Color(0.82, 0.82, 0.82, 1)
'''


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def bootstrap(project: Path, intent: dict[str, Any], template: str) -> dict[str, Any]:
    root = Path(project).resolve()
    if not root.is_dir():
        raise ValueError("bootstrap target must be an existing directory")
    if any(root.iterdir()):
        raise ValueError("bootstrap target must be empty")
    if template not in TEMPLATES:
        raise ValueError(f"unsupported bootstrap template: {template}")
    intent = _validate_intent(intent)

    parent = root.parent
    staging = Path(tempfile.mkdtemp(prefix=f".{root.name}.arcont-bootstrap-", dir=parent))
    try:
        for rel in (
            "assets/user",
            "incoming",
            "scenes",
            "scripts",
            "materials",
            "audio",
            "authoring/recipes",
            "authoring/scenarios",
            "tests",
            ".arcont/assets/user",
        ):
            (staging / rel).mkdir(parents=True, exist_ok=True)

        _write_text(staging / "project.godot", _project_godot(intent))
        _write_text(
            staging / "project.intent.json",
            json.dumps(intent, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        )
        _write_text(
            staging / "scenes/main.tscn",
            _scene_3d() if template == "godot-3d-minimal" else _scene_2d(),
        )
        _write_text(
            staging / "authoring/README.md",
            "# Authoring\n\nProject-owned recipes and scenarios live here. ARCONT remains external.\n",
        )

        tracked = [
            "project.godot",
            "project.intent.json",
            "scenes/main.tscn",
            "authoring/README.md",
        ]
        file_hashes = {rel: _sha256(staging / rel) for rel in tracked}
        receipt = {
            "protocol": "arcont-project-bootstrap",
            "version": 1,
            "template": template,
            "project_id": intent["project_id"],
            "engine": "Godot",
            "files": file_hashes,
            "network_access": False,
            "production_project_location": "external",
        }
        _write_text(
            staging / ".arcont/bootstrap.json",
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        )

        # The tree is fully materialized before replacing the caller-provided
        # empty directory, avoiding a half-written bootstrap on normal errors.
        if any(root.iterdir()):
            raise ValueError("bootstrap target changed while staging")
        root.rmdir()
        try:
            os.replace(staging, root)
        except Exception:
            root.mkdir(parents=True, exist_ok=True)
            raise

        return {
            "ok": True,
            "write_performed": True,
            "result": {
                **receipt,
                "project_root": str(root),
                "receipt": ".arcont/bootstrap.json",
                "intent": "project.intent.json",
                "main_scene": "scenes/main.tscn",
            },
        }
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def execute(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    if request.get("protocol_version") != PROTOCOL_VERSION:
        raise ValueError("request requires protocol_version=1")
    operation = request.get("operation")
    if operation not in OPERATIONS:
        raise ValueError(f"unsupported operation: {operation}")
    if operation == "capabilities":
        return {
            "ok": True,
            "write_performed": False,
            "operations": list(OPERATIONS),
            "templates": list(TEMPLATES),
            "requirements": ["existing empty external directory", "validated project intent"],
            "network_access": False,
        }
    if set(request) - {"protocol_version", "operation", "intent", "template"}:
        raise ValueError("bootstrap request has unsupported fields")
    return bootstrap(
        Path(project),
        request.get("intent"),
        request.get("template", "godot-3d-minimal"),
    )


def respond(project: Path, request: Any) -> dict[str, Any]:
    try:
        if not isinstance(request, dict):
            raise ValueError("request must be an object")
        return {"protocol_version": PROTOCOL_VERSION, **execute(project, request)}
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "ok": False,
            "write_performed": False,
            "error": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--request", default="-")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.request == "-" else Path(args.request).read_text(encoding="utf-8")
        result = respond(Path(args.project), json.loads(raw))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"protocol_version": 1, "ok": False, "write_performed": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
