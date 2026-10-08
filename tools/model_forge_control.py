#!/usr/bin/env python3
"""Bounded local Model Forge control for external game projects.

No network downloads or arbitrary processor execution are exposed here. The
control plane can inspect, budget-check, derive collision policy, and stage a
local glTF/GLB candidate into an external project with explicit provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from tools.model_forge_inspect import inspect as inspect_model
    from tools.production_assets import closure
    from tools.project_lock import document_lock
except ModuleNotFoundError:
    from model_forge_inspect import inspect as inspect_model
    from production_assets import closure
    from project_lock import document_lock

PROTOCOL_VERSION = 1
OPERATIONS = ("capabilities", "inspect", "validate", "collision.recipe", "stage")
SEMANTIC_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def _relative(value: Any) -> Path:
    if not isinstance(value, str):
        raise ValueError("project-relative path required")
    pure = PurePosixPath(value)
    if not value or pure.is_absolute() or pure.as_posix() != value or ".." in pure.parts or "\\" in value:
        raise ValueError("safe project-relative path required")
    return Path(*pure.parts)


def _contained(project: Path, relative: Any, must_exist: bool = False) -> Path:
    lexical = project / _relative(relative)
    if any(parent.is_symlink() for parent in [lexical, *lexical.parents] if parent == project or project in parent.parents):
        raise ValueError("symlink paths are not accepted")
    path = lexical.resolve()
    if path == project or project not in path.parents:
        raise ValueError("path escapes external project")
    if any(parent.is_symlink() for parent in [path, *path.parents] if parent == project or project in parent.parents):
        raise ValueError("symlink paths are not accepted")
    if must_exist and not path.is_file():
        raise ValueError("model file does not exist")
    return path


def _profile(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("budgets"), dict):
        raise ValueError("inline profile with budgets required")
    budgets = value["budgets"]
    for key in ("triangles_max", "materials_max"):
        number = budgets.get(key)
        if isinstance(number, bool) or not isinstance(number, int) or number < 0:
            raise ValueError(f"invalid budget: {key}")
    return value


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def execute(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    if request.get("protocol_version") != PROTOCOL_VERSION:
        raise ValueError("request requires protocol_version=1")
    operation = request.get("operation")
    if operation not in OPERATIONS:
        raise ValueError(f"unsupported operation: {operation}")
    root = Path(project).resolve()
    if not root.is_dir():
        raise ValueError("external project root must exist")

    if operation == "capabilities":
        return {
            "ok": True,
            "write_performed": False,
            "operations": list(OPERATIONS),
            "network_access": False,
            "mutating_operations": ["stage"],
            "delivery_modes": ["candidate", "validated"],
            "validated_delivery_requires": ["profile", "pinned Khronos glTF Validator", "complete dependency closure"],
        }

    model_rel = request.get("model")
    model = _contained(root, model_rel, must_exist=True)
    if model.suffix.lower() not in {".glb", ".gltf"}:
        raise ValueError("Model Forge control accepts glTF/GLB only")

    report = inspect_model(model)
    if operation == "inspect":
        return {"ok": True, "write_performed": False, "result": report}

    if operation == "validate":
        profile = _profile(request.get("profile"))
        budgets = profile["budgets"]
        errors = []
        if report.get("triangles", 0) > budgets["triangles_max"]:
            errors.append(f"triangles {report['triangles']} > {budgets['triangles_max']}")
        if report.get("materials", 0) > budgets["materials_max"]:
            errors.append(f"materials {report['materials']} > {budgets['materials_max']}")
        if report.get("gltf_version") != "2.0":
            errors.append("not glTF 2.0")
        return {
            "ok": True,
            "write_performed": False,
            "result": {"profile": profile.get("id"), "technical_passed": not errors, "errors": errors, "inspection": report},
        }

    if operation == "collision.recipe":
        mode = request.get("mode", "box")
        if mode not in {"box", "convex", "manual"}:
            raise ValueError("unsupported collision mode")
        return {
            "ok": True,
            "write_performed": False,
            "result": {
                "version": 1,
                "render_asset": model_rel,
                "mode": mode,
                "principle": "collision represents gameplay, not render detail",
                "game_validation_required": True,
            },
        }

    semantic_id = request.get("semantic_id")
    if not isinstance(semantic_id, str) or not SEMANTIC_ID.fullmatch(semantic_id):
        raise ValueError("stage requires safe semantic_id")
    delivery_mode = request.get("delivery_mode", "candidate")
    if delivery_mode not in {"candidate", "validated"}:
        raise ValueError("delivery_mode must be candidate or validated")
    if delivery_mode == "validated":
        budgets = _profile(request.get("profile"))["budgets"]
        if any(report[key] > budgets[key + "_max"] for key in ("triangles", "materials")):
            raise ValueError("asset exceeds validated delivery profile")
    destination = request.get("destination")
    base = _contained(root, destination, must_exist=False)
    target = base.joinpath(*semantic_id.split("."))
    if target.exists():
        raise ValueError("staging destination already exists")
    dependencies = closure(root, model_rel)
    digests = {rel: _sha256(_contained(root, rel, True)) for rel in dependencies}
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".candidate-", dir=target.parent))
    try:
        files = {}
        for rel in dependencies:
            source = _contained(root, rel, True)
            bundled = "asset" + model.suffix.lower() if rel == model_rel else source.relative_to(model.parent).as_posix()
            if bundled in {"asset.manifest.json", "asset" + model.suffix.lower()} and rel != model_rel:
                raise ValueError("dependency collides with reserved bundle filename")
            dest = temporary / bundled
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
            if _sha256(dest) != digests[rel] or _sha256(source) != digests[rel]:
                raise ValueError("source changed during staging")
            files[bundled] = {"source": rel, "sha256": digests[rel], "size_bytes": dest.stat().st_size}
        asset_name = "asset" + model.suffix.lower()
        # Re-resolve the complete bundle before publication; the source tree is
        # irrelevant to this check and can no longer mask missing dependencies.
        closure(temporary, asset_name)
        staged_report = inspect_model(temporary / asset_name)
        staged_report["path"] = asset_name
        specification = None
        if delivery_mode == "validated":
            try:
                from tools.model_forge_spec_validate import validate_spec
            except ModuleNotFoundError:
                from model_forge_spec_validate import validate_spec
            specification = validate_spec(temporary / asset_name)
            if not specification["ok"]:
                raise ValueError("Khronos glTF specification validation failed")
            if any(staged_report[key] > budgets[key + "_max"] for key in ("triangles", "materials")):
                raise ValueError("staged asset exceeds validated delivery profile")
        manifest = {
            "version": 2, "semantic_id": semantic_id, "file": asset_name,
            "sha256": digests[model_rel], "source": str(_relative(model_rel)),
            "inspection": staged_report, "files": files,
            "delivery_status": "spec-and-budget-validated" if specification else "candidate",
            "spec_validation": specification or "not-certified",
            "profile": request.get("profile") if specification else None,
            "runtime_evidence_required": True,
        }
        (temporary / "asset.manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        with document_lock(root, target.relative_to(root).as_posix()):
            _contained(root, target.relative_to(root).as_posix())
            if target.exists():
                raise ValueError("staging destination already exists")
            os.rename(temporary, target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {
        "ok": True,
        "write_performed": True,
        "result": {
            **manifest,
            "bundle_directory": target.relative_to(root).as_posix(),
        },
    }


def respond(project: Path, request: Any) -> dict[str, Any]:
    try:
        if not isinstance(request, dict):
            raise ValueError("request must be an object")
        return {"protocol_version": PROTOCOL_VERSION, **execute(project, request)}
    except (ValueError, OSError, TypeError, KeyError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"protocol_version": PROTOCOL_VERSION, "ok": False, "write_performed": False, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--request", default="-")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.request == "-" else Path(args.request).read_text(encoding="utf-8")
        result = respond(Path(args.project), json.loads(raw))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"protocol_version": PROTOCOL_VERSION, "ok": False, "write_performed": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
