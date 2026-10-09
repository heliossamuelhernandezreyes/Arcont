#!/usr/bin/env python3
"""ARCONT visual-production contract gate (P0): no writes, no engine, no network.

JSON Schema 2020-12 validates the portable shape. Explicit cross-reference and
project-local checks prevent silent orphan zones, fake staged assets, bad hashes,
path escapes, unsupported renderer assumptions and measurement overclaims.
Runtime scene content and artistic quality are deliberately out of scope.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = Path(__file__).resolve().parents[1] / "schemas/proposals/visual-production-intent.schema.json"
SUPPORTED_RENDERERS = {"Godot": {"gl_compatibility", "gl_compatibility_mobile", "gl_compatibility_windows", "mobile", "gl_compatibility_linux", "gl_compatibility_android", "forward_plus"}, "Unity": set(), "Other": set()}
LAYER_NAMES = {"gameplay-semantic", "structure", "functional-props", "dressing", "signage", "atmosphere"}


def _safe_path(root: Path, relative: str) -> Path:
    # Resolve symlinks and verify containment. A lexical path check alone fails
    # when e.g. assets/safe is a symlink to /tmp/outside.
    child = (root / relative).resolve()
    if not child.is_relative_to(root.resolve()) or not relative or relative.startswith("/"):
        raise ValueError(f"path escapes project root: {relative!r}")
    return child


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _unique(records: list[dict[str, Any]], name: str, errors: list[str]) -> set[str]:
    found: set[str] = set()
    for entry in records:
        key = entry["id"]
        if key in found:
            errors.append(f"{name}: duplicate id {key!r}")
        found.add(key)
    return found


def validate_intent(intent: dict[str, Any], project_root: Path | None = None,
                    schema_path: Path = SCHEMA) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        return ["jsonschema>=4 is required; install jsonschema==4.25.1"], []
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    for fault in sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(intent),
                        key=lambda e: (list(map(str, e.absolute_path)), e.message)):
        where = ".".join(map(str, fault.absolute_path)) or "$"
        errors.append(f"schema {where}: {fault.message}")
    if errors:
        return errors, warnings

    light_ids = _unique(intent["lighting_profiles"], "lighting_profiles", errors)
    zone_ids = _unique(intent["zones"], "zones", errors)
    _unique(intent["asset_roles"], "asset_roles", errors)
    _unique(intent["capture_plan"], "capture_plan", errors)
    layers = [x["kind"] for x in intent["layers"]]
    if len(layers) != len(set(layers)):
        errors.append("layers: duplicate kind")
    if "gameplay-semantic" not in layers:
        errors.append("layers: gameplay-semantic ownership layer is required")
    if set(layers) - LAYER_NAMES:
        errors.append("layers: invalid kind")
    palette = intent["visual_kit"]["palette"]
    _unique(palette, "visual_kit.palette", errors)

    engine = intent["render_profile"]["engine"]
    renderer = intent["render_profile"]["renderer"]
    if engine == "Godot" and renderer not in SUPPORTED_RENDERERS["Godot"]:
        errors.append(f"render_profile: unsupported/unrecognized Godot renderer {renderer!r}")
    if engine != "Godot":
        warnings.append("renderer capabilities for this engine have not been audited")
    if engine == "Godot" and renderer == "gl_compatibility" and intent["render_profile"]["target_platform"] == "Android":
        warnings.append("Godot Compatibility: do not assume Forward+ GI, SSAO or volumetric fog")
    if intent["budgets"]["fallback_fps"] > intent["budgets"]["target_fps"]:
        errors.append("budgets: fallback_fps must be <= target_fps")
    if intent["budgets"]["measurement_status"] == "measured":
        errors.append("budgets: 'measured' requires external, hashed runtime trace evidence; this design contract alone cannot claim it")

    for zone in intent["zones"]:
        if zone["lighting_profile_id"] not in light_ids:
            errors.append(f"zones.{zone['id']}: missing lighting profile {zone['lighting_profile_id']!r}")
    for shot in intent["capture_plan"]:
        if shot["zone_id"] not in zone_ids:
            errors.append(f"capture_plan.{shot['id']}: missing zone {shot['zone_id']!r}")
        if shot["renderer"] != renderer:
            errors.append(f"capture_plan.{shot['id']}: renderer mismatch")
        if shot["roi"]["x"] + shot["roi"]["width"] > 1.00000001 or shot["roi"]["y"] + shot["roi"]["height"] > 1.00000001:
            errors.append(f"capture_plan.{shot['id']}: roi falls outside viewport")
        if shot["baseline_sha256"] is None or shot["candidate_sha256"] is None:
            warnings.append(f"capture_plan.{shot['id']}: comparison not yet possible (missing hashed frames)")
        if any(not math.isfinite(val) for axis in ("camera_position", "camera_target") for val in shot[axis]):
            errors.append(f"capture_plan.{shot['id']}: nonfinite camera coordinate")

    if project_root is None:
        warnings.append("semantic map, region ids, and asset bytes not cross-checked (no --project-root)")
        for asset in intent["asset_roles"]:
            if asset["status"] in ("staged", "approved"):
                errors.append(f"asset_roles.{asset['id']}: staged/approved asset requires --project-root for provenance check")
        return errors, warnings

    root = project_root.resolve()
    if not root.is_dir():
        errors.append(f"project root is not a directory: {root}")
        return errors, warnings
    map_info = intent["semantic_map"]
    try:
        map_path = _safe_path(root, map_info["path"])
        if not map_path.is_file():
            errors.append(f"semantic map missing: {map_info['path']}")
        else:
            if map_info["sha256"] is not None and _digest(map_path) != map_info["sha256"]:
                errors.append("semantic_map: SHA-256 does not match game-owned map")
            map_data = json.loads(map_path.read_text(encoding="utf-8"))
            region_ids = {r["id"] for r in map_data.get("regions", []) if isinstance(r, dict) and isinstance(r.get("id"), str)}
            for zone in intent["zones"]:
                if zone["region_id"] is not None and zone["region_id"] not in region_ids:
                    errors.append(f"zones.{zone['id']}: unknown semantic region {zone['region_id']!r}")
            if map_info["sha256"] is None:
                warnings.append("semantic_map: no pinned SHA-256; reproducibility not established")
    except (OSError, ValueError, json.JSONDecodeError, TypeError) as exc:
        errors.append(f"semantic_map: {exc}")

    for asset in intent["asset_roles"]:
        status = asset["status"]
        if status not in ("staged", "approved"):
            continue
        record = asset["source_record"]
        try:
            asset_record_path = _safe_path(root, record)
            if not asset_record_path.is_file():
                raise ValueError("provenance record not found")
            receipt = json.loads(asset_record_path.read_text(encoding="utf-8"))
            if receipt.get("sha256") != asset["sha256"]:
                raise ValueError("asset hash differs from provenance record")
            license_name = receipt.get("asset_license", receipt.get("license"))
            if license_name not in ("CC0", "CC0-1.0"):
                raise ValueError("asset license not verified as CC0")
            staged = receipt.get("staged_path")
            if not isinstance(staged, str):
                raise ValueError("provenance has no staged_path")
            staged_file = _safe_path(root, staged)
            if not staged_file.is_file() or _digest(staged_file) != asset["sha256"]:
                raise ValueError("staged asset bytes do not match sha256")
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"asset_roles.{asset['id']}: {exc}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("intent", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args()
    try:
        payload = json.loads(args.intent.read_text(encoding="utf-8"))
        errors, warnings = validate_intent(payload, args.project_root)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        errors, warnings = [str(exc)], []
    result = {"ok": not errors, "protocol": "arcont-visual-intent-validation",
              "schema_version": 1, "errors": errors, "warnings": warnings,
              "writes_performed": False, "runtime_measured": False}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for warning in warnings:
            print("VISUAL INTENT WARN", warning)
        for error in errors:
            print("VISUAL INTENT FAIL", error)
        if not errors:
            print("VISUAL INTENT PASS (structure and references only; no visual quality approval)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
