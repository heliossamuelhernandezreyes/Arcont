#!/usr/bin/env python3
"""Machine-readable control plane for ARCONT.

The control plane is intentionally read-only. It discovers whitelisted ARCONT
capabilities, runs bounded diagnostics, and inspects external game repositories
without writing to them or embedding production game code in ARCONT.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

REGISTRY_FILENAME = "agent.capabilities.json"
MANIFEST_FILENAME = "arcont.manifest.json"
PROTOCOL = "arcont-agent-control"
MAX_STDIO_CHARS = 12000
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_FILES = 50000

SOURCE_EXTENSIONS = {
    ".gd", ".gdshader", ".cs", ".cpp", ".c", ".h", ".hpp", ".py", ".lua", ".js", ".ts", ".tsx", ".jsx"
}
ASSET_2D_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".bmp", ".tga"}
ASSET_3D_EXTENSIONS = {".glb", ".gltf", ".fbx", ".obj", ".dae", ".blend"}
AUDIO_EXTENSIONS = {".wav", ".ogg", ".mp3", ".flac", ".opus"}
SCENE_EXTENSIONS = {".tscn", ".scn"}
RESOURCE_EXTENSIONS = {".tres", ".res"}
IGNORED_DIRS = {".git", ".godot", "node_modules", "__pycache__", ".cache", ".arcont"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def load_registry(root: Path) -> dict[str, Any]:
    path = root / REGISTRY_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"missing capability registry: {path}")
    registry = _load_json(path)
    if registry.get("schema_version") != 1 or registry.get("protocol") != PROTOCOL:
        raise ValueError("unsupported ARCONT agent capability registry")
    capabilities = registry.get("capabilities")
    if not isinstance(capabilities, list):
        raise ValueError("registry.capabilities must be an array")
    ids: set[str] = set()
    for item in capabilities:
        if not isinstance(item, dict):
            raise ValueError("every capability must be an object")
        cap_id = item.get("id")
        if not isinstance(cap_id, str) or not cap_id:
            raise ValueError("every capability requires a non-empty id")
        if cap_id in ids:
            raise ValueError(f"duplicate capability id: {cap_id}")
        ids.add(cap_id)
        if item.get("access") not in {"read-only", "external-runtime"}:
            raise ValueError(f"unsupported capability access mode: {cap_id}")
        entrypoint = item.get("entrypoint")
        argv = item.get("argv")
        if entrypoint is not None and (not isinstance(entrypoint, str) or not entrypoint):
            raise ValueError(f"invalid entrypoint: {cap_id}")
        if argv is not None and (not isinstance(argv, list) or not all(isinstance(v, str) for v in argv)):
            raise ValueError(f"invalid argv: {cap_id}")
    return registry


def repository_guards(root: Path) -> dict[str, Any]:
    manifest = _load_json(root / MANIFEST_FILENAME)
    return {
        "production_game_code_allowed": bool(manifest.get("production_game_code_allowed")),
        "embedded_godot_project_allowed": bool(manifest.get("embedded_godot_project_allowed")),
        "repository_role": manifest.get("repository_role"),
        "arcont_version": manifest.get("arcont_version"),
    }


def capability_snapshot(root: Path) -> dict[str, Any]:
    registry = load_registry(root)
    rows = []
    for item in registry["capabilities"]:
        entrypoint = item.get("entrypoint")
        available = True
        resolved_entrypoint = None
        if entrypoint:
            candidate = (root / entrypoint).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                available = False
            else:
                available = candidate.is_file()
                resolved_entrypoint = entrypoint
        row = dict(item)
        row["available"] = available
        if resolved_entrypoint:
            row["resolved_entrypoint"] = resolved_entrypoint
        rows.append(row)
    return {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "root": str(root),
        "guards": repository_guards(root),
        "capabilities": rows,
    }


def _clip(text: str) -> str:
    if len(text) <= MAX_STDIO_CHARS:
        return text
    return text[:MAX_STDIO_CHARS] + "\n...<truncated>"


def _json_or_text(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return _clip(stripped)


def run_diagnostics(root: Path, timeout_seconds: int) -> dict[str, Any]:
    registry = load_registry(root)
    results = []
    started = time.monotonic()
    for item in registry["capabilities"]:
        if not item.get("doctor", False):
            continue
        if item.get("access") != "read-only":
            results.append({"id": item["id"], "ok": False, "status": "refused-non-read-only"})
            continue
        entrypoint = item.get("entrypoint")
        if not entrypoint:
            results.append({"id": item["id"], "ok": False, "status": "missing-entrypoint"})
            continue
        script = (root / entrypoint).resolve()
        try:
            script.relative_to(root.resolve())
        except ValueError:
            results.append({"id": item["id"], "ok": False, "status": "entrypoint-outside-root"})
            continue
        if not script.is_file():
            results.append({"id": item["id"], "ok": False, "status": "entrypoint-missing"})
            continue
        command = [sys.executable, str(script), *item.get("argv", [])]
        try:
            proc = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            results.append(
                {
                    "id": item["id"],
                    "ok": proc.returncode == 0,
                    "status": "passed" if proc.returncode == 0 else "failed",
                    "exit_code": proc.returncode,
                    "stdout": _json_or_text(proc.stdout),
                    "stderr": _clip(proc.stderr.strip()) or None,
                }
            )
        except subprocess.TimeoutExpired as exc:
            results.append(
                {
                    "id": item["id"],
                    "ok": False,
                    "status": "timeout",
                    "timeout_seconds": timeout_seconds,
                    "stdout": _clip((exc.stdout or "") if isinstance(exc.stdout, str) else ""),
                    "stderr": _clip((exc.stderr or "") if isinstance(exc.stderr, str) else ""),
                }
            )
    return {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "operation": "doctor",
        "ok": all(row.get("ok") for row in results) if results else True,
        "duration_ms": round((time.monotonic() - started) * 1000, 3),
        "results": results,
    }


def inspect_project(project_root: Path, max_files: int) -> dict[str, Any]:
    project_root = project_root.resolve()
    if not project_root.is_dir():
        raise FileNotFoundError(f"project root is not a directory: {project_root}")
    if max_files < 1:
        raise ValueError("max_files must be >= 1")

    ext_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    top_level_dirs: Counter[str] = Counter()
    total_bytes = 0
    file_count = 0
    truncated = False

    for current, dirs, files in os.walk(project_root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not (Path(current) / d).is_symlink()]
        for name in files:
            path = Path(current) / name
            if path.is_symlink():
                continue
            if file_count >= max_files:
                truncated = True
                break
            file_count += 1
            try:
                total_bytes += path.stat().st_size
            except OSError:
                pass
            rel = path.relative_to(project_root)
            if len(rel.parts) > 1:
                top_level_dirs[rel.parts[0]] += 1
            suffix = path.suffix.lower() or "<none>"
            ext_counts[suffix] += 1
            if suffix in SOURCE_EXTENSIONS:
                category_counts["source"] += 1
            if suffix in ASSET_2D_EXTENSIONS:
                category_counts["assets_2d"] += 1
            if suffix in ASSET_3D_EXTENSIONS:
                category_counts["assets_3d"] += 1
            if suffix in AUDIO_EXTENSIONS:
                category_counts["audio"] += 1
            if suffix in SCENE_EXTENSIONS:
                category_counts["scenes"] += 1
            if suffix in RESOURCE_EXTENSIONS:
                category_counts["resources"] += 1
        if truncated:
            break

    detectors = {
        "godot": (project_root / "project.godot").is_file(),
        "unity": (project_root / "ProjectSettings" / "ProjectVersion.txt").is_file(),
        "unreal": any(project_root.glob("*.uproject")),
    }
    engine = next((name for name, matched in detectors.items() if matched), "unknown")

    return {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "operation": "inspect-project",
        "project": {
            "root": str(project_root),
            "engine": engine,
            "detectors": detectors,
            "file_count": file_count,
            "total_bytes_observed": total_bytes,
            "scan_truncated": truncated,
            "max_files": max_files,
            "categories": dict(sorted(category_counts.items())),
            "extensions": dict(ext_counts.most_common(40)),
            "top_level_directories": dict(top_level_dirs.most_common(30)),
        },
        "write_performed": False,
        "limitations": [
            "Static inventory only; no engine execution, scene rendering, asset semantic review, or performance claim.",
            "Symlinks and generated/cache directories are skipped.",
        ],
    }


def cmd_capabilities(args: argparse.Namespace) -> int:
    print(json.dumps(capability_snapshot(Path(args.root).resolve()), indent=2, sort_keys=True))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    report = run_diagnostics(Path(args.root).resolve(), args.timeout)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def cmd_inspect_project(args: argparse.Namespace) -> int:
    print(json.dumps(inspect_project(Path(args.project_root), args.max_files), indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="arcont-agent", description="ARCONT machine-readable agent control plane")
    parser.add_argument("--root", default=str(repo_root()), help="ARCONT repository root")
    sub = parser.add_subparsers(dest="command", required=True)

    caps = sub.add_parser("capabilities", help="list whitelisted ARCONT capabilities and repository guards")
    caps.set_defaults(func=cmd_capabilities)

    doctor = sub.add_parser("doctor", help="run whitelisted read-only diagnostics")
    doctor.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="per-capability timeout in seconds")
    doctor.set_defaults(func=cmd_doctor)

    inspect_cmd = sub.add_parser("inspect-project", help="inspect an external game repository without modifying it")
    inspect_cmd.add_argument("project_root")
    inspect_cmd.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    inspect_cmd.set_defaults(func=cmd_inspect_project)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema_version": 1, "protocol": PROTOCOL, "ok": False, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
