#!/usr/bin/env python3
"""Declarative observation -> hypothesis -> repair-plan compiler for ARCONT.

This module never executes a repair. It evaluates bounded policies against
structured evidence, selects at most one unambiguous candidate, and emits a
normal ARCONT execution plan for later explicit execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

POLICY_PROTOCOL = "arcont-agent-diagnosis-policy"
POLICY_VERSION = 1
PLAN_PROTOCOL = "arcont-agent-plan"
MAX_HYPOTHESES = 64
MAX_CONDITIONS = 32
MAX_FILTERS = 16
ID = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


class DiagnosisError(ValueError):
    pass


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def json_pointer(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise DiagnosisError("JSON pointer must be absolute")
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
            if index < 0 or index >= len(current):
                raise KeyError(pointer)
            current = current[index]
        else:
            raise KeyError(pointer)
    return current


def _ref(value: Any, evidence: Any, candidate: Any = None) -> tuple[bool, Any]:
    if isinstance(value, dict) and set(value) == {"$evidence"}:
        try:
            return True, json_pointer(evidence, value["$evidence"])
        except KeyError:
            return False, None
    if isinstance(value, dict) and set(value) == {"$candidate"}:
        if candidate is None:
            return False, None
        try:
            return True, json_pointer(candidate, value["$candidate"])
        except KeyError:
            return False, None
    return True, value


def evaluate_condition(condition: dict[str, Any], evidence: Any, candidate: Any = None) -> dict[str, Any]:
    if not isinstance(condition, dict) or set(condition) - {"left", "op", "right"}:
        raise DiagnosisError("invalid condition")
    if "left" not in condition or "op" not in condition:
        raise DiagnosisError("condition requires left and op")
    op = condition["op"]
    if op not in {"exists", "equals", "not-equals", "lt", "lte", "gt", "gte", "truthy", "falsy"}:
        raise DiagnosisError(f"unsupported condition operator: {op}")

    left_exists, left = _ref(condition["left"], evidence, candidate)
    right_exists, right = _ref(condition.get("right"), evidence, candidate)

    if op == "exists":
        ok = left_exists
    elif op == "truthy":
        ok = left_exists and bool(left)
    elif op == "falsy":
        ok = left_exists and not bool(left)
    elif op == "equals":
        ok = left_exists and right_exists and left == right
    elif op == "not-equals":
        ok = left_exists and right_exists and left != right
    else:
        if not left_exists or not right_exists:
            ok = False
        elif isinstance(left, bool) or isinstance(right, bool):
            ok = False
        elif not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            ok = False
        elif not math.isfinite(float(left)) or not math.isfinite(float(right)):
            ok = False
        elif op == "lt":
            ok = left < right
        elif op == "lte":
            ok = left <= right
        elif op == "gt":
            ok = left > right
        else:
            ok = left >= right

    return {
        "ok": ok,
        "op": op,
        "left_exists": left_exists,
        "left": left if left_exists else None,
        "right_exists": right_exists,
        "right": right if right_exists else None,
    }


def _validate_conditions(values: Any, label: str, maximum: int) -> list[dict[str, Any]]:
    if not isinstance(values, list) or len(values) > maximum:
        raise DiagnosisError(f"{label} must be an array with at most {maximum} entries")
    return values


def _vector3(value: Any) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) < 3:
        raise DiagnosisError("spatial selection requires a 3D vector")
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(float(x)) for x in value[:3]):
        raise DiagnosisError("spatial selection vector must contain finite numbers")
    return float(value[0]), float(value[1]), float(value[2])


def select_candidate(spec: dict[str, Any], evidence: Any) -> dict[str, Any]:
    allowed = {"source", "filters", "nearest_xz_to", "position_pointer", "max_distance", "stable_patch_prefix"}
    if not isinstance(spec, dict) or set(spec) - allowed:
        raise DiagnosisError("invalid candidate selector")
    source = spec.get("source")
    if not isinstance(source, str):
        raise DiagnosisError("candidate selector requires source pointer")
    try:
        candidates = json_pointer(evidence, source)
    except KeyError as exc:
        raise DiagnosisError(f"candidate source not found: {source}") from exc
    if not isinstance(candidates, list) or len(candidates) > 10000:
        raise DiagnosisError("candidate source must be a bounded array")

    filters = _validate_conditions(spec.get("filters", []), "candidate filters", MAX_FILTERS)
    eligible = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        checks = [evaluate_condition(rule, evidence, item) for rule in filters]
        if all(check["ok"] for check in checks):
            eligible.append((item, checks))
    if not eligible:
        raise DiagnosisError("candidate selector found no eligible candidates")

    target_ptr = spec.get("nearest_xz_to")
    if target_ptr is None:
        if len(eligible) != 1:
            raise DiagnosisError("candidate selector is ambiguous without spatial selection")
        candidate, checks = eligible[0]
        return {"candidate": candidate, "filters": checks, "distance_xz": None, "source": source,
                "stable_patch_prefix": spec.get("stable_patch_prefix")}

    if not isinstance(target_ptr, str):
        raise DiagnosisError("nearest_xz_to must be an evidence pointer")
    try:
        target = _vector3(json_pointer(evidence, target_ptr))
    except KeyError as exc:
        raise DiagnosisError(f"spatial target not found: {target_ptr}") from exc
    position_pointer = spec.get("position_pointer", "/position")
    if not isinstance(position_pointer, str):
        raise DiagnosisError("position_pointer must be a JSON pointer")
    ranked = []
    for item, checks in eligible:
        try:
            position = _vector3(json_pointer(item, position_pointer))
        except KeyError:
            continue
        distance = math.hypot(position[0] - target[0], position[2] - target[2])
        ranked.append((distance, item, checks))
    if not ranked:
        raise DiagnosisError("eligible candidates have no usable spatial position")
    ranked.sort(key=lambda row: row[0])
    best = ranked[0]
    max_distance = spec.get("max_distance")
    if max_distance is not None:
        if isinstance(max_distance, bool) or not isinstance(max_distance, (int, float)) or not math.isfinite(float(max_distance)) or max_distance < 0:
            raise DiagnosisError("max_distance must be a finite nonnegative number")
        if best[0] > float(max_distance):
            raise DiagnosisError("nearest candidate exceeds max_distance")
    if len(ranked) > 1 and abs(ranked[1][0] - best[0]) <= 1e-9:
        raise DiagnosisError("nearest candidate selection is ambiguous")
    return {
        "candidate": best[1],
        "filters": best[2],
        "distance_xz": best[0],
        "source": source,
        "stable_patch_prefix": spec.get("stable_patch_prefix"),
    }


def _escape_stable_id(identity: str) -> str:
    if not isinstance(identity, str) or not identity:
        raise DiagnosisError("selected candidate requires a non-empty id for stable patch paths")
    return identity.replace("~", "~0").replace("/", "~1")


def resolve_template(value: Any, evidence: Any, selection: dict[str, Any] | None) -> Any:
    candidate = selection["candidate"] if selection else None
    if isinstance(value, dict):
        if set(value) == {"$evidence"}:
            try:
                return json_pointer(evidence, value["$evidence"])
            except KeyError as exc:
                raise DiagnosisError(f"template evidence pointer not found: {value['$evidence']}") from exc
        if set(value) == {"$candidate"}:
            if candidate is None:
                raise DiagnosisError("template requires a selected candidate")
            try:
                return json_pointer(candidate, value["$candidate"])
            except KeyError as exc:
                raise DiagnosisError(f"template candidate pointer not found: {value['$candidate']}") from exc
        if set(value) == {"$candidate_path"}:
            if selection is None:
                raise DiagnosisError("candidate path requires a selected candidate")
            prefix = selection.get("stable_patch_prefix")
            if not isinstance(prefix, str) or not prefix.startswith("/"):
                raise DiagnosisError("candidate selector requires stable_patch_prefix")
            suffix = value["$candidate_path"]
            if not isinstance(suffix, str) or (suffix and not suffix.startswith("/")):
                raise DiagnosisError("$candidate_path suffix must be empty or an absolute pointer")
            identity = _escape_stable_id(candidate.get("id"))
            return prefix.rstrip("/") + "/@" + identity + suffix
        # Preserve execution-loop prior-step bindings verbatim.
        if set(value) == {"$from", "pointer"}:
            return dict(value)
        return {key: resolve_template(item, evidence, selection) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_template(item, evidence, selection) for item in value]
    return value


def validate_policy(policy: Any) -> dict[str, Any]:
    if not isinstance(policy, dict):
        raise DiagnosisError("policy must be an object")
    allowed = {"protocol", "version", "id", "description", "hypotheses"}
    if set(policy) - allowed:
        raise DiagnosisError("policy has unsupported top-level fields")
    if policy.get("protocol") != POLICY_PROTOCOL or policy.get("version") != POLICY_VERSION:
        raise DiagnosisError("unsupported diagnosis policy protocol/version")
    if not isinstance(policy.get("id"), str) or not ID.fullmatch(policy["id"]):
        raise DiagnosisError("policy requires a safe id")
    hypotheses = policy.get("hypotheses")
    if not isinstance(hypotheses, list) or not hypotheses or len(hypotheses) > MAX_HYPOTHESES:
        raise DiagnosisError(f"policy requires 1 to {MAX_HYPOTHESES} hypotheses")
    seen = set()
    for index, hypothesis in enumerate(hypotheses):
        if not isinstance(hypothesis, dict):
            raise DiagnosisError(f"hypotheses/{index} must be an object")
        allowed_h = {"id", "code", "summary", "priority", "when", "candidate", "require", "details", "repair_plan"}
        if set(hypothesis) - allowed_h:
            raise DiagnosisError(f"hypotheses/{index} has unsupported fields")
        ident = hypothesis.get("id")
        if not isinstance(ident, str) or not ID.fullmatch(ident) or ident in seen:
            raise DiagnosisError(f"hypotheses/{index} requires a unique safe id")
        seen.add(ident)
        if not isinstance(hypothesis.get("code"), str) or not hypothesis["code"]:
            raise DiagnosisError(f"hypotheses/{index} requires code")
        if not isinstance(hypothesis.get("summary"), str) or not hypothesis["summary"]:
            raise DiagnosisError(f"hypotheses/{index} requires summary")
        priority = hypothesis.get("priority", 0)
        if isinstance(priority, bool) or not isinstance(priority, int) or not -1000 <= priority <= 1000:
            raise DiagnosisError(f"hypotheses/{index} has invalid priority")
        _validate_conditions(hypothesis.get("when", []), "when", MAX_CONDITIONS)
        _validate_conditions(hypothesis.get("require", []), "require", MAX_CONDITIONS)
        if "candidate" in hypothesis and not isinstance(hypothesis["candidate"], dict):
            raise DiagnosisError(f"hypotheses/{index} candidate must be an object")
        if "repair_plan" in hypothesis and not isinstance(hypothesis["repair_plan"], dict):
            raise DiagnosisError(f"hypotheses/{index} repair_plan must be an object")
    return policy


def compile_repair_plan(template: dict[str, Any], evidence: Any, selection: dict[str, Any] | None) -> dict[str, Any]:
    resolved = resolve_template(template, evidence, selection)
    if not isinstance(resolved, dict):
        raise DiagnosisError("repair_plan template must resolve to an object")
    capability = resolved.get("capability")
    if not isinstance(capability, str) or not capability:
        raise DiagnosisError("repair_plan requires capability")
    plan_id = resolved.get("id")
    goal = resolved.get("goal")
    inspect_request = resolved.get("inspect_request")
    repair_request = resolved.get("repair_request")
    expect = resolved.get("expect", [])
    if not isinstance(plan_id, str) or not ID.fullmatch(plan_id):
        raise DiagnosisError("repair_plan requires safe id")
    if not isinstance(goal, str) or not goal:
        raise DiagnosisError("repair_plan requires goal")
    if not isinstance(inspect_request, dict) or inspect_request.get("protocol_version") != 1:
        raise DiagnosisError("repair_plan.inspect_request requires protocol_version=1")
    if not isinstance(repair_request, dict) or repair_request.get("protocol_version") != 1:
        raise DiagnosisError("repair_plan.repair_request requires protocol_version=1")
    if not isinstance(expect, list) or len(expect) > 16:
        raise DiagnosisError("repair_plan.expect must be a bounded array")
    return {
        "protocol": PLAN_PROTOCOL,
        "version": 1,
        "id": plan_id,
        "goal": goal,
        "permissions": {"project_write": True},
        "capability_allowlist": [capability],
        "steps": [
            {
                "id": "inspect_target",
                "kind": "invoke",
                "capability": capability,
                "request": inspect_request,
            },
            {
                "id": "apply_repair",
                "kind": "invoke",
                "capability": capability,
                "request": repair_request,
                "expect": expect,
            },
        ],
    }


def diagnose(policy: dict[str, Any], evidence: Any) -> dict[str, Any]:
    validate_policy(policy)
    if not isinstance(evidence, dict):
        raise DiagnosisError("evidence must be an object")

    evaluations = []
    matches = []
    for hypothesis in policy["hypotheses"]:
        when = [evaluate_condition(rule, evidence) for rule in hypothesis.get("when", [])]
        row = {"id": hypothesis["id"], "code": hypothesis["code"], "priority": hypothesis.get("priority", 0),
               "when": when, "matched": False}
        if not all(check["ok"] for check in when):
            evaluations.append(row)
            continue

        selection = None
        try:
            if "candidate" in hypothesis:
                selection = select_candidate(hypothesis["candidate"], evidence)
            require = [evaluate_condition(rule, evidence, selection["candidate"] if selection else None)
                       for rule in hypothesis.get("require", [])]
            row["require"] = require
            if not all(check["ok"] for check in require):
                evaluations.append(row)
                continue
            row["matched"] = True
            row["candidate"] = {
                "id": selection["candidate"].get("id") if selection else None,
                "distance_xz": selection.get("distance_xz") if selection else None,
            } if selection else None
            details = resolve_template(hypothesis.get("details", {}), evidence, selection)
            repair_plan = None
            if "repair_plan" in hypothesis:
                repair_plan = compile_repair_plan(hypothesis["repair_plan"], evidence, selection)
            match = {
                "id": hypothesis["id"],
                "code": hypothesis["code"],
                "summary": hypothesis["summary"],
                "priority": hypothesis.get("priority", 0),
                "candidate": selection["candidate"] if selection else None,
                "candidate_distance_xz": selection.get("distance_xz") if selection else None,
                "details": details,
                "repair_plan": repair_plan,
            }
            matches.append(match)
        except DiagnosisError as exc:
            row["candidate_error"] = str(exc)
        evaluations.append(row)

    if not matches:
        return {
            "schema_version": 1,
            "protocol": "arcont-agent-diagnosis",
            "ok": True,
            "matched": False,
            "status": "no-match",
            "policy_id": policy["id"],
            "policy_sha256": canonical_sha256(policy),
            "evidence_sha256": canonical_sha256(evidence),
            "evaluations": evaluations,
        }

    matches.sort(key=lambda item: (-item["priority"], item["id"]))
    top_priority = matches[0]["priority"]
    top = [item for item in matches if item["priority"] == top_priority]
    if len(top) != 1:
        return {
            "schema_version": 1,
            "protocol": "arcont-agent-diagnosis",
            "ok": False,
            "matched": False,
            "status": "ambiguous",
            "policy_id": policy["id"],
            "policy_sha256": canonical_sha256(policy),
            "evidence_sha256": canonical_sha256(evidence),
            "candidate_hypotheses": [{"id": item["id"], "code": item["code"], "priority": item["priority"]} for item in top],
            "evaluations": evaluations,
        }

    selected = top[0]
    return {
        "schema_version": 1,
        "protocol": "arcont-agent-diagnosis",
        "ok": True,
        "matched": True,
        "status": "diagnosed",
        "policy_id": policy["id"],
        "policy_sha256": canonical_sha256(policy),
        "evidence_sha256": canonical_sha256(evidence),
        "hypothesis": selected,
        "evaluations": evaluations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--evidence", default="-", help="evidence JSON path, or - for stdin")
    parser.add_argument("--require-match", action="store_true")
    args = parser.parse_args()
    try:
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
    except (OSError, json.JSONDecodeError, DiagnosisError, ValueError) as exc:
        print(json.dumps({"schema_version": 1, "protocol": "arcont-agent-diagnosis", "ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
