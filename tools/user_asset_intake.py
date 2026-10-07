#!/usr/bin/env python3
"""Bounded intake for user-provided assets inside an external game project.

V1 accepts individual local files placed below project/incoming. It never
downloads from the network, extracts archives, executes asset contents or
infers legal rights. Staging requires an explicit user rights declaration and
writes a provenance record alongside the project.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path, PurePosixPath
from typing import Any

PROTOCOL_VERSION = 1
OPERATIONS = ("capabilities", "inspect", "stage", "list")
ASSET_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
MAX_FILE_BYTES = 512 * 1024 * 1024
ALLOWED = {
    ".png": "texture", ".jpg": "texture", ".jpeg": "texture", ".webp": "texture", ".svg": "vector",
    ".glb": "model3d", ".gltf": "model3d", ".fbx": "model3d", ".obj": "model3d", ".dae": "model3d",
    ".wav": "audio", ".ogg": "audio", ".mp3": "audio", ".flac": "audio", ".opus": "audio",
    ".ttf": "font", ".otf": "font",
}
DESTINATIONS = {
    "texture": "assets/user/textures",
    "vector": "assets/user/textures",
    "model3d": "assets/user/models",
    "audio": "assets/user/audio",
    "font": "assets/user/fonts",
}
RIGHTS_BASES = {"user-owned", "licensed", "public-domain"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("project-relative source path required")
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value or ".." in pure.parts or "\\" in value:
        raise ValueError("safe project-relative source path required")
    return Path(*pure.parts)


def _source(project: Path, value: Any) -> Path:
    rel = _relative(value)
    if not rel.parts or rel.parts[0] != "incoming":
        raise ValueError("user asset source must be below project/incoming")
    path = (project / rel).resolve()
    if path == project or project not in path.parents:
        raise ValueError("asset source escapes project")
    current = path
    while current != project:
        if current.is_symlink():
            raise ValueError("symlink asset paths are not accepted")
        current = current.parent
    if not path.is_file():
        raise ValueError("user asset source file does not exist")
    return path


def _inspect(project: Path, source: Any) -> dict[str, Any]:
    path = _source(project, source)
    extension = path.suffix.lower()
    kind = ALLOWED.get(extension)
    if kind is None:
        raise ValueError(f"unsupported user asset extension: {extension or '<none>'}")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ValueError("user asset exceeds v1 size limit")
    return {
        "source": path.relative_to(project).as_posix(),
        "filename": path.name,
        "extension": extension,
        "kind": kind,
        "bytes": size,
        "sha256": _sha256(path),
        "rights_inferred": False,
    }


def _validated_rights(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("stage requires rights declaration")
    allowed = {"basis", "commercial_use", "redistribution", "license_name", "attribution", "notes"}
    if set(value) - allowed:
        raise ValueError("rights declaration has unsupported fields")
    basis = value.get("basis")
    if basis not in RIGHTS_BASES:
        raise ValueError(f"rights.basis must be one of {sorted(RIGHTS_BASES)}")
    for key in ("commercial_use", "redistribution"):
        if not isinstance(value.get(key), bool):
            raise ValueError(f"rights.{key} must be boolean")
    for key, limit in (("license_name", 200), ("attribution", 1000), ("notes", 2000)):
        if key in value and value[key] is not None and (not isinstance(value[key], str) or len(value[key]) > limit):
            raise ValueError(f"rights.{key} must be null or a bounded string")
    if basis == "licensed" and not isinstance(value.get("license_name"), str):
        raise ValueError("licensed assets require rights.license_name")
    return dict(value)


def _project_policy(project: Path) -> dict[str, Any]:
    path = project / "project.intent.json"
    if not path.is_file():
        raise ValueError("project.intent.json is required before asset staging")
    try:
        from tools.arcont_bridge import validate_intent
    except ModuleNotFoundError:
        from arcont_bridge import validate_intent
    intent = validate_intent(json.loads(path.read_text(encoding="utf-8")))
    policy = intent.get("asset_policy", {})
    if policy.get("user_assets") is not True:
        raise ValueError("project intent does not allow user assets")
    return policy


def _record_dir(project: Path) -> Path:
    return project / ".arcont/assets/user"


def list_records(project: Path) -> dict[str, Any]:
    base = _record_dir(project)
    records = []
    if base.is_dir():
        for path in sorted(base.glob("*.asset.json")):
            if path.is_symlink():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                records.append(data)
    return {"ok": True, "write_performed": False, "result": {"assets": records, "count": len(records)}}


def stage(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    policy = _project_policy(project)
    asset_id = request.get("asset_id")
    if not isinstance(asset_id, str) or not ASSET_ID.fullmatch(asset_id):
        raise ValueError("stage requires safe asset_id")
    inspection = _inspect(project, request.get("source"))
    rights = _validated_rights(request.get("rights"))
    if policy.get("commercial_use_required") is True and rights["commercial_use"] is not True:
        raise ValueError("project requires assets declared for commercial use")
    allowed_licenses = policy.get("allowed_licenses")
    if rights["basis"] == "licensed" and isinstance(allowed_licenses, list) and allowed_licenses:
        if rights.get("license_name") not in allowed_licenses:
            raise ValueError("declared asset license is not in project allowed_licenses")
    forbidden = policy.get("forbidden_licenses")
    if rights.get("license_name") and isinstance(forbidden, list) and rights["license_name"] in forbidden:
        raise ValueError("declared asset license is forbidden by project intent")

    source = project / inspection["source"]
    destination_dir = project / DESTINATIONS[inspection["kind"]] / asset_id
    record_path = _record_dir(project) / f"{asset_id}.asset.json"
    if destination_dir.exists() or record_path.exists():
        raise ValueError("asset_id is already staged")

    destination_dir.mkdir(parents=True, exist_ok=False)
    try:
        target = destination_dir / source.name
        shutil.copy2(source, target)
        staged_sha = _sha256(target)
        if staged_sha != inspection["sha256"]:
            raise ValueError("staged asset hash mismatch")
        record = {
            "protocol": "arcont-user-asset",
            "version": 1,
            "id": asset_id,
            "origin": "user-provided",
            "source": inspection["source"],
            "staged_path": target.relative_to(project).as_posix(),
            "kind": inspection["kind"],
            "extension": inspection["extension"],
            "bytes": inspection["bytes"],
            "sha256": staged_sha,
            "rights": rights,
            "rights_status": "user-declared-not-verified-by-arcont",
            "network_access": False,
        }
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        shutil.rmtree(destination_dir, ignore_errors=True)
        if record_path.exists():
            record_path.unlink()
        raise

    return {
        "ok": True,
        "write_performed": True,
        "result": record,
    }


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
            "mutating_operations": ["stage"],
            "source_root": "incoming/",
            "allowed_extensions": sorted(ALLOWED),
            "max_file_bytes": MAX_FILE_BYTES,
            "network_access": False,
            "archive_extraction": False,
        }
    if operation == "inspect":
        return {"ok": True, "write_performed": False, "result": _inspect(root, request.get("source"))}
    if operation == "list":
        return list_records(root)
    if operation == "stage":
        return stage(root, request)
    raise AssertionError("unreachable")


def respond(project: Path, request: Any) -> dict[str, Any]:
    try:
        if not isinstance(request, dict):
            raise ValueError("request must be an object")
        return {"protocol_version": PROTOCOL_VERSION, **execute(project, request)}
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
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
        result = {"protocol_version": 1, "ok": False, "write_performed": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
