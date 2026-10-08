#!/usr/bin/env python3
"""ARCONT Universal Agent Bridge v1.

A transport-neutral, one-request JSON/stdio surface for external AI agents.
The bridge exposes project discovery, persistent project intent, asset
inventory, bounded hypothesis evaluation and execution of existing ARCONT
plans. It never grants a new mutation primitive: write operations still pass
through the normal revision-aware execution loop and require explicit opt-in.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from tools.arcont_agent import (
        capability_snapshot,
        inspect_project,
        invoke_capability,
        load_registry,
        repo_root,
    )
    from tools.agent_execution_loop import execute_plan
    from tools.agent_hypothesis_gate import evaluate_proposal
except ModuleNotFoundError:
    from arcont_agent import capability_snapshot, inspect_project, invoke_capability, load_registry, repo_root
    from agent_execution_loop import execute_plan
    from agent_hypothesis_gate import evaluate_proposal

PROTOCOL = "arcont-bridge"
VERSION = 1
INTENT_FILENAME = "project.intent.json"
MAX_ASSETS_DEFAULT = 2000
MAX_ASSETS_HARD = 10000
HASH_FILE_LIMIT = 64 * 1024 * 1024
AUTHORING_JSON_LIMIT = 2 * 1024 * 1024
AUTHORING_ROOTS = ("authoring/recipes", "authoring/scenarios")

ASSET_KINDS = {
    ".png": "texture", ".jpg": "texture", ".jpeg": "texture", ".webp": "texture",
    ".svg": "vector", ".bmp": "texture", ".tga": "texture", ".exr": "texture", ".hdr": "texture",
    ".glb": "model3d", ".gltf": "model3d", ".fbx": "model3d", ".obj": "model3d",
    ".dae": "model3d", ".blend": "model3d",
    ".wav": "audio", ".ogg": "audio", ".mp3": "audio", ".flac": "audio", ".opus": "audio",
    ".ttf": "font", ".otf": "font", ".woff": "font", ".woff2": "font",
    ".tscn": "scene", ".scn": "scene", ".tres": "resource", ".res": "resource",
    ".gdshader": "shader",
}
IGNORED_DIRS = {".git", ".godot", ".arcont", "node_modules", "__pycache__", ".cache"}


class BridgeError(ValueError):
    pass


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BridgeError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BridgeError(f"{label} is not valid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BridgeError(f"{label} must be a JSON object")
    return value


def _safe_project(project: Path, arcont_root: Path) -> Path:
    resolved = project.resolve()
    if not resolved.is_dir():
        raise BridgeError(f"project root is not a directory: {resolved}")
    root = arcont_root.resolve()
    if resolved == root or root in resolved.parents or resolved in root.parents:
        raise BridgeError(
            "refusing overlapping ARCONT/project trees; neither path may contain the other"
        )
    return resolved


def validate_intent(intent: Any) -> dict[str, Any]:
    if not isinstance(intent, dict):
        raise BridgeError("project intent must be an object")
    allowed = {
        "protocol", "version", "project_id", "title", "genre", "targets", "visual_style",
        "references", "goals", "priorities", "scope", "performance", "asset_policy",
        "constraints", "notes"
    }
    unknown = set(intent) - allowed
    if unknown:
        raise BridgeError(f"project intent has unsupported fields: {sorted(unknown)}")
    if intent.get("protocol") != "arcont-project-intent" or intent.get("version") != 1:
        raise BridgeError("unsupported project intent protocol/version")
    for key in ("project_id", "title", "genre"):
        value = intent.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > 200:
            raise BridgeError(f"project intent requires non-empty {key} <=200 chars")
    for key in ("targets", "references", "goals", "priorities", "constraints"):
        if key in intent:
            values = intent[key]
            if not isinstance(values, list) or len(values) > 64 or not all(isinstance(x, str) and x.strip() and len(x) <= 500 for x in values):
                raise BridgeError(f"project intent {key} must be an array of non-empty strings")
    if "visual_style" in intent and (not isinstance(intent["visual_style"], str) or len(intent["visual_style"]) > 500):
        raise BridgeError("project intent visual_style must be a string <=500 chars")
    if "scope" in intent and (not isinstance(intent["scope"], str) or len(intent["scope"]) > 1000):
        raise BridgeError("project intent scope must be a string <=1000 chars")
    if "notes" in intent and (not isinstance(intent["notes"], str) or len(intent["notes"]) > 4000):
        raise BridgeError("project intent notes must be a string <=4000 chars")

    performance = intent.get("performance", {})
    if not isinstance(performance, dict) or set(performance) - {"target_fps", "resolution", "platform_notes"}:
        raise BridgeError("invalid project intent performance")
    if "target_fps" in performance:
        fps = performance["target_fps"]
        if isinstance(fps, bool) or not isinstance(fps, (int, float)) or fps <= 0 or fps > 1000:
            raise BridgeError("performance.target_fps must be in (0,1000]")
    for key in ("resolution", "platform_notes"):
        if key in performance and (not isinstance(performance[key], str) or len(performance[key]) > 500):
            raise BridgeError(f"performance.{key} must be a string <=500 chars")

    asset_policy = intent.get("asset_policy", {})
    allowed_asset = {
        "user_assets", "public_assets", "commercial_use_required",
        "allow_network_discovery", "allowed_licenses", "forbidden_licenses"
    }
    if not isinstance(asset_policy, dict) or set(asset_policy) - allowed_asset:
        raise BridgeError("invalid project intent asset_policy")
    for key in ("user_assets", "public_assets", "commercial_use_required", "allow_network_discovery"):
        if key in asset_policy and not isinstance(asset_policy[key], bool):
            raise BridgeError(f"asset_policy.{key} must be boolean")
    for key in ("allowed_licenses", "forbidden_licenses"):
        if key in asset_policy:
            values = asset_policy[key]
            if not isinstance(values, list) or len(values) > 64 or not all(isinstance(x, str) and x.strip() for x in values):
                raise BridgeError(f"asset_policy.{key} must be an array of license identifiers")

    return intent


def read_intent(project: Path) -> dict[str, Any]:
    path = project / INTENT_FILENAME
    if not path.is_file():
        return {
            "ok": True,
            "present": False,
            "path": INTENT_FILENAME,
            "intent": None,
            "limitations": ["No persistent project intent is available; the agent must not infer missing product requirements from ARCONT."],
        }
    intent = validate_intent(_load_object(path, "project intent"))
    canonical = json.dumps(intent, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "ok": True,
        "present": True,
        "path": INTENT_FILENAME,
        "sha256": hashlib.sha256(canonical).hexdigest(),
        "intent": intent,
    }


def inspect_assets(project: Path, max_assets: int = MAX_ASSETS_DEFAULT) -> dict[str, Any]:
    if isinstance(max_assets, bool) or not isinstance(max_assets, int) or not 1 <= max_assets <= MAX_ASSETS_HARD:
        raise BridgeError(f"max_assets must be an integer in [1,{MAX_ASSETS_HARD}]")
    assets: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    total_bytes = 0
    truncated = False

    for current, dirs, files in os.walk(project, followlinks=False):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not (Path(current) / d).is_symlink()]
        for name in files:
            path = Path(current) / name
            if path.is_symlink():
                continue
            kind = ASSET_KINDS.get(path.suffix.lower())
            if kind is None:
                continue
            if len(assets) >= max_assets:
                truncated = True
                break
            try:
                size = path.stat().st_size
            except OSError:
                size = None
            row: dict[str, Any] = {
                "path": path.relative_to(project).as_posix(),
                "kind": kind,
                "extension": path.suffix.lower(),
                "bytes": size,
            }
            if isinstance(size, int):
                total_bytes += size
                if size <= HASH_FILE_LIMIT:
                    try:
                        row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                    except OSError:
                        row["sha256"] = None
                else:
                    row["sha256"] = None
                    row["hash_skipped_reason"] = "file exceeds bridge v1 hash limit"
            assets.append(row)
            counts[kind] = counts.get(kind, 0) + 1
        if truncated:
            break

    return {
        "ok": True,
        "asset_count": len(assets),
        "total_bytes_observed": total_bytes,
        "counts": dict(sorted(counts.items())),
        "truncated": truncated,
        "max_assets": max_assets,
        "assets": assets,
        "limitations": [
            "Inventory identifies local project files only; it does not infer copyright/license rights from file contents.",
            "assets.inspect inventories local files only; provider-scoped network discovery is available separately through asset.public.* when project policy allows it.",
            "Technical inventory does not establish artistic quality, runtime cost, rig correctness or target-platform suitability.",
        ],
    }



def authoring_catalog(project: Path) -> dict[str, Any]:
    documents: list[dict[str, Any]] = []
    for root_name in AUTHORING_ROOTS:
        root = project / root_name
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.json")):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            row: dict[str, Any] = {
                "path": path.relative_to(project).as_posix(),
                "kind": "recipe" if root_name.endswith("recipes") else "scenario",
                "bytes": size,
            }
            if size <= AUTHORING_JSON_LIMIT:
                try:
                    data = _load_object(path, "authoring document")
                    for key in ("id", "version", "title", "purpose"):
                        if key in data and (data[key] is None or isinstance(data[key], (str, int, float, bool))):
                            row[key] = data[key]
                    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                    row["sha256"] = hashlib.sha256(canonical).hexdigest()
                except (BridgeError, OSError):
                    row["parseable"] = False
                else:
                    row["parseable"] = True
            else:
                row["parseable"] = False
                row["parse_skipped_reason"] = "document exceeds bridge v1 authoring JSON limit"
            documents.append(row)
    return {
        "ok": True,
        "godot_authoring_contract_present": (project / "godot-authoring.json").is_file(),
        "map_forge_contract_present": (project / "map-forge.authoring.json").is_file(),
        "documents": documents,
        "document_count": len(documents),
        "allowed_roots": list(AUTHORING_ROOTS),
    }


def read_authoring_document(project: Path, relative_path: Any) -> dict[str, Any]:
    if not isinstance(relative_path, str) or not relative_path or len(relative_path) > 500:
        raise BridgeError("authoring.document.read requires a non-empty path <=500 chars")
    rel = Path(relative_path)
    if rel.is_absolute() or ".." in rel.parts:
        raise BridgeError("authoring document path must be project-relative and cannot traverse parents")
    normalized = rel.as_posix()
    if not any(normalized == root or normalized.startswith(root + "/") for root in AUTHORING_ROOTS):
        raise BridgeError("authoring document path is outside allowed authoring roots")
    if rel.suffix.lower() != ".json":
        raise BridgeError("authoring document must be JSON")
    path = (project / rel).resolve()
    try:
        path.relative_to(project.resolve())
    except ValueError as exc:
        raise BridgeError("authoring document escapes project root") from exc
    if path.is_symlink() or not path.is_file():
        raise BridgeError(f"authoring document not found: {relative_path}")
    size = path.stat().st_size
    if size > AUTHORING_JSON_LIMIT:
        raise BridgeError("authoring document exceeds bridge v1 size limit")
    data = _load_object(path, "authoring document")
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "ok": True,
        "path": normalized,
        "sha256": hashlib.sha256(canonical).hexdigest(),
        "document": data,
    }


def discover(arcont_root: Path, project: Path) -> dict[str, Any]:
    snapshot = capability_snapshot(arcont_root)
    return {
        "ok": True,
        "bridge": {
            "protocol": PROTOCOL,
            "version": VERSION,
            "transport": "json-stdio",
            "operations": [
                "discover",
                "project.inspect",
                "project.intent.read",
                "project.bootstrap",
                "assets.inspect",
                "asset.user.inspect",
                "asset.user.stage",
                "asset.user.list",
                "asset.public.providers",
                "asset.public.search",
                "asset.public.files",
                "asset.public.stage",
                "asset.public.list",
                "godot.structured.validate",
                "godot.script.inspect",
                "godot.script.create",
                "godot.script.replace",
                "godot.script.function.replace",
                "godot.scene.inspect",
                "godot.scene.edit",
                "godot.resource.inspect",
                "godot.resource.edit",
                "godot.input.action.set",
                "development.session.capabilities",
                "development.session.create",
                "development.session.inspect",
                "development.session.execute",
                "authoring.catalog",
                "authoring.document.read",
                "hypothesis.evaluate",
                "plan.execute",
            ],
            "mutation_boundary": {
                "bridge_creates_new_writer_primitives": False,
                "direct_writer_operations": [
                    "project.bootstrap", "asset.user.stage", "asset.public.stage",
                    "godot.script.create", "godot.script.replace", "godot.script.function.replace",
                    "godot.scene.inspect", "godot.scene.edit", "godot.resource.inspect", "godot.resource.edit",
                    "godot.input.action.set",
                    "development.session.create", "development.session.execute"
                ],
                "direct_writer_operations_require_explicit_write_opt_in": True,
                "plan_execute_requires_explicit_write_opt_in": True,
                "arbitrary_shell_execution_allowed": False,
                "auto_retry_mutations_allowed": False,
            },
        },
        "project": {
            "root": str(project),
            "intent_path": INTENT_FILENAME,
        },
        "agent_control": snapshot,
    }


def handle_request(
    arcont_root: Path,
    project: Path,
    request: dict[str, Any],
    *,
    allow_project_write: bool,
) -> dict[str, Any]:
    if request.get("protocol") != PROTOCOL or request.get("version") != VERSION:
        raise BridgeError("unsupported ARCONT bridge protocol/version")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 128:
        raise BridgeError("bridge request requires non-empty request_id <=128 chars")
    operation = request.get("operation")
    if operation not in {
        "discover", "project.inspect", "project.intent.read", "project.bootstrap", "assets.inspect",
        "asset.user.inspect", "asset.user.stage", "asset.user.list",
        "asset.public.providers", "asset.public.search", "asset.public.files", "asset.public.stage", "asset.public.list",
        "godot.structured.validate", "godot.script.inspect", "godot.script.create", "godot.script.replace",
        "godot.script.function.replace", "godot.scene.inspect", "godot.scene.edit",
        "godot.resource.inspect", "godot.resource.edit", "godot.input.action.set",
        "development.session.capabilities", "development.session.create",
        "development.session.inspect", "development.session.execute",
        "authoring.catalog", "authoring.document.read", "hypothesis.evaluate", "plan.execute"
    }:
        raise BridgeError(f"unsupported bridge operation: {operation!r}")
    args = request.get("arguments", {})
    if not isinstance(args, dict):
        raise BridgeError("bridge request arguments must be an object")

    project = _safe_project(project, arcont_root)
    if operation == "discover":
        result = discover(arcont_root, project)
    elif operation == "project.inspect":
        max_files = args.get("max_files", 50000)
        if isinstance(max_files, bool) or not isinstance(max_files, int) or max_files < 1 or max_files > 200000:
            raise BridgeError("max_files must be an integer in [1,200000]")
        result = inspect_project(project, max_files)
    elif operation == "project.intent.read":
        if args:
            raise BridgeError("project.intent.read accepts no arguments")
        result = read_intent(project)
    elif operation == "project.bootstrap":
        if set(args) - {"intent", "template"} or "intent" not in args:
            raise BridgeError("project.bootstrap requires intent and optional template")
        result = invoke_capability(
            arcont_root,
            "project.bootstrap.control",
            project,
            {
                "protocol_version": 1,
                "operation": "bootstrap",
                "intent": args["intent"],
                "template": args.get("template", "godot-3d-minimal"),
            },
            allow_project_write,
            120,
        )
    elif operation == "assets.inspect":
        unknown = set(args) - {"max_assets"}
        if unknown:
            raise BridgeError(f"assets.inspect has unsupported arguments: {sorted(unknown)}")
        result = inspect_assets(project, args.get("max_assets", MAX_ASSETS_DEFAULT))
    elif operation == "asset.user.inspect":
        if set(args) != {"source"}:
            raise BridgeError("asset.user.inspect requires exactly one source")
        try:
            from tools.user_asset_intake import execute as asset_intake_execute
        except ModuleNotFoundError:
            from user_asset_intake import execute as asset_intake_execute
        result = asset_intake_execute(
            project,
            {"protocol_version": 1, "operation": "inspect", "source": args["source"]},
        )
    elif operation == "asset.user.list":
        if args:
            raise BridgeError("asset.user.list accepts no arguments")
        try:
            from tools.user_asset_intake import execute as asset_intake_execute
        except ModuleNotFoundError:
            from user_asset_intake import execute as asset_intake_execute
        result = asset_intake_execute(project, {"protocol_version": 1, "operation": "list"})
    elif operation == "asset.user.stage":
        if set(args) != {"asset_id", "source", "rights"}:
            raise BridgeError("asset.user.stage requires asset_id, source and rights")
        result = invoke_capability(
            arcont_root,
            "asset-intake.control",
            project,
            {
                "protocol_version": 1,
                "operation": "stage",
                "asset_id": args["asset_id"],
                "source": args["source"],
                "rights": args["rights"],
            },
            allow_project_write,
            120,
        )
    elif operation in {"asset.public.providers", "asset.public.search", "asset.public.files", "asset.public.list"}:
        try:
            from tools.public_asset_discovery import execute as public_asset_execute
        except ModuleNotFoundError:
            from public_asset_discovery import execute as public_asset_execute
        if operation == "asset.public.providers":
            if args:
                raise BridgeError("asset.public.providers accepts no arguments")
            public_request = {"protocol_version": 1, "operation": "providers"}
        elif operation == "asset.public.search":
            unknown = set(args) - {"query", "asset_type", "limit"}
            if unknown or "query" not in args:
                raise BridgeError("asset.public.search requires query and optional asset_type/limit")
            public_request = {
                "protocol_version": 1,
                "operation": "search",
                "query": args["query"],
                "asset_type": args.get("asset_type", "all"),
                "limit": args.get("limit", 10),
            }
        elif operation == "asset.public.files":
            if set(args) != {"asset_id"}:
                raise BridgeError("asset.public.files requires exactly one asset_id")
            public_request = {
                "protocol_version": 1,
                "operation": "files",
                "asset_id": args["asset_id"],
            }
        else:
            if args:
                raise BridgeError("asset.public.list accepts no arguments")
            public_request = {"protocol_version": 1, "operation": "list"}
        result = public_asset_execute(project, public_request)
    elif operation == "asset.public.stage":
        if set(args) != {"semantic_id", "asset_id", "file_key", "manifest_sha256"}:
            raise BridgeError("asset.public.stage requires semantic_id, asset_id, file_key and manifest_sha256")
        result = invoke_capability(
            arcont_root,
            "public-asset.control",
            project,
            {
                "protocol_version": 1,
                "operation": "stage",
                "semantic_id": args["semantic_id"],
                "asset_id": args["asset_id"],
                "file_key": args["file_key"],
                "manifest_sha256": args["manifest_sha256"],
            },
            allow_project_write,
            900,
        )
    elif operation in {"godot.structured.validate", "godot.script.inspect"}:
        try:
            from tools.godot_structured_editing import execute as structured_execute
        except ModuleNotFoundError:
            from godot_structured_editing import execute as structured_execute
        mapping = {
            "godot.structured.validate": "validate",
            "godot.script.inspect": "script.inspect",
        }
        structured_request = {"protocol_version": 1, "operation": mapping[operation], **args}
        result = structured_execute(project, structured_request)
    elif operation in {
        "godot.script.create", "godot.script.replace", "godot.script.function.replace",
        "godot.scene.inspect", "godot.scene.edit", "godot.resource.inspect", "godot.resource.edit",
        "godot.input.action.set"
    }:
        mapping = {
            "godot.script.create": "script.create",
            "godot.script.replace": "script.replace",
            "godot.script.function.replace": "script.function.replace",
            "godot.scene.inspect": "scene.inspect",
            "godot.scene.edit": "scene.edit",
            "godot.resource.inspect": "resource.inspect",
            "godot.resource.edit": "resource.edit",
            "godot.input.action.set": "input.action.set",
        }
        result = invoke_capability(
            arcont_root,
            "godot.structured.control",
            project,
            {"protocol_version": 1, "operation": mapping[operation], **args},
            allow_project_write,
            900,
        )
    elif operation in {"development.session.capabilities", "development.session.inspect"}:
        try:
            from tools.development_session import execute as development_session_execute
        except ModuleNotFoundError:
            from development_session import execute as development_session_execute
        if operation == "development.session.capabilities":
            if args:
                raise BridgeError("development.session.capabilities accepts no arguments")
            session_request = {"protocol_version": 1, "operation": "capabilities"}
        else:
            if set(args) != {"session_id"}:
                raise BridgeError("development.session.inspect requires session_id")
            session_request = {
                "protocol_version": 1,
                "operation": "inspect",
                "session_id": args["session_id"],
            }
        result = development_session_execute(project, session_request)
    elif operation in {"development.session.create", "development.session.execute"}:
        if operation == "development.session.create":
            if set(args) != {"spec"}:
                raise BridgeError("development.session.create requires spec")
            session_request = {
                "protocol_version": 1,
                "operation": "create",
                "spec": args["spec"],
            }
        else:
            required = {"session_id", "if_session_revision", "milestone_id", "plan", "complete_milestone"}
            unknown = set(args) - (required | {"completion_note", "completion_evidence"})
            if unknown or not required.issubset(args):
                raise BridgeError("development.session.execute requires session revision, milestone, plan and completion flag")
            session_request = {
                "protocol_version": 1,
                "operation": "execute",
                **args,
            }
        result = invoke_capability(
            arcont_root,
            "development.session.control",
            project,
            session_request,
            allow_project_write,
            900,
        )
    elif operation == "authoring.catalog":
        if args:
            raise BridgeError("authoring.catalog accepts no arguments")
        result = authoring_catalog(project)
    elif operation == "authoring.document.read":
        if set(args) != {"path"}:
            raise BridgeError("authoring.document.read requires exactly one path")
        result = read_authoring_document(project, args["path"])
    elif operation == "hypothesis.evaluate":
        if set(args) != {"proposal", "evidence"}:
            raise BridgeError("hypothesis.evaluate requires proposal and evidence")
        if not isinstance(args["proposal"], dict) or not isinstance(args["evidence"], dict):
            raise BridgeError("proposal and evidence must be objects")
        result = evaluate_proposal(args["proposal"], args["evidence"])
    else:
        if set(args) != {"plan"} or not isinstance(args["plan"], dict):
            raise BridgeError("plan.execute requires exactly one plan object")
        registry = load_registry(arcont_root)
        result = execute_plan(
            arcont_root,
            project,
            args["plan"],
            allow_project_write,
            registry,
            inspect_project,
            invoke_capability,
        )

    return {
        "protocol": PROTOCOL,
        "version": VERSION,
        "request_id": request_id,
        "operation": operation,
        "ok": result.get("ok") is True,
        "result": result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="arcont-bridge", description=__doc__)
    parser.add_argument("--root", default=str(repo_root()), help="ARCONT repository root")
    parser.add_argument("--project", required=True, help="external game project root")
    parser.add_argument("--request", default="-", help="bridge request JSON path, or - for stdin")
    parser.add_argument("--allow-project-write", action="store_true",
                        help="required for plan.execute when its plan contains project mutations")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.request == "-" else Path(args.request).read_text(encoding="utf-8")
        request = json.loads(raw)
        if not isinstance(request, dict):
            raise BridgeError("bridge request must be a JSON object")
        report = handle_request(
            Path(args.root).resolve(),
            Path(args.project),
            request,
            allow_project_write=args.allow_project_write,
        )
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if report["ok"] else 1
    except (OSError, json.JSONDecodeError, BridgeError, ValueError, PermissionError) as exc:
        print(json.dumps({
            "protocol": PROTOCOL,
            "version": VERSION,
            "ok": False,
            "error": str(exc),
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
