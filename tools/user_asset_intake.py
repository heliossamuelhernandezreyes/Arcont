#!/usr/bin/env python3
"""Bounded intake for user-provided assets inside an external game project.

V1 accepts individual local files placed below project/incoming. It never
downloads from the network, extracts archives, executes asset contents or
infers legal rights. Staging requires an explicit user rights declaration and
writes a bounded provenance record alongside the project.
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
MAX_RECORD_BYTES = 1024 * 1024
MAX_RECORDS = 2000
ALLOWED = {
    ".png": "texture", ".jpg": "texture", ".jpeg": "texture", ".webp": "texture", ".svg": "vector",
    ".glb": "model3d",
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


def _relative(value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("project-relative source path required")
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value or ".." in pure.parts or chr(92) in value:
        raise ValueError("safe project-relative source path required")
    return Path(*pure.parts)


def _reject_symlink_ancestors(project: Path, path: Path) -> None:
    project = project.resolve()
    lexical = path if path.is_absolute() else project / path
    try:
        rel = lexical.relative_to(project)
    except ValueError as exc:
        raise ValueError("path escapes external project") from exc
    current = project
    for part in rel.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError("symlink paths are not accepted")


def _safe_destination(project: Path, relative: str) -> Path:
    root = project.resolve()
    rel = _relative(relative)
    lexical = root / rel
    _reject_symlink_ancestors(root, lexical)
    parent = lexical.parent.resolve()
    if parent != root and root not in parent.parents:
        raise ValueError("destination escapes external project")
    return lexical


def _source(project: Path, value: Any) -> Path:
    root = project.resolve()
    rel = _relative(value)
    if not rel.parts or rel.parts[0] != "incoming":
        raise ValueError("user asset source must be below project/incoming")
    lexical = root / rel
    _reject_symlink_ancestors(root, lexical)
    path = lexical.resolve()
    if path == root or root not in path.parents:
        raise ValueError("asset source escapes project")
    if not path.is_file():
        raise ValueError("user asset source file does not exist")
    return path


def _hash_and_size(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            total += len(chunk)
            if total > MAX_FILE_BYTES:
                raise ValueError("user asset exceeds v1 size limit")
            digest.update(chunk)
    return digest.hexdigest(), total


def _inspect(project: Path, source: Any) -> dict[str, Any]:
    path = _source(project, source)
    extension = path.suffix.lower()
    kind = ALLOWED.get(extension)
    if kind is None:
        raise ValueError(f"unsupported user asset extension: {extension or '<none>'}")
    sha256, size = _hash_and_size(path)
    return {
        "source": path.relative_to(project.resolve()).as_posix(),
        "filename": path.name,
        "extension": extension,
        "kind": kind,
        "bytes": size,
        "sha256": sha256,
        "rights_inferred": False,
        "dependency_policy": "single-file-self-contained",
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
    if basis == "licensed":
        license_name = value.get("license_name")
        if not isinstance(license_name, str) or not license_name.strip():
            raise ValueError("licensed assets require a non-empty rights.license_name")
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
    return _safe_destination(project, ".arcont/assets/user")


def list_records(project: Path) -> dict[str, Any]:
    root = project.resolve()
    base = _record_dir(root)
    records = []
    if not base.exists():
        return {"ok": True, "write_performed": False, "result": {"assets": [], "count": 0}}
    _reject_symlink_ancestors(root, base)
    if not base.is_dir():
        raise ValueError("user asset provenance path is not a directory")
    paths = sorted(base.glob("*.asset.json"))
    if len(paths) > MAX_RECORDS:
        raise ValueError("user asset provenance record count exceeds v1 limit")
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"invalid user asset provenance entry: {path.name}")
        size = path.stat().st_size
        if size > MAX_RECORD_BYTES:
            raise ValueError(f"user asset provenance record exceeds size limit: {path.name}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid user asset provenance record: {path.name}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"user asset provenance record must be an object: {path.name}")
        records.append(data)
    return {"ok": True, "write_performed": False, "result": {"assets": records, "count": len(records)}}


def stage(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    root = project.resolve()
    policy = _project_policy(root)
    asset_id = request.get("asset_id")
    if not isinstance(asset_id, str) or not ASSET_ID.fullmatch(asset_id):
        raise ValueError("stage requires safe asset_id")
    inspection = _inspect(root, request.get("source"))
    rights = _validated_rights(request.get("rights"))
    if policy.get("commercial_use_required") is True and rights["commercial_use"] is not True:
        raise ValueError("project requires assets declared for commercial use")
    allowed_licenses = policy.get("allowed_licenses")
    if rights["basis"] == "licensed" and isinstance(allowed_licenses, list):
        if rights.get("license_name") not in allowed_licenses:
            raise ValueError("declared asset license is not in project allowed_licenses")
    forbidden = policy.get("forbidden_licenses")
    if rights.get("license_name") and isinstance(forbidden, list) and rights["license_name"] in forbidden:
        raise ValueError("declared asset license is forbidden by project intent")

    source = _source(root, inspection["source"])
    destination_dir = _safe_destination(root, f"{DESTINATIONS[inspection['kind']]}/{asset_id}")
    record_path = _safe_destination(root, f".arcont/assets/user/{asset_id}.asset.json")
    if destination_dir.exists() or record_path.exists():
        raise ValueError("asset_id is already staged")

    _reject_symlink_ancestors(root, destination_dir)
    _reject_symlink_ancestors(root, record_path)
    destination_dir.mkdir(parents=True, exist_ok=False)
    try:
        target = destination_dir / source.name
        shutil.copy2(source, target)
        staged_sha, staged_size = _hash_and_size(target)
        if staged_sha != inspection["sha256"] or staged_size != inspection["bytes"]:
            raise ValueError("staged asset differs from inspected source")
        # Re-read the source after copy to fail closed if it changed while staging.
        source_sha, source_size = _hash_and_size(source)
        if source_sha != inspection["sha256"] or source_size != inspection["bytes"]:
            raise ValueError("source asset changed during staging")
        record = {
            "protocol": "arcont-user-asset",
            "version": 1,
            "id": asset_id,
            "origin": "user-provided",
            "source": inspection["source"],
            "staged_path": target.relative_to(root).as_posix(),
            "kind": inspection["kind"],
            "extension": inspection["extension"],
            "bytes": staged_size,
            "sha256": staged_sha,
            "rights": rights,
            "rights_status": "user-declared-not-verified-by-arcont",
            "network_access": False,
        }
        record_path.parent.mkdir(parents=True, exist_ok=True)
        _reject_symlink_ancestors(root, record_path.parent)
        record_path.write_text(
            json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + chr(10),
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(destination_dir, ignore_errors=True)
        if record_path.exists() and not record_path.is_symlink():
            record_path.unlink()
        raise

    return {"ok": True, "write_performed": True, "result": record}


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
            "model_formats": [".glb"],
            "dependency_policy": "single-file-self-contained",
            "max_file_bytes": MAX_FILE_BYTES,
            "max_record_bytes": MAX_RECORD_BYTES,
            "max_records": MAX_RECORDS,
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
