#!/usr/bin/env python3
"""ARCONT 1.0 hardening checks. Stdlib-only."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

HEX40 = re.compile(r"^[0-9a-f]{40}$", re.I)
HEX64 = re.compile(r"^[0-9a-f]{64}$", re.I)
MATURITY = {
    "L0_UNKNOWN": 0,
    "L1_SOURCE_TRACED": 1,
    "L2_HYPOTHESIS": 2,
    "L3_OBSERVED": 3,
    "L4_REPRODUCED": 4,
    "L5_CROSS_HARDWARE": 5,
    "L6_CROSS_VERSION": 6,
    "L7_VALIDATED_RULE": 7,
}


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_manifest(repo: Path) -> list[str]:
    errors: list[str] = []
    path = repo / "arcont.manifest.json"
    if not path.exists():
        return ["missing arcont.manifest.json"]
    m = load_json(path)
    if m.get("arcont_version") != "1.0.0":
        errors.append("manifest: expected arcont_version 1.0.0")
    if m.get("production_game_code_allowed") is not False:
        errors.append("manifest: production_game_code_allowed must be false")
    if m.get("embedded_godot_project_allowed") is not False:
        errors.append("manifest: embedded_godot_project_allowed must be false")
    godot = m.get("engines", {}).get("godot", {})
    if godot.get("version") != "4.7.2-stable":
        errors.append("manifest: canonical Godot version mismatch")
    if not HEX40.fullmatch(str(godot.get("commit", ""))):
        errors.append("manifest: Godot commit must be 40 hex chars")
    for rel in [
        m.get("knowledge", {}).get("evidence_ledger"),
        m.get("knowledge", {}).get("maturity_model"),
        m.get("benchmarks", {}).get("result_schema"),
        m.get("integrity", {}).get("validator"),
        m.get("integrity", {}).get("hardening_validator"),
        m.get("integrity", {}).get("ci"),
    ]:
        if not rel or not (repo / rel).exists():
            errors.append(f"manifest: missing referenced path {rel!r}")
    return errors


def validate_result(obj: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["schema_version", "benchmark_id", "run_id", "engine", "platform", "runtime", "experiment", "metrics", "aborted"]:
        if key not in obj:
            errors.append(f"result: missing {key}")
    if obj.get("schema_version") != 1:
        errors.append("result: schema_version must be 1")
    engine = obj.get("engine") or {}
    for key in ["name", "version", "commit"]:
        if not engine.get(key):
            errors.append(f"result: engine.{key} required")
    if engine.get("commit") and not HEX40.fullmatch(str(engine["commit"])):
        errors.append("result: engine.commit invalid")
    if obj.get("aborted") is True and not obj.get("abort_reason"):
        errors.append("result: aborted run requires abort_reason")
    provenance = obj.get("provenance") or {}
    if provenance.get("harness_commit") is not None and not HEX40.fullmatch(str(provenance["harness_commit"])):
        errors.append("result: provenance.harness_commit invalid")
    for key in ["raw_data_sha256", "result_sha256"]:
        val = provenance.get(key)
        if val is not None and not HEX64.fullmatch(str(val)):
            errors.append(f"result: provenance.{key} invalid")
    return errors


def max_maturity(evidence: dict[str, Any]) -> int:
    if evidence.get("validated_rule"):
        return 7
    if evidence.get("engine_versions", 0) >= 2 and evidence.get("reproductions", 0) >= 2:
        return 6
    if evidence.get("hardware_profiles", 0) >= 2 and evidence.get("reproductions", 0) >= 2:
        return 5
    if evidence.get("reproductions", 0) >= 2:
        return 4
    if evidence.get("observations", 0) >= 1:
        return 3
    if evidence.get("hypothesis"):
        return 2
    if evidence.get("source_traced"):
        return 1
    return 0


def check_maturity(level: str, evidence: dict[str, Any]) -> list[str]:
    if level not in MATURITY:
        return [f"maturity: unknown level {level}"]
    allowed = max_maturity(evidence)
    actual = MATURITY[level]
    return [] if actual <= allowed else [f"maturity: {level} exceeds evidence ceiling L{allowed}"]


def cmd_validate(args: argparse.Namespace) -> int:
    repo = Path(args.root).resolve()
    errors = validate_manifest(repo)
    for p in repo.rglob("*.result.json"):
        try:
            errors.extend(f"{p.relative_to(repo)}: {e}" for e in validate_result(load_json(p)))
        except Exception as exc:
            errors.append(f"{p.relative_to(repo)}: invalid JSON: {exc}")
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


def cmd_result(args: argparse.Namespace) -> int:
    errors = validate_result(load_json(Path(args.file)))
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


def cmd_hash(args: argparse.Namespace) -> int:
    p = Path(args.file)
    print(json.dumps({"algorithm": "sha256", "digest": sha256(p), "bytes": p.stat().st_size, "artifact": str(p)}, indent=2))
    return 0


def cmd_maturity(args: argparse.Namespace) -> int:
    evidence = {
        "source_traced": args.source_traced,
        "hypothesis": args.hypothesis,
        "observations": args.observations,
        "reproductions": args.reproductions,
        "hardware_profiles": args.hardware_profiles,
        "engine_versions": args.engine_versions,
        "validated_rule": args.validated_rule,
    }
    errors = check_maturity(args.level, evidence)
    print(json.dumps({"ok": not errors, "errors": errors, "evidence_ceiling": max_maturity(evidence)}, indent=2))
    return 1 if errors else 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="arcont-hardening")
    sub = p.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--root", default=str(root()))
    v.set_defaults(func=cmd_validate)
    r = sub.add_parser("validate-result")
    r.add_argument("file")
    r.set_defaults(func=cmd_result)
    h = sub.add_parser("hash")
    h.add_argument("file")
    h.set_defaults(func=cmd_hash)
    m = sub.add_parser("maturity")
    m.add_argument("level", choices=sorted(MATURITY))
    m.add_argument("--source-traced", action="store_true")
    m.add_argument("--hypothesis", action="store_true")
    m.add_argument("--observations", type=int, default=0)
    m.add_argument("--reproductions", type=int, default=0)
    m.add_argument("--hardware-profiles", type=int, default=0)
    m.add_argument("--engine-versions", type=int, default=0)
    m.add_argument("--validated-rule", action="store_true")
    m.set_defaults(func=cmd_maturity)
    return p


if __name__ == "__main__":
    args = parser().parse_args()
    sys.exit(args.func(args))
