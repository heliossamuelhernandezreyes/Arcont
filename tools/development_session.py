#!/usr/bin/env python3
"""Persistent bounded development sessions for ARCONT.

A development session is a durable orchestration envelope around the existing
ARCONT execution-plan engine. The external AI remains responsible for planning
and proposing the next bounded plan. ARCONT persists milestones, budgets,
receipts and revision state, executes at most one plan per request, and never
silently retries a failed mutation.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

try:
    from tools.agent_execution_loop import canonical_sha256, execute_plan, validate_plan
    from tools.arcont_agent import inspect_project, invoke_capability, load_registry
except ModuleNotFoundError:
    from agent_execution_loop import canonical_sha256, execute_plan, validate_plan
    from arcont_agent import inspect_project, invoke_capability, load_registry

PROTOCOL_VERSION = 1
SESSION_PROTOCOL = "arcont-development-session"
OPERATIONS = ("capabilities", "create", "inspect", "execute")
ID = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MAX_MILESTONES = 16
MAX_CAPABILITIES = 32
MAX_HISTORY = 32
MAX_ACCEPTANCE = 16
MAX_NOTE = 2000
BUDGET_LIMITS = {
    "max_plan_runs": (1, 32, 12),
    "max_execution_steps": (1, 256, 96),
    "max_write_steps": (0, 96, 48),
    "max_failed_runs": (0, 8, 4),
}


class SessionError(ValueError):
    pass


def arcont_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _state_revision(state: dict[str, Any]) -> str:
    material = dict(state)
    material.pop("revision", None)
    return _sha(material)


def _project(project: Path) -> Path:
    root = arcont_root().resolve()
    resolved = Path(project).resolve()
    if not resolved.is_dir():
        raise SessionError("external project root must exist")
    if resolved == root or root in resolved.parents:
        raise SessionError("refusing ARCONT itself or an embedded project")
    return resolved


def _intent_sha(project: Path) -> str:
    path = project / "project.intent.json"
    if not path.is_file() or path.is_symlink():
        raise SessionError("development session requires project.intent.json")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SessionError("project.intent.json is invalid JSON") from exc
    if not isinstance(value, dict):
        raise SessionError("project intent must be an object")
    if value.get("protocol") != "arcont-project-intent" or value.get("version") != 1:
        raise SessionError("unsupported project intent protocol/version")
    return _sha(value)


def _registry() -> tuple[dict[str, Any], str, set[str]]:
    root = arcont_root()
    registry = load_registry(root)
    registry_sha = canonical_sha256(registry)
    invocable = {
        item["id"]
        for item in registry.get("capabilities", [])
        if isinstance(item, dict)
        and item.get("invocable") is True
        and item.get("access") == "external-project-write"
        and isinstance(item.get("id"), str)
        and item.get("id") != "development.session.control"
    }
    return registry, registry_sha, invocable


def _file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _toolchain_sha(registry: dict[str, Any], capability_allowlist: list[str]) -> str:
    root = arcont_root().resolve()
    by_id = {
        item.get("id"): item
        for item in registry.get("capabilities", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    capabilities = []
    for capability_id in sorted(capability_allowlist):
        item = by_id.get(capability_id)
        if not isinstance(item, dict):
            raise SessionError(f"session capability disappeared from registry: {capability_id}")
        entrypoint = item.get("entrypoint")
        if not isinstance(entrypoint, str):
            raise SessionError(f"session capability has no entrypoint: {capability_id}")
        path = (root / entrypoint).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise SessionError("capability entrypoint escapes ARCONT") from exc
        if not path.is_file():
            raise SessionError(f"capability entrypoint is missing: {capability_id}")
        capabilities.append({
            "id": capability_id,
            "registry": item,
            "entrypoint_sha256": _file_sha(path),
        })
    core = {}
    for relative in (
        "tools/agent_execution_loop.py",
        "tools/arcont_agent.py",
        "tools/development_session.py",
    ):
        path = root / relative
        if not path.is_file():
            raise SessionError(f"development session core file missing: {relative}")
        core[relative] = _file_sha(path)
    return _sha({
        "registry_sha256": canonical_sha256(registry),
        "capabilities": capabilities,
        "core": core,
    })


def _session_root(project: Path, session_id: str) -> Path:
    base = project / ".arcont" / "development-sessions"
    current = project
    for part in Path(".arcont/development-sessions").parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise SessionError("session storage cannot traverse symlinks")
    root = base / session_id
    if root.exists() and root.is_symlink():
        raise SessionError("session directory cannot be a symlink")
    return root


@contextlib.contextmanager
def _session_lock(project: Path, session_id: str):
    root = _session_root(project, session_id)
    if not root.is_dir():
        raise SessionError("development session not found")
    lock_path = root / "session.lock"
    if lock_path.exists() and lock_path.is_symlink():
        raise SessionError("session lock cannot be a symlink")
    handle = lock_path.open("a+b")
    try:
        if os.name == "posix":
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        elif os.name == "nt":
            import msvcrt
            if lock_path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            raise SessionError("development session locking is unsupported on this platform")
        yield
    finally:
        try:
            if os.name == "posix":
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            elif os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            handle.close()


def _state_path(project: Path, session_id: str) -> Path:
    return _session_root(project, session_id) / "session.json"


def _pending_path(project: Path, session_id: str) -> Path:
    return _session_root(project, session_id) / "pending-run.json"


def _read_pending(project: Path, session_id: str) -> dict[str, Any] | None:
    path = _pending_path(project, session_id)
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise SessionError("development session pending-run marker is invalid")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SessionError("development session pending-run marker is invalid JSON") from exc
    required = {
        "protocol", "version", "session_id", "run_id", "milestone_id",
        "session_revision_before", "plan_id", "plan_sha256"
    }
    if not isinstance(value, dict) or set(value) != required:
        raise SessionError("development session pending-run marker has invalid fields")
    if value.get("protocol") != "arcont-development-session-pending" or value.get("version") != 1:
        raise SessionError("development session pending-run marker is invalid")
    if value.get("session_id") != session_id:
        raise SessionError("development session pending-run marker belongs to another session")
    for key in ("run_id", "milestone_id", "plan_id"):
        raw = value.get(key)
        if not isinstance(raw, str) or not raw or len(raw) > 128:
            raise SessionError(f"development session pending-run {key} is invalid")
    for key in ("session_revision_before", "plan_sha256"):
        raw = value.get(key)
        if not isinstance(raw, str) or not SHA256.fullmatch(raw):
            raise SessionError(f"development session pending-run {key} is invalid")
    return value


def _receipt_path_from_history(project: Path, row: dict[str, Any]) -> Path:
    relative = row.get("receipt")
    digest = row.get("receipt_sha256")
    if not isinstance(relative, str) or not relative.startswith(".arcont/development-sessions/"):
        raise SessionError("development session history receipt path is invalid")
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise SessionError("development session history receipt path escapes project")
    path = project / rel
    if path.is_symlink() or not path.is_file():
        raise SessionError("development session history receipt is missing")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise SessionError("development session history receipt hash is invalid")
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise SessionError("development session history receipt hash mismatch")
    return path


def _reconcile_completed_pending(project: Path, state: dict[str, Any]) -> dict[str, Any] | None:
    pending = _read_pending(project, state["id"])
    if pending is None:
        return None
    matches = [row for row in state.get("history", []) if row.get("run_id") == pending["run_id"]]
    if len(matches) > 1:
        raise SessionError("development session history contains duplicate run ids")
    if len(matches) == 1:
        row = matches[0]
        if row.get("milestone_id") != pending["milestone_id"]:
            raise SessionError("pending run milestone does not match committed history")
        if row.get("plan_id") != pending["plan_id"] or row.get("plan_sha256") != pending["plan_sha256"]:
            raise SessionError("pending run plan identity does not match committed history")
        _receipt_path_from_history(project, row)
        _pending_path(project, state["id"]).unlink()
        return None
    return pending


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise SessionError("session storage directory cannot be a symlink")
    temp = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
    temp.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temp, path)


def _load_state(project: Path, session_id: Any) -> dict[str, Any]:
    if not isinstance(session_id, str) or not ID.fullmatch(session_id):
        raise SessionError("invalid development session id")
    path = _state_path(project, session_id)
    if not path.is_file() or path.is_symlink():
        raise SessionError("development session not found")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SessionError("development session state is invalid JSON") from exc
    if not isinstance(state, dict):
        raise SessionError("development session state must be an object")
    if state.get("protocol") != SESSION_PROTOCOL or state.get("version") != 1:
        raise SessionError("unsupported development session state")
    revision = state.get("revision")
    if not isinstance(revision, str) or revision != _state_revision(state):
        raise SessionError("development session revision/hash mismatch")
    return state


def _budgets(value: Any) -> dict[str, int]:
    if value is None:
        value = {}
    if not isinstance(value, dict) or set(value) - set(BUDGET_LIMITS):
        raise SessionError("invalid development-session budgets")
    result: dict[str, int] = {}
    for key, (minimum, maximum, default) in BUDGET_LIMITS.items():
        raw = value.get(key, default)
        if isinstance(raw, bool) or not isinstance(raw, int) or not minimum <= raw <= maximum:
            raise SessionError(f"{key} must be in [{minimum},{maximum}]")
        result[key] = raw
    return result


def _milestones(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_MILESTONES:
        raise SessionError(f"milestones requires 1..{MAX_MILESTONES} entries")
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, dict) or set(raw) - {"id", "goal", "acceptance"}:
            raise SessionError(f"milestones/{index}: invalid fields")
        milestone_id = raw.get("id")
        if not isinstance(milestone_id, str) or not ID.fullmatch(milestone_id) or milestone_id in seen:
            raise SessionError(f"milestones/{index}: invalid or duplicate id")
        seen.add(milestone_id)
        goal = raw.get("goal")
        if not isinstance(goal, str) or not goal.strip() or len(goal) > 1000:
            raise SessionError(f"milestones/{index}: goal must be non-empty <=1000 chars")
        acceptance = raw.get("acceptance", [])
        if (
            not isinstance(acceptance, list)
            or len(acceptance) > MAX_ACCEPTANCE
            or not all(isinstance(item, str) and item.strip() and len(item) <= 500 for item in acceptance)
        ):
            raise SessionError(f"milestones/{index}: invalid acceptance list")
        rows.append(
            {
                "id": milestone_id,
                "goal": goal,
                "acceptance": acceptance,
                "status": "active" if index == 0 else "pending",
                "completed_by_run": None,
                "completion_note": None,
            }
        )
    return rows


def _session_capabilities(value: Any, known: set[str]) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or len(value) > MAX_CAPABILITIES
        or len(set(value)) != len(value)
    ):
        raise SessionError("capability_allowlist requires unique capability ids")
    for item in value:
        if not isinstance(item, str) or item not in known:
            raise SessionError(f"unsupported session capability: {item!r}")
    return value


def _remaining(state: dict[str, Any]) -> dict[str, int]:
    budgets = state["budgets"]
    counters = state["counters"]
    return {
        "plan_runs": max(0, budgets["max_plan_runs"] - counters["plan_runs"]),
        "execution_steps": max(0, budgets["max_execution_steps"] - counters["execution_steps"]),
        "write_steps": max(0, budgets["max_write_steps"] - counters["write_steps"]),
        "failed_runs": max(0, budgets["max_failed_runs"] - counters["failed_runs"]),
    }


def _active_milestone(state: dict[str, Any]) -> dict[str, Any] | None:
    rows = [item for item in state["milestones"] if item["status"] == "active"]
    if len(rows) > 1:
        raise SessionError("development session has multiple active milestones")
    return rows[0] if rows else None


def capabilities() -> dict[str, Any]:
    _, registry_sha, known = _registry()
    return {
        "ok": True,
        "write_performed": False,
        "result": {
            "protocol": SESSION_PROTOCOL,
            "version": 1,
            "operations": list(OPERATIONS),
            "max_milestones": MAX_MILESTONES,
            "max_history": MAX_HISTORY,
            "budget_limits": {
                key: {"min": low, "max": high, "default": default}
                for key, (low, high, default) in BUDGET_LIMITS.items()
            },
            "registry_sha256": registry_sha,
            "eligible_capabilities": sorted(known),
            "execution_semantics": [
                "one bounded ARCONT plan per execute request",
                "no silent retry",
                "failed plans stop and are recorded",
                "session writes require exact session revision",
                "plan capability allowlist must be a subset of session allowlist",
                "project intent and ARCONT registry hashes are pinned for the session",
            ],
        },
    }


def create(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    spec = request.get("spec")
    if not isinstance(spec, dict):
        raise SessionError("create requires spec object")
    allowed = {
        "id", "goal", "capability_allowlist", "permissions", "budgets", "milestones"
    }
    if set(spec) - allowed:
        raise SessionError("development session spec has unsupported fields")
    session_id = spec.get("id")
    if not isinstance(session_id, str) or not ID.fullmatch(session_id):
        raise SessionError("development session requires safe id")
    goal = spec.get("goal")
    if not isinstance(goal, str) or not goal.strip() or len(goal) > 2000:
        raise SessionError("development session goal must be non-empty <=2000 chars")
    permissions = spec.get("permissions", {"project_write": True})
    if (
        not isinstance(permissions, dict)
        or set(permissions) != {"project_write"}
        or not isinstance(permissions["project_write"], bool)
    ):
        raise SessionError("permissions must contain project_write boolean")

    root = _session_root(project, session_id)
    if root.exists():
        raise SessionError("development session id already exists")
    registry, registry_sha, known = _registry()
    capability_allowlist = _session_capabilities(spec.get("capability_allowlist"), known)
    milestones = _milestones(spec.get("milestones"))
    budgets = _budgets(spec.get("budgets"))
    intent_sha = _intent_sha(project)
    toolchain_sha = _toolchain_sha(registry, capability_allowlist)

    state: dict[str, Any] = {
        "protocol": SESSION_PROTOCOL,
        "version": 1,
        "id": session_id,
        "goal": goal,
        "status": "active",
        "stop_reason": None,
        "sequence": 0,
        "project_root": str(project),
        "project_intent_sha256": intent_sha,
        "registry_sha256": registry_sha,
        "toolchain_sha256": toolchain_sha,
        "permissions": permissions,
        "capability_allowlist": capability_allowlist,
        "budgets": budgets,
        "counters": {
            "plan_runs": 0,
            "execution_steps": 0,
            "write_steps": 0,
            "failed_runs": 0,
            "milestones_completed": 0,
        },
        "milestones": milestones,
        "history": [],
    }
    state["revision"] = _state_revision(state)
    root.mkdir(parents=True, exist_ok=False)
    _atomic_json(root / "session.json", state)
    return {
        "ok": True,
        "write_performed": True,
        "result": {
            "session": state,
            "remaining": _remaining(state),
            "next_milestone": _active_milestone(state),
        },
    }


def inspect(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    state = _load_state(project, request.get("session_id"))
    current_intent = _intent_sha(project)
    current_registry_obj, current_registry, _ = _registry()
    current_toolchain = _toolchain_sha(current_registry_obj, state["capability_allowlist"])
    pending = _read_pending(project, state["id"])
    return {
        "ok": True,
        "write_performed": False,
        "result": {
            "session": state,
            "remaining": _remaining(state),
            "next_milestone": _active_milestone(state),
            "pending_run": pending,
            "environment": {
                "intent_matches": current_intent == state["project_intent_sha256"],
                "registry_matches": current_registry == state["registry_sha256"],
                "toolchain_matches": current_toolchain == state["toolchain_sha256"],
                "current_project_intent_sha256": current_intent,
                "current_registry_sha256": current_registry,
                "current_toolchain_sha256": current_toolchain,
            },
        },
    }


def _require_revision(state: dict[str, Any], expected: Any) -> None:
    if not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise SessionError("execute requires if_session_revision SHA-256")
    if expected != state["revision"]:
        raise SessionError("development session revision conflict")


def _execute_one_locked(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    state = _load_state(project, request.get("session_id"))
    _require_revision(state, request.get("if_session_revision"))
    pending = _reconcile_completed_pending(project, state)
    if pending is not None:
        raise SessionError(
            "development session has an unresolved pending run; refuse automatic retry and inspect/review the project before starting a new session"
        )
    if state["status"] != "active":
        raise SessionError(f"development session is not active: {state['status']}")

    current_intent = _intent_sha(project)
    registry, current_registry, known = _registry()
    current_toolchain = _toolchain_sha(registry, state["capability_allowlist"])
    if current_intent != state["project_intent_sha256"]:
        raise SessionError("project intent changed since session creation; start a new reviewed session")
    if current_registry != state["registry_sha256"]:
        raise SessionError("ARCONT capability registry changed since session creation; start a new reviewed session")
    if current_toolchain != state["toolchain_sha256"]:
        raise SessionError("ARCONT session toolchain changed since session creation; start a new reviewed session")

    milestone = _active_milestone(state)
    if milestone is None:
        raise SessionError("active session has no active milestone")
    milestone_id = request.get("milestone_id")
    if milestone_id != milestone["id"]:
        raise SessionError("execute milestone_id must match the active milestone")

    plan = request.get("plan")
    validate_plan(plan, known)
    session_allow = set(state["capability_allowlist"])
    plan_allow = set(plan["capability_allowlist"])
    if not plan_allow.issubset(session_allow):
        raise SessionError("plan capability allowlist exceeds session capability allowlist")
    if plan.get("permissions", {}).get("project_write", False) and not state["permissions"]["project_write"]:
        raise SessionError("plan requests project write but session forbids it")

    complete_milestone = request.get("complete_milestone", False)
    if not isinstance(complete_milestone, bool):
        raise SessionError("complete_milestone must be boolean")
    note = request.get("completion_note")
    if note is not None and (not isinstance(note, str) or len(note) > MAX_NOTE):
        raise SessionError(f"completion_note must be null/string <={MAX_NOTE}")
    if complete_milestone and not milestone["acceptance"]:
        raise SessionError("milestone completion requires explicit acceptance criteria in session spec")

    remaining = _remaining(state)
    if remaining["plan_runs"] <= 0:
        raise SessionError("development-session plan-run budget exhausted")
    if len(plan["steps"]) > remaining["execution_steps"]:
        raise SessionError("plan exceeds remaining execution-step budget")
    invoke_steps = sum(1 for step in plan["steps"] if step.get("kind") == "invoke")
    if invoke_steps > remaining["write_steps"]:
        raise SessionError("plan invoke count exceeds remaining write-step budget")
    if remaining["failed_runs"] <= 0 and state["budgets"]["max_failed_runs"] > 0:
        raise SessionError("development-session failed-run budget exhausted")

    run_index = state["counters"]["plan_runs"] + 1
    run_id = f"run-{run_index:03d}-{uuid.uuid4().hex[:12]}"
    run_path = _session_root(project, state["id"]) / "runs" / f"{run_id}.json"
    if run_path.exists():
        raise SessionError("development-session run receipt collision")
    pending_path = _pending_path(project, state["id"])
    if pending_path.exists():
        raise SessionError("development-session pending run already exists")
    _atomic_json(
        pending_path,
        {
            "protocol": "arcont-development-session-pending",
            "version": 1,
            "session_id": state["id"],
            "run_id": run_id,
            "milestone_id": milestone["id"],
            "session_revision_before": state["revision"],
            "plan_id": plan["id"],
            "plan_sha256": canonical_sha256(plan),
        },
    )

    result = execute_plan(
        arcont_root(),
        project,
        plan,
        state["permissions"]["project_write"],
        registry,
        inspect_project,
        invoke_capability,
    )

    post_intent = _intent_sha(project)
    post_registry_obj, post_registry, _ = _registry()
    post_toolchain = _toolchain_sha(post_registry_obj, state["capability_allowlist"])
    environment_stable = (
        post_intent == state["project_intent_sha256"]
        and post_registry == state["registry_sha256"]
        and post_toolchain == state["toolchain_sha256"]
    )

    receipt = {
        "protocol": "arcont-development-session-run",
        "version": 1,
        "session_id": state["id"],
        "run_id": run_id,
        "milestone_id": milestone["id"],
        "session_revision_before": state["revision"],
        "plan": plan,
        "plan_sha256": canonical_sha256(plan),
        "execution": result,
        "complete_milestone_requested": complete_milestone,
        "completion_note": note,
        "environment_after": {
            "project_intent_sha256": post_intent,
            "registry_sha256": post_registry,
            "toolchain_sha256": post_toolchain,
            "stable": environment_stable,
        },
    }
    _atomic_json(run_path, receipt)
    receipt_sha = hashlib.sha256(run_path.read_bytes()).hexdigest()

    state["sequence"] += 1
    state["counters"]["plan_runs"] += 1
    state["counters"]["execution_steps"] += int(result.get("steps_completed", 0) or 0)
    state["counters"]["write_steps"] += int(result.get("write_steps", 0) or 0)
    if result.get("ok") is not True:
        state["counters"]["failed_runs"] += 1

    history_row = {
        "run_id": run_id,
        "milestone_id": milestone["id"],
        "ok": result.get("ok") is True,
        "status": result.get("status"),
        "plan_id": plan["id"],
        "plan_sha256": canonical_sha256(plan),
        "receipt": run_path.relative_to(project).as_posix(),
        "receipt_sha256": receipt_sha,
        "steps_completed": result.get("steps_completed", 0),
        "write_steps": result.get("write_steps", 0),
        "failed_step": result.get("failed_step"),
    }
    state["history"].append(history_row)
    if len(state["history"]) > MAX_HISTORY:
        raise SessionError("session history exceeded hard limit")

    if result.get("ok") is True and complete_milestone and environment_stable:
        milestone["status"] = "completed"
        milestone["completed_by_run"] = run_id
        milestone["completion_note"] = note
        state["counters"]["milestones_completed"] += 1
        pending = [item for item in state["milestones"] if item["status"] == "pending"]
        if pending:
            pending[0]["status"] = "active"
        else:
            state["status"] = "completed"
            state["stop_reason"] = "all-milestones-completed"

    if result.get("ok") is not True:
        failed_remaining = state["budgets"]["max_failed_runs"] - state["counters"]["failed_runs"]
        if failed_remaining <= 0:
            state["status"] = "paused"
            state["stop_reason"] = "failed-run-budget-exhausted"

    if not environment_stable:
        state["status"] = "paused"
        state["stop_reason"] = "environment-changed-during-run"

    after_remaining = _remaining(state)
    if state["status"] == "active":
        if after_remaining["plan_runs"] <= 0:
            state["status"] = "paused"
            state["stop_reason"] = "plan-run-budget-exhausted"
        elif after_remaining["execution_steps"] <= 0:
            state["status"] = "paused"
            state["stop_reason"] = "execution-step-budget-exhausted"
        elif after_remaining["write_steps"] <= 0 and state["permissions"]["project_write"]:
            state["status"] = "paused"
            state["stop_reason"] = "write-step-budget-exhausted"

    state["revision"] = _state_revision(state)
    _atomic_json(_state_path(project, state["id"]), state)
    if pending_path.is_file() and not pending_path.is_symlink():
        pending_path.unlink()

    return {
        "ok": result.get("ok") is True and environment_stable,
        "write_performed": True,
        "result": {
            "session": state,
            "execution": result,
            "run": history_row,
            "remaining": _remaining(state),
            "next_milestone": _active_milestone(state),
            "next_action": (
                "session-complete"
                if state["status"] == "completed"
                else "session-paused"
                if not environment_stable
                else "review-failure-and-submit-new-plan"
                if result.get("ok") is not True and state["status"] == "active"
                else "session-paused"
                if state["status"] == "paused"
                else "submit-next-bounded-plan"
            ),
        },
    }


def execute_one(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    session_id = request.get("session_id")
    if not isinstance(session_id, str) or not ID.fullmatch(session_id):
        raise SessionError("invalid development session id")
    with _session_lock(project, session_id):
        return _execute_one_locked(project, request)


def execute(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    if request.get("protocol_version") != PROTOCOL_VERSION:
        raise SessionError("request requires protocol_version=1")
    operation = request.get("operation")
    if operation not in OPERATIONS:
        raise SessionError(f"unsupported development-session operation: {operation}")
    project = _project(project)
    if operation == "capabilities":
        return capabilities()
    if operation == "create":
        return create(project, request)
    if operation == "inspect":
        return inspect(project, request)
    return execute_one(project, request)


def respond(project: Path, request: Any) -> dict[str, Any]:
    try:
        if not isinstance(request, dict):
            raise SessionError("request must be an object")
        return {"protocol_version": 1, **execute(project, request)}
    except (
        OSError,
        SessionError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
    ) as exc:
        return {
            "protocol_version": 1,
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
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
