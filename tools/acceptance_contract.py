"""Typed acceptance criteria, pinned at session creation rather than completion."""
from typing import Any
try:
    from tools.agent_execution_loop import evaluate_expectations
except ModuleNotFoundError:
    from agent_execution_loop import evaluate_expectations


def validate_criterion(value: Any):
    # Legacy prose remains readable, but cannot certify a completed milestone.
    if isinstance(value, str) and value.strip() and len(value) <= 500:
        return value
    if not isinstance(value, dict) or set(value) != {"description", "verification_level", "checks"}:
        raise ValueError("acceptance requires description, verification_level and checks")
    if not isinstance(value["description"], str) or not 1 <= len(value["description"].strip()) <= 500:
        raise ValueError("invalid acceptance description")
    if value["verification_level"] not in {"static", "runtime"}:
        raise ValueError("verification_level must be static or runtime")
    checks = value["checks"]
    if not isinstance(checks, list) or not 1 <= len(checks) <= 8:
        raise ValueError("acceptance requires 1..8 typed checks")
    for check in checks:
        if not isinstance(check, dict) or set(check) - {"kind", "capability", "operation", "request_match", "expect"}:
            raise ValueError("invalid acceptance check fields")
        if check.get("kind") not in {"inspect-project", "invoke"}:
            raise ValueError("acceptance check kind required")
        if check["kind"] == "invoke":
            if not all(isinstance(check.get(k), str) and check[k] for k in ("capability", "operation")):
                raise ValueError("invoke acceptance requires capability and operation")
            if not isinstance(check.get("request_match", {}), dict):
                raise ValueError("request_match must be an object")
        elif set(check) - {"kind", "expect"}:
            raise ValueError("inventory acceptance cannot select a capability")
        expectations = check.get("expect")
        if not isinstance(expectations, list) or not 1 <= len(expectations) <= 16:
            raise ValueError("acceptance must declare 1..16 result predicates")
        for assertion in expectations:
            if (not isinstance(assertion, dict) or set(assertion) - {"pointer", "op", "value"}
                    or not isinstance(assertion.get("pointer"), str) or not assertion["pointer"].startswith("/")
                    or assertion.get("op") not in {"exists", "equals", "not-equals", "truthy", "falsy"}
                    or assertion.get("op") in {"equals", "not-equals"} and "value" not in assertion):
                raise ValueError("invalid acceptance result predicate")
        if value["verification_level"] == "runtime":
            if check.get("capability") != "godot.authoring.control" or check.get("operation") != "playtest":
                raise ValueError("runtime acceptance requires the trusted playtest capability")
            if {"pointer": "/result/passed", "op": "equals", "value": True} not in expectations:
                raise ValueError("runtime acceptance must require passed=true")
    return value


def _contains(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and _contains(actual[k], v) for k, v in expected.items())
    return type(actual) is type(expected) and actual == expected


def verify_criterion(criterion, steps):
    if isinstance(criterion, str):
        return False, []
    covered = set()
    reports = []
    for step in steps:
        matches = []
        if isinstance(step, dict) and step.get("ok") is True:
            for index, check in enumerate(criterion["checks"]):
                if step.get("kind") != check["kind"]:
                    continue
                if check["kind"] == "invoke":
                    request = step.get("resolved_request", {})
                    if (step.get("capability") != check["capability"] or request.get("operation") != check["operation"]
                            or not _contains(request, check.get("request_match", {}))):
                        continue
                evaluated = evaluate_expectations(step.get("output"), check["expect"])
                for report, assertion in zip(evaluated, check["expect"]):
                    if assertion["op"] == "equals" and isinstance(assertion.get("value"), bool):
                        report["ok"] = report["ok"] and type(report["actual"]) is bool
                if all(row["ok"] for row in evaluated):
                    matches.append(index)
                    covered.add(index)
        reports.append({"step_id": step.get("id") if isinstance(step, dict) else None,
                        "matching_checks": matches, "evidence_ok": bool(matches)})
    return len(covered) == len(criterion["checks"]) and all(r["evidence_ok"] for r in reports), reports
