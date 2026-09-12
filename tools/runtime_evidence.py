#!/usr/bin/env python3
"""ARCONT runtime-evidence bridge.

This tool does not run Godot. It validates machine-readable benchmark plans,
emits a runner-facing manifest for one benchmark, and validates externally
produced result files against the canonical campaign before they can be treated
as ARCONT runtime evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from tools.arcont_hardening import HEX40, HEX64, validate_result
    from tools.arcont_lab import load_all_graphs
except ModuleNotFoundError:
    from arcont_hardening import HEX40, HEX64, validate_result
    from arcont_lab import load_all_graphs

CANONICAL_VERSION = "4.7.2-stable"
CANONICAL_COMMIT = "ed1daf0bf001b61586d9930840f2f1394092c079"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_plan(root: Path) -> Path:
    return root / "docs" / "benchmarks" / "FIRST_RUNTIME_MATRIX.json"


def validate_plan(plan: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    if plan.get("schema_version") != 1:
        errors.append("plan: schema_version must be 1")
    campaign_id = plan.get("campaign_id")
    if not isinstance(campaign_id, str) or not campaign_id.startswith("ARC-CAMPAIGN-"):
        errors.append("plan: campaign_id must start ARC-CAMPAIGN-")

    engine = plan.get("engine") or {}
    if engine.get("name") != "godot":
        errors.append("plan: engine.name must be godot")
    if engine.get("version") != CANONICAL_VERSION:
        errors.append("plan: engine.version does not match canonical Godot pin")
    if engine.get("commit") != CANONICAL_COMMIT:
        errors.append("plan: engine.commit does not match canonical Godot pin")

    graph_nodes, _ = load_all_graphs(root)
    benchmarks = plan.get("benchmarks")
    if not isinstance(benchmarks, list) or not benchmarks:
        return errors + ["plan: benchmarks must be a non-empty list"]

    seen: set[str] = set()
    for idx, bench in enumerate(benchmarks):
        prefix = f"plan.benchmarks[{idx}]"
        if not isinstance(bench, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        bid = bench.get("id")
        if not isinstance(bid, str) or not bid.startswith("ARC-BENCH-"):
            errors.append(f"{prefix}: id must start ARC-BENCH-")
        elif bid in seen:
            errors.append(f"{prefix}: duplicate benchmark id {bid}")
        else:
            seen.add(bid)

        hyp = bench.get("hypothesis_ref")
        if not isinstance(hyp, str) or hyp not in graph_nodes:
            errors.append(f"{prefix}: hypothesis_ref {hyp!r} is not a Knowledge Graph node")
        refs = bench.get("knowledge_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{prefix}: knowledge_refs must be non-empty")
        else:
            for ref in refs:
                if ref not in graph_nodes:
                    errors.append(f"{prefix}: knowledge_ref {ref!r} is not a Knowledge Graph node")

        sweep = bench.get("sweep")
        if not isinstance(sweep, list) or not sweep:
            errors.append(f"{prefix}: sweep must be non-empty")
        elif any(not isinstance(v, int) or v < 0 for v in sweep):
            errors.append(f"{prefix}: sweep values must be non-negative integers")
        elif sweep != sorted(set(sweep)):
            errors.append(f"{prefix}: sweep must be unique and ascending")

        if not isinstance(bench.get("repetitions"), int) or bench.get("repetitions", 0) < 2:
            errors.append(f"{prefix}: repetitions must be >= 2")
        for field in ("warmup_seconds", "sample_seconds"):
            value = bench.get(field)
            if not isinstance(value, (int, float)) or value < 0 or (field == "sample_seconds" and value == 0):
                errors.append(f"{prefix}: invalid {field}")
        metrics = bench.get("metrics")
        if not isinstance(metrics, list) or not metrics or any(not isinstance(m, str) or not m for m in metrics):
            errors.append(f"{prefix}: metrics must be a non-empty string list")
        abort = bench.get("abort")
        if not isinstance(abort, dict) or not abort:
            errors.append(f"{prefix}: abort policy is required")
    return errors


def benchmark_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {b["id"]: b for b in plan.get("benchmarks", []) if isinstance(b, dict) and isinstance(b.get("id"), str)}


def runner_manifest(plan: dict[str, Any], benchmark_id: str) -> dict[str, Any]:
    benches = benchmark_map(plan)
    if benchmark_id not in benches:
        raise KeyError(benchmark_id)
    bench = benches[benchmark_id]
    return {
        "schema_version": 1,
        "campaign_id": plan["campaign_id"],
        "benchmark": bench,
        "engine": plan["engine"],
        "runner_requirements": {
            "record_platform": ["os", "device", "cpu", "gpu"],
            "record_runtime": ["renderer", "resolution", "build_type", "vsync"],
            "raw_samples_required": True,
            "raw_data_sha256_required": True,
            "harness_commit_required": True,
            "clock": "monotonic",
            "interpretation_in_runner": False
        }
    }


def validate_against_plan(result: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    errors = list(validate_result(result))
    benches = benchmark_map(plan)
    bid = result.get("benchmark_id")
    if bid not in benches:
        errors.append(f"result: benchmark_id {bid!r} is not registered in the canonical campaign")
        return errors
    bench = benches[bid]

    engine = result.get("engine") or {}
    if engine != plan.get("engine"):
        errors.append("result: engine identity must exactly match campaign engine pin")

    platform = result.get("platform") or {}
    for key in ("os", "device", "cpu", "gpu"):
        if not platform.get(key):
            errors.append(f"result: platform.{key} required for runtime evidence")
    runtime = result.get("runtime") or {}
    for key in ("renderer", "resolution", "build_type", "vsync"):
        if key not in runtime or runtime.get(key) in (None, ""):
            errors.append(f"result: runtime.{key} required for runtime evidence")

    experiment = result.get("experiment") or {}
    if experiment.get("hypothesis_ref") != bench.get("hypothesis_ref"):
        errors.append("result: experiment.hypothesis_ref does not match benchmark plan")
    if experiment.get("variable") != bench.get("variable"):
        errors.append("result: experiment.variable does not match benchmark plan")
    if experiment.get("value") not in bench.get("sweep", []):
        errors.append("result: experiment.value is outside benchmark sweep")
    repetition = experiment.get("repetition")
    if not isinstance(repetition, int) or repetition < 1 or repetition > bench.get("repetitions", 0):
        errors.append("result: experiment.repetition outside planned range")
    if experiment.get("warmup_seconds") != bench.get("warmup_seconds"):
        errors.append("result: warmup_seconds differs from preregistered plan")
    if experiment.get("sample_seconds") != bench.get("sample_seconds"):
        errors.append("result: sample_seconds differs from preregistered plan")

    metrics = result.get("metrics") or {}
    if not result.get("aborted"):
        for metric in bench.get("metrics", []):
            if metric not in metrics:
                errors.append(f"result: planned metric {metric!r} missing")

    provenance = result.get("provenance") or {}
    if not result.get("aborted"):
        if not HEX40.fullmatch(str(provenance.get("harness_commit", ""))):
            errors.append("result: valid provenance.harness_commit required")
        if not HEX64.fullmatch(str(provenance.get("raw_data_sha256", ""))):
            errors.append("result: valid provenance.raw_data_sha256 required")
    return errors


def cmd_validate_plan(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    plan = load_json(Path(args.plan))
    errors = validate_plan(plan, root)
    print(json.dumps({"ok": not errors, "errors": errors, "benchmarks": len(plan.get("benchmarks", []))}, indent=2))
    return 1 if errors else 0


def cmd_manifest(args: argparse.Namespace) -> int:
    plan = load_json(Path(args.plan))
    try:
        manifest = runner_manifest(plan, args.benchmark)
    except KeyError:
        print(json.dumps({"ok": False, "error": f"unknown benchmark {args.benchmark}"}, indent=2))
        return 1
    print(json.dumps(manifest, indent=2))
    return 0


def cmd_validate_result(args: argparse.Namespace) -> int:
    plan = load_json(Path(args.plan))
    result = load_json(Path(args.result))
    errors = validate_against_plan(result, plan)
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


def parser() -> argparse.ArgumentParser:
    root = repo_root()
    default_plan = str(canonical_plan(root))
    p = argparse.ArgumentParser(prog="arcont-runtime-evidence")
    sub = p.add_subparsers(dest="command", required=True)

    vp = sub.add_parser("validate-plan")
    vp.add_argument("--root", default=str(root))
    vp.add_argument("--plan", default=default_plan)
    vp.set_defaults(func=cmd_validate_plan)

    em = sub.add_parser("emit-manifest")
    em.add_argument("benchmark")
    em.add_argument("--plan", default=default_plan)
    em.set_defaults(func=cmd_manifest)

    vr = sub.add_parser("validate-result")
    vr.add_argument("result")
    vr.add_argument("--plan", default=default_plan)
    vr.set_defaults(func=cmd_validate_result)
    return p


if __name__ == "__main__":
    args = parser().parse_args()
    sys.exit(args.func(args))
