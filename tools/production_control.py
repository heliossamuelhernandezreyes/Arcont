#!/usr/bin/env python3
"""Unified ARCONT production-preparation control for external game projects.

This wrapper composes the reusable production validators already present in
ARCONT behind one versioned JSON request surface. Production game code remains
in the external project. Mutating operations are explicit in the response.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from tools.production_assets import stage, validate_plan
    from tools.production_audio import validate as validate_audio
    from tools.production_bundle import materialize
    from tools.production_evidence import compare, summarize
    from tools.production_finish import review as review_finish
    from tools.production_recipes import animation_profile, sector
except ModuleNotFoundError:
    from production_assets import stage, validate_plan
    from production_audio import validate as validate_audio
    from production_bundle import materialize
    from production_evidence import compare, summarize
    from production_finish import review as review_finish
    from production_recipes import animation_profile, sector

PROTOCOL_VERSION = 1
OPERATIONS = (
    "capabilities",
    "assets.validate",
    "assets.stage",
    "animation.validate",
    "sector.validate",
    "performance.summarize",
    "performance.compare",
    "finish.review",
    "audio.review",
    "bundle.materialize",
)


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} requires an object")
    return value


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
            "mutating_operations": ["assets.stage", "bundle.materialize"],
            "limits": [
                "Technical validation does not establish AAA art quality.",
                "Rendered/device acceptance remains project-owned evidence.",
            ],
        }

    if operation == "assets.validate":
        result = validate_plan(root, _object(request.get("plan"), "plan"))
        return {"ok": True, "write_performed": False, "result": result}

    if operation == "assets.stage":
        destination = request.get("destination")
        if not isinstance(destination, str) or not destination:
            raise ValueError("assets.stage requires destination")
        result = stage(root, _object(request.get("plan"), "plan"), destination)
        return {"ok": True, "write_performed": True, "result": result}

    if operation == "animation.validate":
        profile = _object(request.get("profile"), "profile")
        animation_profile(profile)
        return {
            "ok": True,
            "write_performed": False,
            "result": {
                "clips": len(profile["clips"]),
                "mapped_bones": len(profile["bone_map"]),
                "scope": "profile contract; native adapter acceptance still required",
            },
        }

    if operation == "sector.validate":
        result = sector(_object(request.get("recipe"), "recipe"))
        return {"ok": True, "write_performed": False, "result": result}

    if operation == "performance.summarize":
        result = summarize(_object(request.get("record"), "record"))
        return {"ok": True, "write_performed": False, "result": result}

    if operation == "performance.compare":
        before = _object(request.get("before"), "before")
        after = _object(request.get("after"), "after")
        return {"ok": True, "write_performed": False, "result": compare(before, after)}

    if operation == "finish.review":
        profile = request.get("profile")
        if profile is None:
            profile_path = Path(__file__).resolve().parents[1] / "templates" / "production" / "tps-mobile-finish.profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
        result = review_finish(_object(profile, "profile"), _object(request.get("record"), "record"))
        return {"ok": True, "write_performed": False, "result": result}

    if operation == "audio.review":
        directory = request.get("directory")
        if not isinstance(directory, str) or not directory:
            raise ValueError("audio.review requires project-relative directory")
        result = validate_audio(root, _object(request.get("record"), "record"), directory)
        return {"ok": True, "write_performed": False, "result": result}

    source = request.get("source")
    destination = request.get("destination")
    files = _object(request.get("files"), "files")
    replace = request.get("replace", False)
    if not isinstance(source, str) or not isinstance(destination, str) or not isinstance(replace, bool):
        raise ValueError("bundle.materialize requires source/destination strings and boolean replace")
    result = materialize(root, source, destination, files, replace)
    return {"ok": True, "write_performed": True, "result": result}


def respond(project: Path, request: Any) -> dict[str, Any]:
    try:
        if not isinstance(request, dict):
            raise ValueError("request must be an object")
        return {"protocol_version": PROTOCOL_VERSION, **execute(project, request)}
    except (ValueError, KeyError, OSError, TypeError) as exc:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "ok": False,
            "write_performed": False,
            "error": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--request", default="-", help="request JSON path, or - for stdin")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.request == "-" else Path(args.request).read_text(encoding="utf-8")
        request = json.loads(raw)
        result = respond(Path(args.project), request)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"protocol_version": PROTOCOL_VERSION, "ok": False, "write_performed": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
