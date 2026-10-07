#!/usr/bin/env python3
"""Bounded deterministic execution plans for the ARCONT agent control plane."""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Callable

PLAN_PROTOCOL = "arcont-agent-plan"
PLAN_VERSION = 1
MAX_STEPS = 24
STEP_ID = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def json_pointer(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("binding/assertion pointer must be an RFC6901-style absolute JSON pointer")
    current = value
    for raw in pointer.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise KeyError(pointer)
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit():
                raise KeyError(pointer)
            index = int(token)
            if index >= len(current):
                raise KeyError(pointer)
            current = current[index]
        else:
            raise KeyError(pointer)
    return current


def resolve_bindings(value: Any, outputs: dict[str, Any], available_steps: set[str]) -> Any:
    if isinstance(value, dict):
        if set(value) == {"$from", "pointer"}:
            source = value.get("$from")
            pointer = value.get("pointer")
            if not isinstance(source, str) or source not in available_steps or source not in outputs:
                raise ValueError(f"binding references unavailable prior step: {source!r}")
            try:
                return json_pointer(outputs[source], pointer)
            except KeyError as exc:
                raise ValueError(f"binding pointer not found in step {source}: {pointer}") from exc
        return {key: resolve_bindings(item, outputs, available_steps) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_bindings(item, outputs, available_steps) for item in value]
    return value


def validate_plan(plan: Any, known_capabilities: set[str]) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise ValueError("plan must be an object")
    if plan.get("protocol") != PLAN_PROTOCOL or plan.get("version") != PLAN_VERSION:
        raise ValueError("unsupported agent plan protocol/version")
    plan_id = plan.get("id")
    if not isinstance(plan_id, str) or not STEP_ID.fullmatch(plan_id):
        raise ValueError("plan requires a safe id")
    goal = plan.get("goal")
    if not isinstance(goal, str) or not goal.strip() or len(goal) > 1000:
        raise ValueError("plan requires a non-empty bounded goal")

    permissions = plan.get("permissions", {})
    if not isinstance(permissions, dict) or set(permissions) - {"project_write"}:
        raise ValueError("permissions only supports project_write")
    if not isinstance(permissions.get("project_write", False), bool):
        raise ValueError("permissions.project_write must be boolean")

    allowlist = plan.get("capability_allowlist")
    if not isinstance(allowlist, list) or not allowlist or len(set(allowlist)) != len(allowlist):
        raise ValueError("capability_allowlist requires unique capability ids")
    if any(not isinstance(item, str) or item not in known_capabilities for item in allowlist):
        raise ValueError("capability_allowlist contains unknown capability")

    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps or len(steps) > MAX_STEPS:
        raise ValueError(f"steps requires 1 to {MAX_STEPS} entries")
    seen: set[str] = set()
    for index, step in enumerate(steps):
        path = f"steps/{index}"
        if not isinstance(step, dict):
            raise ValueError(f"{path}: requires object")
        if set(step) - {"id", "kind", "capability", "request", "max_files", "timeout_seconds", "expect"}:
            raise ValueError(f"{path}: unsupported fields")
        step_id = step.get("id")
        if not isinstance(step_id, str) or not STEP_ID.fullmatch(step_id) or step_id in seen:
            raise ValueError(f"{path}: invalid or duplicate id")
        seen.add(step_id)
        kind = step.get("kind")
        if kind not in {"inspect-project", "invoke"}:
            raise ValueError(f"{path}: unsupported kind")
        timeout = step.get("timeout_seconds", 120)
        if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 900:
            raise ValueError(f"{path}: timeout_seconds must be in [1,900]")
        if kind == "inspect-project":
            if step.get("capability") is not None or step.get("request") is not None:
                raise ValueError(f"{path}: inspect-project cannot include capability/request")
            max_files = step.get("max_files", 50000)
            if isinstance(max_files, bool) or not isinstance(max_files, int) or not 1 <= max_files <= 200000:
                raise ValueError(f"{path}: invalid max_files")
        else:
            capability = step.get("capability")
            if capability not in allowlist:
                raise ValueError(f"{path}: capability is not pre-authorized by capability_allowlist")
            if not isinstance(step.get("request"), dict):
                raise ValueError(f"{path}: invoke requires request object")
        expect = step.get("expect", [])
        if not isinstance(expect, list) or len(expect) > 16:
            raise ValueError(f"{path}: expect must be a bounded array")
        for assertion in expect:
            if not isinstance(assertion, dict) or set(assertion) - {"pointer", "op", "value"}:
                raise ValueError(f"{path}: invalid expectation")
            if not isinstance(assertion.get("pointer"), str) or not assertion["pointer"].startswith("/"):
                raise ValueError(f"{path}: expectation pointer required")
            if assertion.get("op") not in {"exists", "equals", "not-equals", "truthy", "falsy"}:
                raise ValueError(f"{path}: invalid expectation operator")
            if assertion.get("op") in {"equals", "not-equals"} and "value" not in assertion:
                raise ValueError(f"{path}: comparison expectation requires value")
    return plan


def evaluate_expectations(output: Any, expectations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for assertion in expectations:
        pointer = assertion["pointer"]
        op = assertion["op"]
        exists = True
        try:
            actual = json_pointer(output, pointer)
        except KeyError:
            exists = False
            actual = None
        expected = assertion.get("value")
        if op == "exists":
            ok = exists
        elif op == "equals":
            ok = exists and actual == expected
        elif op == "not-equals":
            ok = exists and actual != expected
        elif op == "truthy":
            ok = exists and bool(actual)
        else:
            ok = exists and not bool(actual)
        results.append({"pointer": pointer, "op": op, "expected": expected if "value" in assertion else None,
                        "actual": actual, "exists": exists, "ok": ok})
    return results


def execute_plan(
    root: Path,
    project: Path,
    plan: dict[str, Any],
    allow_project_write: bool,
    registry: dict[str, Any],
    inspect_fn: Callable[[Path, int], dict[str, Any]],
    invoke_fn: Callable[[Path, str, Path, dict[str, Any], bool, int], dict[str, Any]],
) -> dict[str, Any]:
    known = {
        item["id"]
        for item in registry.get("capabilities", [])
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and item.get("invocable") is True
        and item.get("access") == "external-project-write"
    }
    validate_plan(plan, known)

    plan_permission = plan.get("permissions", {}).get("project_write", False)
    has_invoke = any(step.get("kind") == "invoke" for step in plan["steps"])
    if has_invoke and not plan_permission:
        raise PermissionError("plans with invoke steps require permissions.project_write=true")
    if plan_permission and not allow_project_write:
        raise PermissionError("plan requests project_write but CLI permission was not granted")

    project = Path(project).resolve()
    root = Path(root).resolve()
    if not project.is_dir():
        raise FileNotFoundError(f"project root is not a directory: {project}")
    if project == root or root in project.parents:
        raise ValueError("refusing to execute a plan against ARCONT itself or an embedded project")

    registry_hash = canonical_sha256(registry)
    plan_hash = canonical_sha256(plan)
    outputs: dict[str, Any] = {}
    receipts = []
    completed: set[str] = set()
    write_steps = 0
    started = time.monotonic()

    for index, step in enumerate(plan["steps"]):
        step_started = time.monotonic()
        step_id = step["id"]
        try:
            if step["kind"] == "inspect-project":
                output = inspect_fn(project, step.get("max_files", 50000))
            else:
                request = resolve_bindings(step["request"], outputs, completed)
                if request.get("protocol_version") != 1:
                    raise ValueError(f"{step_id}: resolved invoke request requires protocol_version=1")
                output = invoke_fn(
                    root,
                    step["capability"],
                    project,
                    request,
                    allow_project_write and plan_permission,
                    step.get("timeout_seconds", 120),
                )
            expectations = evaluate_expectations(output, step.get("expect", []))
            execution_ok = isinstance(output, dict) and output.get("ok") is True
            expectations_ok = all(item["ok"] for item in expectations)
            ok = execution_ok and expectations_ok
            if isinstance(output, dict):
                nested = output.get("result") if isinstance(output.get("result"), dict) else {}
                write_performed = bool(
                    output.get("write_performed")
                    or output.get("committed")
                    or nested.get("write_performed")
                    or nested.get("committed")
                )
            else:
                write_performed = False
            if write_performed:
                write_steps += 1
            receipt = {
                "index": index,
                "id": step_id,
                "kind": step["kind"],
                "capability": step.get("capability"),
                "ok": ok,
                "execution_ok": execution_ok,
                "expectations_ok": expectations_ok,
                "expectations": expectations,
                "write_performed": write_performed,
                "duration_ms": round((time.monotonic() - step_started) * 1000, 3),
                "output": output,
            }
            receipts.append(receipt)
            outputs[step_id] = output
            completed.add(step_id)
            if not ok:
                return {
                    "schema_version": 1,
                    "protocol": PLAN_PROTOCOL,
                    "operation": "run-plan",
                    "ok": False,
                    "status": "stopped",
                    "failed_step": step_id,
                    "plan_id": plan["id"],
                    "goal": plan["goal"],
                    "plan_sha256": plan_hash,
                    "registry_sha256": registry_hash,
                    "project": str(project),
                    "steps_completed": len(receipts),
                    "write_steps": write_steps,
                    "duration_ms": round((time.monotonic() - started) * 1000, 3),
                    "steps": receipts,
                }
        except Exception as exc:
            receipts.append({
                "index": index,
                "id": step_id,
                "kind": step["kind"],
                "capability": step.get("capability"),
                "ok": False,
                "error": str(exc),
                "write_performed": False,
                "duration_ms": round((time.monotonic() - step_started) * 1000, 3),
            })
            return {
                "schema_version": 1,
                "protocol": PLAN_PROTOCOL,
                "operation": "run-plan",
                "ok": False,
                "status": "error",
                "failed_step": step_id,
                "plan_id": plan["id"],
                "goal": plan["goal"],
                "plan_sha256": plan_hash,
                "registry_sha256": registry_hash,
                "project": str(project),
                "steps_completed": len(receipts),
                "write_steps": write_steps,
                "duration_ms": round((time.monotonic() - started) * 1000, 3),
                "steps": receipts,
            }

    return {
        "schema_version": 1,
        "protocol": PLAN_PROTOCOL,
        "operation": "run-plan",
        "ok": True,
        "status": "completed",
        "plan_id": plan["id"],
        "goal": plan["goal"],
        "plan_sha256": plan_hash,
        "registry_sha256": registry_hash,
        "project": str(project),
        "steps_completed": len(receipts),
        "write_steps": write_steps,
        "duration_ms": round((time.monotonic() - started) * 1000, 3),
        "steps": receipts,
    }
