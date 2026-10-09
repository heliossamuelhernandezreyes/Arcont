#!/usr/bin/env python3
"""Model Forge: reproducibly select glTF/GLB models and their external dependencies
from an ALREADY ACQUIRED, SHA-pinned, reviewed CC0 ZIP archive.

The game owns final assets; ARCONT owns this reusable, offline intake recipe.
No arbitrary downloads, automatic approvals, geometry mutations or physics edits.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

try:
    from tools.model_forge_materialize import gate
    from tools.model_forge_inspect import inspect
    from tools.production_assets import closure
except ModuleNotFoundError:
    from model_forge_materialize import gate
    from model_forge_inspect import inspect
    from production_assets import closure

MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 128 * 1024 * 1024
MAX_SELECTED_BYTES = 32 * 1024 * 1024
MAX_MEMBERS = 2048
MAX_SELECTED_MODELS = 64
MAX_FILE_BYTES = 16 * 1024 * 1024
SHA = re.compile(r"[a-f0-9]{64}", re.ASCII)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _name(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("unsafe or empty archive member name")
    part = PurePosixPath(value)
    if part.is_absolute() or any(x in (".", "..", "") for x in part.parts) or ":" in value:
        raise ValueError("unsafe path traversal or drive in archive")
    if part.as_posix() != value or value.endswith("/"):
        raise ValueError("noncanonical archive member")
    return value


def _json_model(data: bytes, extension: str) -> dict:
    if extension == ".gltf":
        doc = json.loads(data.decode("utf-8"))
    elif extension == ".glb":
        if len(data) < 20 or data[:4] != b"glTF":
            raise ValueError("not a GLB v2 model")
        version, length = struct.unpack_from("<II", data, 4)
        json_length, chunk_kind = struct.unpack_from("<II", data, 12)
        if version != 2 or length != len(data) or chunk_kind != 0x4E4F534A or json_length > len(data) - 20:
            raise ValueError("malformed GLB v2 header/JSON chunk")
        doc = json.loads(data[20:20 + json_length].decode("utf-8"))
    else:
        raise ValueError("only glTF 2.0 or GLB v2")
    if not isinstance(doc, dict) or doc.get("asset", {}).get("version") != "2.0":
        raise ValueError("invalid glTF asset version")
    return doc


def _dependencies(member: str, doc: dict) -> set[str]:
    result: set[str] = set()
    for entry in doc.get("buffers", []) + doc.get("images", []):
        if not isinstance(entry, dict):
            raise ValueError("malformed glTF dependency")
        uri = entry.get("uri")
        if uri is None or (isinstance(uri, str) and uri.startswith("data:")):
            continue
        if not isinstance(uri, str) or not uri or "%" in uri and re.search(r"%(?![0-9A-Fa-f]{2})", uri):
            raise ValueError("malformed external URI")
        parsed = urlsplit(uri)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or "\\" in uri:
            raise ValueError("remote/query-dependent glTF URIs are not allowed")
        rel = unquote(parsed.path)
        _name(rel)
        dep = (PurePosixPath(member).parent / rel).as_posix()
        result.add(_name(dep))
    return result


def stage_archive(archive: Path, *, record: dict, expected_sha256: str,
                  model_members: list[str], prefix: str, destination: Path) -> dict:
    """No existing destinations are overwritten; all files are hash-bound."""
    gate(record)  # canonical Asset Vault commercial, modification and CC0 trust policy
    if record.get("license", {}).get("name") not in ("CC0-1.0", "CC0"):
        raise ValueError("this automatic source-archive path currently requires explicit CC0")
    if not isinstance(expected_sha256, str) or not SHA.fullmatch(expected_sha256):
        raise ValueError("exact expected source SHA-256 is REQUIRED")
    if not isinstance(model_members, list) or not 1 <= len(model_members) <= MAX_SELECTED_MODELS:
        raise ValueError("select between 1 and 64 GLB/glTF models")
    _name(prefix + "/placeholder")
    if any(not isinstance(x, str) for x in model_members) or len(set(model_members)) != len(model_members):
        raise ValueError("model paths must be unique strings")
    for model in model_members:
        _name(model)
        if PurePosixPath(model).suffix.lower() not in {".glb", ".gltf"}:
            raise ValueError("unsupported model type")
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("source archive missing, symlink or too large")
    raw = archive.read_bytes()
    if _sha(raw) != expected_sha256:
        raise ValueError("source archive sha256 mismatch")
    if destination.exists() or destination.is_symlink():
        raise ValueError("refusing to overwrite existing bundle")
    if destination.parent.is_symlink():
        raise ValueError("destination parent cannot be a symlink")
    with zipfile.ZipFile(archive) as z:
        info_by_path = {}
        total = 0
        if len(z.infolist()) > MAX_MEMBERS:
            raise ValueError("archive member count exceeds limit")
        for info in z.infolist():
            if info.is_dir():
                continue
            path = _name(info.filename)
            if path in info_by_path or info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("duplicate, encrypted or symlink archive member")
            if info.file_size > MAX_FILE_BYTES:
                raise ValueError("oversized archive member")
            total += info.file_size
            if total > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("archive decompressed size exceeds bound")
            info_by_path[path] = info
        license_path = next((k for k in ("License.txt", "license.txt", "LICENSE.txt")
                             if k in info_by_path), None)
        if license_path is None:
            raise ValueError("original creator license file absent")
        license_bytes = z.read(license_path)
        if b"CC0" not in license_bytes and b"Creative Commons" not in license_bytes:
            raise ValueError("source license text does not identify CC0")
        originals = [prefix.rstrip("/") + "/" + x for x in model_members]
        chosen = set(originals)
        for original in originals:
            if original not in info_by_path:
                raise ValueError("model not found in source archive: " + original)
            doc = _json_model(z.read(original), PurePosixPath(original).suffix.lower())
            chosen.update(_dependencies(original, doc))
        if any(x not in info_by_path for x in chosen):
            raise ValueError("missing glTF external image/buffer dependency: " +
                             str(sorted(x for x in chosen if x not in info_by_path)))
        rel_files = {}
        for original in sorted(chosen):
            relative = PurePosixPath(original).relative_to(PurePosixPath(prefix.rstrip("/"))).as_posix()
            _name(relative)
            if relative in rel_files:
                raise ValueError("destination bundle collision")
            rel_files[relative] = z.read(original)
        if sum(len(b) for b in rel_files.values()) > MAX_SELECTED_BYTES:
            raise ValueError("selected production dependencies exceed byte budget")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".model-forge-", dir=destination.parent))
    try:
        for relative, data in rel_files.items():
            target = temp.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        assets = {}
        for rel in model_members:
            # This is the existing canonical inspector + full dependency resolver,
            # not a fragile Kenney-specific filename heuristic.
            references = closure(temp, rel)
            report = inspect(temp / rel)
            if report["meshes"] < 1 or report["triangles"] < 1:
                raise ValueError("empty GLB model: " + rel)
            assets[rel] = {"inspection": report, "dependencies": references}
        (temp / "SOURCE_LICENSE.txt").write_bytes(license_bytes)
        manifest = {
            "protocol": "arcont-model-forge-source-bundle", "version": 1,
            "asset_record_id": record["id"], "provider": record.get("source", {}).get("provider"),
            "license": "CC0-1.0", "original_archive_sha256": expected_sha256,
            "source_archive_member_prefix": prefix, "models": assets,
            "files": {p: {"sha256": _sha(data), "bytes": len(data)} for p, data in sorted(rel_files.items())},
            "creator_license_sha256": _sha(license_bytes),
            "delivery_status": "source-closure-and-geometry-validated",
            "godot_import_status": "not_tested", "android_runtime_status": "needs_measurement",
            "limits": ["Does not certify Godot import, rendering quality, collision or Android FPS"],
        }
        (temp / "PROVENANCE.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        if destination.exists():
            raise ValueError("concurrent destination already exists")
        os.rename(temp, destination)
        return manifest
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--record", type=Path, required=True, help="reviewed Asset Vault record")
    p.add_argument("--expected-sha256", required=True)
    p.add_argument("--prefix", required=True, help="archive root holding selected model paths")
    p.add_argument("--model", action="append", required=True, help="repeat for selected model")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    try:
        record = json.loads(a.record.read_text(encoding="utf-8"))
        result = stage_archive(a.archive, record=record, expected_sha256=a.expected_sha256,
                               model_members=a.model, prefix=a.prefix, destination=a.out)
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "write_performed": False}))
        return 1
    print(json.dumps({"ok": True, "result": result}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
