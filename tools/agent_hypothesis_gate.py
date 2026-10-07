#!/usr/bin/env python3
"""Safety gate for model-authored ARCONT hypothesis proposals.

A model may propose a novel diagnosis against structured evidence, but it does
not get to emit an arbitrary execution plan. This gate validates a narrow
proposal language and compiles it into an ordinary diagnosis policy. The
existing diagnosis engine then selects the hypothesis/candidate and compiles the
revision-checked repair plan.

V1 intentionally supports one repair primitive:
  map-forge-stable-object-patch

The gate is read-only and never executes the compiled repair.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from tools.agent_diagnosis import DiagnosisError, canonical_sha256, diagnose, validate_policy
except ModuleNotFoundError:
    from agent_diagnosis import DiagnosisError, canonical_sha256, diagnose, validate_policy


PROPOSAL_PROTOCOL = "arcont-agent-hypothesis-proposal"
PROPOSAL_VERSION = 1
ID = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
SAFE_POINTER = re.compile(r"^/(?:[^/~]|~[01])(?:[^/]|/(?:[^/~]|~[01]))*$")
MAX_WHEN = 24
MAX_FILTERS = 16
MAX_REQUIRE = 24
MAX_CHANGES = 8
MAX_DISTANCE = 1000.0
ALLOWED_REPAIR_KIND = "map-forge-stable-object-patch"
ALLOWED_CAPABILITY = "map-forge.editor.control"
STABLE_PATCH_PREFIX = "/map/authoring/objects"
CONDITION_OPS = {"exists", "equals", "not-equals", "lt", "lte", "gt", "gte", "truthy", "falsy"}


class ProposalError(ValueError):
    pass


def _safe_pointer(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("/") or len(value) > 256:
        raise ProposalError(f"{label} must be an absolute JSON pointer <=256 chars")
    # JSON Pointer has no parent traversal semantics, but prohibit stable-ID and
    # obvious path-injection syntax from model-authored suffixes.
    if "@" in value or ".." in value or not SAFE_POINTER.fullmatch(value):
        raise ProposalError(f"{label} is not a safe JSON pointer")
    return value


def _reference(value: Any, label: str, *, allow_candidate: bool) -> dict[str, str]:
    if not isinstance(value, dict) or len(value) != 1:
        raise ProposalError(f"{label} must be a single evidence reference")
    if "$evidence" in value:
        return {"$evidence": _safe_pointer(value["$evidence"], f"{label}.$evidence")}
    if allow_candidate and "$candidate" in value:
        return {"$candidate": _safe_pointer(value["$candidate"], f"{label}.$candidate")}
    raise ProposalError(f"{label} uses an unsupported reference")


def _operand(value: Any, label: str, *, allow_candidate: bool = True) -> Any:
    if isinstance(value, dict):
        return _reference(value, label, allow_candidate=allow_candidate)
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise ProposalError(f"{label} must be a scalar or evidence/candidate reference")


def _conditions(values: Any, label: str, maximum: int, *, allow_candidate: bool) -> list[dict[str, Any]]:
    if not isinstance(values, list) or len(values) > maximum:
        raise ProposalError(f"{label} must be an array with at most {maximum} entries")
    result = []
    for index, item in enumerate(values):
        if not isinstance(item, dict) or set(item) - {"left", "op", "right"}:
            raise ProposalError(f"{label}/{index} is invalid")
        if "left" not in item or "op" not in item:
            raise ProposalError(f"{label}/{index} requires left and op")
        op = item["op"]
        if op not in CONDITION_OPS:
            raise ProposalError(f"{label}/{index} uses unsupported operator {op!r}")
        row = {
            "left": _operand(item["left"], f"{label}/{index}/left", allow_candidate=allow_candidate),
            "op": op,
        }
        if op not in {"exists", "truthy", "falsy"}:
            if "right" not in item:
                raise ProposalError(f"{label}/{index} requires right for {op}")
            row["right"] = _operand(item["right"], f"{label}/{index}/right", allow_candidate=allow_candidate)
        elif "right" in item:
            raise ProposalError(f"{label}/{index} must not provide right for {op}")
        result.append(row)
    return result


def _template(value: Any, label: str) -> Any:
    if isinstance(value, dict):
        if len(value) == 1 and ("$evidence" in value or "$candidate" in value):
            return _reference(value, label, allow_candidate=True)
        return {str(key): _template(item, f"{label}/{key}") for key, item in value.items()}
    if isinstance(value, list):
        if len(value) > 64:
            raise ProposalError(f"{label} list is too large")
        return [_template(item, f"{label}/{index}") for index, item in enumerate(value)]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise ProposalError(f"{label} contains unsupported value type")


def _repair_value(value: Any, label: str) -> Any:
    if isinstance(value, dict):
        # Repair values may be grounded in evidence, but never copied blindly
        # from the faulty candidate.
        return _reference(value, label, allow_candidate=False)
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise ProposalError(f"{label} must be a scalar or evidence reference")


def validate_proposal(proposal: Any) -> dict[str, Any]:
    if not isinstance(proposal, dict):
        raise ProposalError("proposal must be an object")
    allowed = {"protocol", "version", "id", "goal", "hypothesis", "provenance"}
    if set(proposal) - allowed:
        raise ProposalError("proposal has unsupported top-level fields")
    if proposal.get("protocol") != PROPOSAL_PROTOCOL or proposal.get("version") != PROPOSAL_VERSION:
        raise ProposalError("unsupported hypothesis proposal protocol/version")
    if not isinstance(proposal.get("id"), str) or not ID.fullmatch(proposal["id"]):
        raise ProposalError("proposal requires a safe id")
    if not isinstance(proposal.get("goal"), str) or not proposal["goal"].strip() or len(proposal["goal"]) > 500:
        raise ProposalError("proposal requires a non-empty goal <=500 chars")

    provenance = proposal.get("provenance", {})
    if not isinstance(provenance, dict) or set(provenance) - {"author_type", "model", "note"}:
        raise ProposalError("invalid proposal provenance")
    if provenance:
        if provenance.get("author_type") not in {"model", "human", "hybrid"}:
            raise ProposalError("provenance.author_type must be model, human or hybrid")
        for key in ("model", "note"):
            if key in provenance and (not isinstance(provenance[key], str) or len(provenance[key]) > 500):
                raise ProposalError(f"invalid provenance.{key}")

    hypothesis = proposal.get("hypothesis")
    if not isinstance(hypothesis, dict):
        raise ProposalError("proposal requires hypothesis")
    allowed_h = {"id", "code", "summary", "priority", "when", "candidate", "require", "details", "repair"}
    if set(hypothesis) - allowed_h:
        raise ProposalError("hypothesis has unsupported fields")
    if not isinstance(hypothesis.get("id"), str) or not ID.fullmatch(hypothesis["id"]):
        raise ProposalError("hypothesis requires a safe id")
    for key in ("code", "summary"):
        if not isinstance(hypothesis.get(key), str) or not hypothesis[key].strip() or len(hypothesis[key]) > 500:
            raise ProposalError(f"hypothesis requires non-empty {key} <=500 chars")
    priority = hypothesis.get("priority", 0)
    if isinstance(priority, bool) or not isinstance(priority, int) or not -1000 <= priority <= 1000:
        raise ProposalError("hypothesis priority must be an integer in [-1000,1000]")

    when = _conditions(hypothesis.get("when", []), "hypothesis.when", MAX_WHEN, allow_candidate=False)
    if not when:
        raise ProposalError("model-authored hypothesis requires at least one evidence precondition")

    candidate = hypothesis.get("candidate")
    if not isinstance(candidate, dict):
        raise ProposalError("hypothesis requires a candidate selector")
    allowed_c = {"source", "filters", "nearest_xz_to", "position_pointer", "max_distance"}
    if set(candidate) - allowed_c:
        raise ProposalError("candidate selector has unsupported fields")
    source = _safe_pointer(candidate.get("source"), "candidate.source")
    filters = _conditions(candidate.get("filters", []), "candidate.filters", MAX_FILTERS, allow_candidate=True)
    if not filters:
        raise ProposalError("candidate selector requires at least one filter")
    nearest = _safe_pointer(candidate.get("nearest_xz_to"), "candidate.nearest_xz_to")
    position_pointer = _safe_pointer(candidate.get("position_pointer", "/position"), "candidate.position_pointer")
    max_distance = candidate.get("max_distance")
    if isinstance(max_distance, bool) or not isinstance(max_distance, (int, float)) or not 0 < float(max_distance) <= MAX_DISTANCE:
        raise ProposalError(f"candidate.max_distance must be in (0,{MAX_DISTANCE}]")

    require = _conditions(hypothesis.get("require", []), "hypothesis.require", MAX_REQUIRE, allow_candidate=True)
    if not require:
        raise ProposalError("model-authored repair requires at least one candidate/evidence requirement")

    details = _template(hypothesis.get("details", {}), "hypothesis.details")
    repair = hypothesis.get("repair")
    if not isinstance(repair, dict):
        raise ProposalError("hypothesis requires repair")
    allowed_r = {"kind", "map_id", "changes"}
    if set(repair) - allowed_r:
        raise ProposalError("repair has unsupported fields")
    if repair.get("kind") != ALLOWED_REPAIR_KIND:
        raise ProposalError(f"unsupported repair kind: {repair.get('kind')!r}")
    map_id = _reference(repair.get("map_id"), "repair.map_id", allow_candidate=False)

    changes = repair.get("changes")
    if not isinstance(changes, list) or not 1 <= len(changes) <= MAX_CHANGES:
        raise ProposalError(f"repair.changes requires 1 to {MAX_CHANGES} entries")
    normalized_changes = []
    seen = set()
    for index, change in enumerate(changes):
        if not isinstance(change, dict) or set(change) != {"candidate_pointer", "value"}:
            raise ProposalError(f"repair.changes/{index} must contain candidate_pointer and value only")
        pointer = _safe_pointer(change["candidate_pointer"], f"repair.changes/{index}/candidate_pointer")
        if pointer in seen:
            raise ProposalError(f"duplicate repair candidate_pointer: {pointer}")
        seen.add(pointer)
        normalized_changes.append({
            "candidate_pointer": pointer,
            "value": _repair_value(change["value"], f"repair.changes/{index}/value"),
        })

    return {
        "protocol": PROPOSAL_PROTOCOL,
        "version": PROPOSAL_VERSION,
        "id": proposal["id"],
        "goal": proposal["goal"],
        "provenance": provenance,
        "hypothesis": {
            "id": hypothesis["id"],
            "code": hypothesis["code"],
            "summary": hypothesis["summary"],
            "priority": priority,
            "when": when,
            "candidate": {
                "source": source,
                "filters": filters,
                "nearest_xz_to": nearest,
                "position_pointer": position_pointer,
                "max_distance": float(max_distance),
            },
            "require": require,
            "details": details,
            "repair": {
                "kind": ALLOWED_REPAIR_KIND,
                "map_id": map_id,
                "changes": normalized_changes,
            },
        },
    }


def compile_policy(proposal: dict[str, Any]) -> dict[str, Any]:
    proposal = validate_proposal(proposal)
    h = proposal["hypothesis"]
    repair = h["repair"]
    patch = []
    for change in repair["changes"]:
        pointer = change["candidate_pointer"]
        patch.append({
            "op": "test",
            "path": {"$candidate_path": pointer},
            "value": {"$candidate": pointer},
        })
        patch.append({
            "op": "replace",
            "path": {"$candidate_path": pointer},
            "value": change["value"],
        })

    policy = {
        "protocol": "arcont-agent-diagnosis-policy",
        "version": 1,
        "id": proposal["id"],
        "description": f"Compiled from model/human proposal {proposal['id']}",
        "hypotheses": [
            {
                "id": h["id"],
                "code": h["code"],
                "summary": h["summary"],
                "priority": h["priority"],
                "when": h["when"],
                "candidate": {
                    **h["candidate"],
                    "stable_patch_prefix": STABLE_PATCH_PREFIX,
                },
                "require": h["require"],
                "details": h["details"],
                "repair_plan": {
                    "id": f"repair_{h['id']}"[:64],
                    "goal": proposal["goal"],
                    "capability": ALLOWED_CAPABILITY,
                    "inspect_request": {
                        "protocol_version": 1,
                        "operation": "inspect",
                        "map_id": repair["map_id"],
                    },
                    "repair_request": {
                        "protocol_version": 1,
                        "operation": "patch",
                        "map_id": repair["map_id"],
                        "if_revision": {"$from": "inspect_target", "pointer": "/result/revision"},
                        "dry_run": False,
                        "patch": patch,
                    },
                    "expect": [
                        {"pointer": "/result/committed", "op": "equals", "value": True},
                        {"pointer": "/result/revision", "op": "exists"},
                    ],
                },
            }
        ],
    }
    validate_policy(policy)
    return policy


def evaluate_proposal(proposal: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    normalized = validate_proposal(proposal)
    policy = compile_policy(normalized)
    diagnosis = diagnose(policy, evidence)
    return {
        "schema_version": 1,
        "protocol": "arcont-agent-hypothesis-gate",
        "ok": diagnosis.get("ok") is True,
        "proposal_id": normalized["id"],
        "proposal_sha256": canonical_sha256(normalized),
        "compiled_policy_sha256": canonical_sha256(policy),
        "provenance": normalized.get("provenance", {}),
        "repair_primitive": ALLOWED_REPAIR_KIND,
        "diagnosis": diagnosis,
        "limits": [
            "Read-only gate: the compiled repair is never executed here.",
            "V1 permits only stable-object Map Forge replace operations guarded by current-value tests.",
            "Repair values must be scalar literals or structured evidence references, never arbitrary code or candidate-derived replacement values.",
            "Execution still requires a separate run-plan call with explicit project-write permission.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--evidence", default="-", help="evidence JSON path, or - for stdin")
    parser.add_argument("--require-match", action="store_true")
    parser.add_argument("--emit-policy", help="optional path to write the validated compiled diagnosis policy")
    args = parser.parse_args()
    try:
        proposal = json.loads(Path(args.proposal).read_text(encoding="utf-8"))
        raw = sys.stdin.read() if args.evidence == "-" else Path(args.evidence).read_text(encoding="utf-8")
        evidence = json.loads(raw)
        if not isinstance(evidence, dict):
            raise ProposalError("evidence must be an object")
        report = evaluate_proposal(proposal, evidence)
        if args.emit_policy:
            policy = compile_policy(proposal)
            Path(args.emit_policy).write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        if not report["ok"]:
            return 1
        if args.require_match and not report["diagnosis"].get("matched"):
            return 1
        return 0
    except (OSError, json.JSONDecodeError, ProposalError, DiagnosisError, ValueError) as exc:
        print(json.dumps({
            "schema_version": 1,
            "protocol": "arcont-agent-hypothesis-gate",
            "ok": False,
            "error": str(exc),
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
