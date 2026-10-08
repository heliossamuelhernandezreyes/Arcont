#!/usr/bin/env python3
"""Machine-readable control plane for ARCONT.

The control plane is read-only inside ARCONT. It discovers whitelisted
capabilities, runs bounded diagnostics, inspects external game repositories, and
can invoke explicitly authorized project writers without embedding production
game code in ARCONT.
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
        if item.get("access") not in {"read-only", "external-project-write", "external-runtime"}:
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


def invoke_capability(
    root: Path,
    capability_id: str,
    project_root: Path,
    request: dict[str, Any],
    allow_project_write: bool,
    timeout_seconds: int,
) -> dict[str, Any]:
    registry = load_registry(root)
    matches = [item for item in registry["capabilities"] if item.get("id") == capability_id]
    if len(matches) != 1:
        raise ValueError(f"unknown capability: {capability_id}")
    item = matches[0]
    if item.get("access") != "external-project-write" or not item.get("invocable", False):
        raise ValueError(f"capability is not an invocable external project writer: {capability_id}")
    if not allow_project_write:
        raise PermissionError("external project write permission is required")
    if not isinstance(request, dict) or request.get("protocol_version") != 1:
        raise ValueError("invocation request requires protocol_version=1")
    if timeout_seconds < 1 or timeout_seconds > 900:
        raise ValueError("timeout must be in [1,900] seconds")

    project = project_root.resolve()
    if not project.is_dir():
        raise FileNotFoundError(f"project root is not a directory: {project}")
    arcont = root.resolve()
    if project == arcont or arcont in project.parents or project in arcont.parents:
        raise ValueError(
            "refusing overlapping ARCONT/project trees; neither path may contain the other"
        )

    entrypoint = item.get("entrypoint")
    if not isinstance(entrypoint, str):
        raise ValueError("capability has no executable entrypoint")
    script = (arcont / entrypoint).resolve()
    try:
        script.relative_to(arcont)
    except ValueError as exc:
        raise ValueError("capability entrypoint escapes ARCONT") from exc
    if not script.is_file():
        raise FileNotFoundError(f"capability entrypoint is missing: {entrypoint}")

    project_arg = item.get("project_arg", "--project")
    request_arg = item.get("request_arg", "--request")
    if not isinstance(project_arg, str) or not isinstance(request_arg, str):
        raise ValueError("invalid invocation argument contract")
    command = [sys.executable, str(script), project_arg, str(project), request_arg, "-"]
    try:
        proc = subprocess.run(
            command,
            cwd=arcont,
            input=json.dumps(request, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "schema_version": 1,
            "protocol": PROTOCOL,
            "operation": "invoke",
            "capability": capability_id,
            "project": str(project),
            "ok": False,
            "status": "timeout",
            "timeout_seconds": timeout_seconds,
            "stdout": _clip((exc.stdout or "") if isinstance(exc.stdout, str) else ""),
            "stderr": _clip((exc.stderr or "") if isinstance(exc.stderr, str) else ""),
        }

    payload = _json_or_text(proc.stdout)
    child_ok = isinstance(payload, dict) and payload.get("ok") is True
    return {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "operation": "invoke",
        "capability": capability_id,
        "project": str(project),
        "permission": "explicit-project-write",
        "ok": proc.returncode == 0 and child_ok,
        "status": "completed" if proc.returncode == 0 else "failed",
        "exit_code": proc.returncode,
        "result": payload,
        "stderr": _clip(proc.stderr.strip()) or None,
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
        "ok": True,
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


def cmd_invoke(args: argparse.Namespace) -> int:
    raw = sys.stdin.read() if args.request == "-" else Path(args.request).read_text(encoding="utf-8")
    request = json.loads(raw)
    if not isinstance(request, dict):
        raise ValueError("request JSON must be an object")
    report = invoke_capability(
        Path(args.root).resolve(),
        args.capability,
        Path(args.project),
        request,
        args.allow_project_write,
        args.timeout,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def cmd_run_plan(args: argparse.Namespace) -> int:
    try:
        from tools.agent_execution_loop import execute_plan
    except ModuleNotFoundError:
        from agent_execution_loop import execute_plan
    raw = sys.stdin.read() if args.plan == "-" else Path(args.plan).read_text(encoding="utf-8")
    plan = json.loads(raw)
    if not isinstance(plan, dict):
        raise ValueError("plan JSON must be an object")
    root = Path(args.root).resolve()
    report = execute_plan(
        root,
        Path(args.project),
        plan,
        args.allow_project_write,
        load_registry(root),
        inspect_project,
        invoke_capability,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def cmd_diagnose(args: argparse.Namespace) -> int:
    try:
        from tools.agent_diagnosis import diagnose
    except ModuleNotFoundError:
        from agent_diagnosis import diagnose
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    raw = sys.stdin.read() if args.evidence == "-" else Path(args.evidence).read_text(encoding="utf-8")
    evidence = json.loads(raw)
    report = diagnose(policy, evidence)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    if not report["ok"]:
        return 1
    if args.require_match and not report.get("matched"):
        return 1
    return 0


def cmd_evaluate_proposal(args: argparse.Namespace) -> int:
    try:
        from tools.agent_hypothesis_gate import compile_policy, evaluate_proposal
    except ModuleNotFoundError:
        from agent_hypothesis_gate import compile_policy, evaluate_proposal
    proposal = json.loads(Path(args.proposal).read_text(encoding="utf-8"))
    raw = sys.stdin.read() if args.evidence == "-" else Path(args.evidence).read_text(encoding="utf-8")
    evidence = json.loads(raw)
    if not isinstance(proposal, dict) or not isinstance(evidence, dict):
        raise ValueError("proposal and evidence must be JSON objects")
    report = evaluate_proposal(proposal, evidence)
    if args.emit_policy:
        Path(args.emit_policy).write_text(
            json.dumps(compile_policy(proposal), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    if not report["ok"]:
        return 1
    if args.require_match and not report["diagnosis"].get("matched"):
        return 1
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

    invoke = sub.add_parser("invoke", help="invoke an explicitly registered external-project writer")
    invoke.add_argument("capability")
    invoke.add_argument("--project", required=True)
    invoke.add_argument("--request", default="-", help="request JSON path, or - for stdin")
    invoke.add_argument("--allow-project-write", action="store_true",
                        help="required explicit permission for any external project writer")
    invoke.add_argument("--timeout", type=int, default=120)
    invoke.set_defaults(func=cmd_invoke)

    run_plan = sub.add_parser("run-plan", help="execute a bounded revision-aware agent plan")
    run_plan.add_argument("--project", required=True)
    run_plan.add_argument("--plan", default="-", help="plan JSON path, or - for stdin")
    run_plan.add_argument("--allow-project-write", action="store_true",
                          help="required in addition to plan.permissions.project_write for writer steps")
    run_plan.set_defaults(func=cmd_run_plan)

    diagnose = sub.add_parser("diagnose", help="evaluate structured evidence and compile a bounded repair plan")
    diagnose.add_argument("--policy", required=True, help="diagnosis policy JSON path")
    diagnose.add_argument("--evidence", default="-", help="evidence JSON path, or - for stdin")
    diagnose.add_argument("--require-match", action="store_true", help="return nonzero if no hypothesis matches")
    diagnose.set_defaults(func=cmd_diagnose)

    proposal = sub.add_parser("evaluate-proposal", help="validate a model-authored hypothesis and compile a bounded repair proposal")
    proposal.add_argument("--proposal", required=True, help="model/human hypothesis proposal JSON path")
    proposal.add_argument("--evidence", default="-", help="structured evidence JSON path, or - for stdin")
    proposal.add_argument("--require-match", action="store_true", help="return nonzero if the proposed hypothesis does not match")
    proposal.add_argument("--emit-policy", help="optional output path for the validated compiled diagnosis policy")
    proposal.set_defaults(func=cmd_evaluate_proposal)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError, PermissionError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema_version": 1, "protocol": PROTOCOL, "ok": False, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
