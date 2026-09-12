#!/usr/bin/env python3
"""Unified ARCONT evidence ingestion kernel.

All measurement providers are adapted into one deterministic evidence bundle.
The adapter never promotes claim maturity; it only normalizes measurements and
preserves provenance. Stdlib-only so it can run in CI and the Runtime Lab.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

HEX40 = re.compile(r"^[0-9a-f]{40}$", re.I)
HEX64 = re.compile(r"^[0-9a-f]{64}$", re.I)
CEILINGS = {"L1_SOURCE_TRACED": 1, "L2_HYPOTHESIS": 2, "L3_OBSERVED": 3}

PROVIDERS = {
    "runtime-lab": {"kind": "controlled-benchmark", "repository": "heliossamuelhernandezreyes/Nia-Tech"},
    "godot-benchmarks": {"kind": "benchmark-suite", "repository": "godotengine/godot-benchmarks"},
    "perfetto": {"kind": "trace-profiler", "repository": "google/perfetto"},
    "tracy": {"kind": "trace-profiler", "repository": "wolfpld/tracy"},
}

# Only mappings whose semantics are known are normalized automatically.
GODOT_BENCHMARK_METRICS = {
    "render_cpu": ("render_cpu_ms", "ms"),
    "render_gpu": ("render_gpu_ms", "ms"),
    "idle": ("cpu_process_ms", "ms"),
    "physics": ("physics_process_ms", "ms"),
    "time": ("wall_time_ms", "ms"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "metric"


def record(*, evidence_id: str, claim_ref: str | None, provider: str, provider_version: str | None,
           provider_commit: str | None, repository: str, immutable_ref: str | None, source_path: str | None,
           engine_version: str | None, engine_commit: str | None, original_name: str, original_unit: str | None,
           normalized_name: str, normalized_unit: str | None, value: float | int | None, platform: str | None,
           hardware: str | None, build_type: str | None, raw_hash: str, limitations: list[str],
           maturity_ceiling: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "evidence_id": evidence_id,
        "claim_ref": claim_ref,
        "provider": {
            "name": provider,
            "kind": PROVIDERS[provider]["kind"],
            "version": provider_version,
            "commit": provider_commit,
        },
        "source": {"repository": repository, "immutable_ref": immutable_ref, "path": source_path},
        "engine": {"version": engine_version, "commit": engine_commit},
        "metric": {
            "original_name": original_name,
            "original_unit": original_unit,
            "normalized_name": normalized_name,
            "normalized_unit": normalized_unit,
            "value": value,
        },
        "provenance": {
            "platform": platform,
            "hardware": hardware,
            "build_type": build_type,
            "raw_sha256": raw_hash,
        },
        "context": context or {},
        "limitations": limitations,
        "maturity_ceiling": maturity_ceiling,
    }


def flatten_metrics(obj: Any) -> Iterable[tuple[str, float | int]]:
    if not isinstance(obj, dict):
        return []
    direct = [(k, v) for k, v in obj.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if direct:
        return direct
    # Godot Benchmarks may nest metrics under a user-provided results prefix.
    nested: list[tuple[str, float | int]] = []
    for value in obj.values():
        if isinstance(value, dict):
            nested.extend((k, v) for k, v in value.items() if isinstance(v, (int, float)) and not isinstance(v, bool))
    return nested


def adapt_godot_benchmarks(path: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    data = load(path)
    if not isinstance(data, dict) or not isinstance(data.get("benchmarks"), list):
        raise ValueError("godot-benchmarks input must contain a benchmarks array")
    engine = data.get("engine") or {}
    system = data.get("system") or {}
    raw_hash = sha256(path)
    hardware = " | ".join(str(x) for x in [system.get("cpu_name"), system.get("cpu_architecture"), system.get("cpu_count")] if x not in (None, "")) or None
    out: list[dict[str, Any]] = []
    for bench in data["benchmarks"]:
        if not isinstance(bench, dict):
            continue
        category, name = str(bench.get("category", "unknown")), str(bench.get("name", "unknown"))
        for metric_name, value in flatten_metrics(bench.get("results", {})):
            if metric_name not in GODOT_BENCHMARK_METRICS:
                continue
            normalized, unit = GODOT_BENCHMARK_METRICS[metric_name]
            out.append(record(
                evidence_id=f"ARC-EXT-GB-{slug(category)}-{slug(name)}-{slug(metric_name)}-{raw_hash[:12]}",
                claim_ref=args.claim_ref,
                provider="godot-benchmarks",
                provider_version=args.provider_version,
                provider_commit=args.provider_commit,
                repository=PROVIDERS["godot-benchmarks"]["repository"],
                immutable_ref=args.source_ref or args.provider_commit,
                source_path=str(path),
                engine_version=engine.get("version"),
                engine_commit=engine.get("version_hash"),
                original_name=metric_name,
                original_unit="ms",
                normalized_name=normalized,
                normalized_unit=unit,
                value=value,
                platform=system.get("os"),
                hardware=hardware,
                build_type=args.build_type,
                raw_hash=raw_hash,
                limitations=["Imported upstream benchmark; semantic equivalence to ARCONT Runtime Lab is not assumed."],
                maturity_ceiling=args.maturity_ceiling,
                context={"category": category, "benchmark": name},
            ))
    if not out:
        raise ValueError("godot-benchmarks input contained no recognized numeric metrics")
    return out


def metric_value(metric: Any) -> float | int | None:
    if isinstance(metric, (int, float)) and not isinstance(metric, bool):
        return metric
    if not isinstance(metric, dict):
        return None
    for key in ("mean", "value", "p50", "median"):
        value = metric.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
    return None


def adapt_runtime_lab(path: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    data = load(path)
    if not isinstance(data, dict) or not data.get("benchmark_id") or not isinstance(data.get("metrics"), dict):
        raise ValueError("runtime-lab input must be an ARCONT benchmark result JSON")
    if data.get("aborted"):
        raise ValueError("aborted Runtime Lab results cannot be normalized as observations")
    provenance = data.get("provenance") or {}
    expected = provenance.get("raw_data_sha256")
    if expected is not None and not HEX64.fullmatch(str(expected)):
        raise ValueError("runtime-lab raw_data_sha256 is invalid")
    engine = data.get("engine") or {}
    platform = data.get("platform") or {}
    runtime = data.get("runtime") or {}
    experiment = data.get("experiment") or {}
    source_hash = sha256(path)
    raw_hash = str(expected) if expected else source_hash
    out: list[dict[str, Any]] = []
    for metric_name, metric in data["metrics"].items():
        value = metric_value(metric)
        if value is None:
            continue
        out.append(record(
            evidence_id=f"ARC-INT-RL-{slug(str(data['benchmark_id']))}-{slug(str(data.get('run_id','run')))}-{slug(metric_name)}",
            claim_ref=args.claim_ref or experiment.get("hypothesis_ref"),
            provider="runtime-lab",
            provider_version=None,
            provider_commit=provenance.get("harness_commit"),
            repository=PROVIDERS["runtime-lab"]["repository"],
            immutable_ref=provenance.get("harness_commit"),
            source_path=str(path),
            engine_version=engine.get("version"),
            engine_commit=engine.get("commit"),
            original_name=metric_name,
            original_unit="ms" if metric_name.endswith("_ms") else None,
            normalized_name=metric_name,
            normalized_unit="ms" if metric_name.endswith("_ms") else None,
            value=value,
            platform=platform.get("os"),
            hardware=" | ".join(str(x) for x in [platform.get("device"), platform.get("cpu"), platform.get("gpu")] if x not in (None, "")) or None,
            build_type=runtime.get("build_type"),
            raw_hash=raw_hash,
            limitations=["Runtime Lab result normalized without changing its canonical benchmark semantics."],
            maturity_ceiling=args.maturity_ceiling,
            context={"benchmark_id": data.get("benchmark_id"), "run_id": data.get("run_id"), "experiment": experiment},
        ))
    if not out:
        raise ValueError("runtime-lab result contained no usable numeric metrics")
    return out


def adapt_trace_extract(path: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    data = load(path)
    if not isinstance(data, dict) or data.get("provider") not in {"perfetto", "tracy"}:
        raise ValueError("trace extract provider must be perfetto or tracy")
    if data["provider"] != args.provider:
        raise ValueError("trace extract provider does not match selected adapter")
    if not isinstance(data.get("metrics"), list) or not data["metrics"]:
        raise ValueError("trace extract requires a non-empty metrics array")
    raw_path = Path(data.get("raw_trace_path", ""))
    if not raw_path.is_absolute():
        raw_path = (path.parent / raw_path).resolve()
    if not raw_path.exists():
        raise ValueError("raw trace referenced by extract does not exist")
    raw_hash = sha256(raw_path)
    declared_hash = data.get("raw_sha256")
    if declared_hash and declared_hash != raw_hash:
        raise ValueError("raw trace hash does not match trace extract")
    engine = data.get("engine") or {}
    system = data.get("system") or {}
    out: list[dict[str, Any]] = []
    for idx, metric in enumerate(data["metrics"]):
        if not isinstance(metric, dict) or not isinstance(metric.get("value"), (int, float)):
            raise ValueError(f"trace metric {idx} is invalid")
        out.append(record(
            evidence_id=f"ARC-EXT-{args.provider.upper()}-{slug(str(metric.get('name','metric')))}-{raw_hash[:12]}-{idx}",
            claim_ref=args.claim_ref,
            provider=args.provider,
            provider_version=data.get("provider_version") or args.provider_version,
            provider_commit=data.get("provider_commit") or args.provider_commit,
            repository=PROVIDERS[args.provider]["repository"],
            immutable_ref=data.get("source_ref") or args.source_ref,
            source_path=str(raw_path),
            engine_version=engine.get("version"),
            engine_commit=engine.get("commit"),
            original_name=str(metric.get("name")),
            original_unit=metric.get("unit"),
            normalized_name=str(metric.get("normalized_name") or metric.get("name")),
            normalized_unit=metric.get("normalized_unit") or metric.get("unit"),
            value=metric.get("value"),
            platform=system.get("platform"),
            hardware=system.get("hardware"),
            build_type=system.get("build_type"),
            raw_hash=raw_hash,
            limitations=list(data.get("limitations") or ["Trace-derived metric; interpretation depends on the declared extraction query/protocol."]),
            maturity_ceiling=args.maturity_ceiling,
            context={"query": metric.get("query"), "event": metric.get("event")},
        ))
    return out


def validate_record(r: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if r.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    provider = (r.get("provider") or {}).get("name")
    if provider not in PROVIDERS:
        errors.append("unregistered provider")
    raw_hash = (r.get("provenance") or {}).get("raw_sha256")
    if not isinstance(raw_hash, str) or not HEX64.fullmatch(raw_hash):
        errors.append("provenance.raw_sha256 must be sha256 hex")
    ceiling = r.get("maturity_ceiling")
    if ceiling not in CEILINGS:
        errors.append("maturity ceiling must be L1-L3")
    metric = r.get("metric") or {}
    if not metric.get("original_name") or not metric.get("normalized_name"):
        errors.append("metric names are required")
    if not isinstance(metric.get("value"), (int, float)) or isinstance(metric.get("value"), bool):
        errors.append("metric.value must be numeric")
    if not r.get("limitations"):
        errors.append("limitations must be non-empty")
    return errors


def bundle(provider: str, source: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [f"{r.get('evidence_id')}: {e}" for r in records for e in validate_record(r)]
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "schema_version": 1,
        "bundle_type": "arcont-evidence-bundle",
        "provider": provider,
        "source_sha256": sha256(source),
        "record_count": len(records),
        "semantic_equivalence_assumed": False,
        "auto_promotion_allowed": False,
        "records": records,
    }


def cmd_ingest(args: argparse.Namespace) -> int:
    path = Path(args.input).resolve()
    if not path.exists():
        raise SystemExit(f"input not found: {path}")
    if args.maturity_ceiling not in CEILINGS:
        raise SystemExit("maturity ceiling must be one of L1_SOURCE_TRACED, L2_HYPOTHESIS, L3_OBSERVED")
    if args.provider == "godot-benchmarks":
        records = adapt_godot_benchmarks(path, args)
    elif args.provider == "runtime-lab":
        records = adapt_runtime_lab(path, args)
    else:
        records = adapt_trace_extract(path, args)
    obj = bundle(args.provider, path, records)
    text = json.dumps(obj, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    obj = load(Path(args.bundle))
    errors: list[str] = []
    if obj.get("bundle_type") != "arcont-evidence-bundle":
        errors.append("invalid bundle_type")
    records = obj.get("records")
    if not isinstance(records, list) or not records:
        errors.append("bundle requires records")
    else:
        for r in records:
            errors.extend(validate_record(r))
    if obj.get("record_count") != (len(records) if isinstance(records, list) else -1):
        errors.append("record_count mismatch")
    if obj.get("auto_promotion_allowed") is not False:
        errors.append("auto_promotion_allowed must be false")
    if obj.get("semantic_equivalence_assumed") is not False:
        errors.append("semantic_equivalence_assumed must be false")
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="arcont-evidence-ingest")
    sub = p.add_subparsers(dest="command", required=True)
    i = sub.add_parser("ingest")
    i.add_argument("provider", choices=sorted(PROVIDERS))
    i.add_argument("input")
    i.add_argument("--output")
    i.add_argument("--claim-ref")
    i.add_argument("--provider-version")
    i.add_argument("--provider-commit")
    i.add_argument("--source-ref")
    i.add_argument("--build-type")
    i.add_argument("--maturity-ceiling", default="L1_SOURCE_TRACED", choices=sorted(CEILINGS))
    i.set_defaults(func=cmd_ingest)
    v = sub.add_parser("validate")
    v.add_argument("bundle")
    v.set_defaults(func=cmd_validate)
    return p


if __name__ == "__main__":
    try:
        ns = parser().parse_args()
        sys.exit(ns.func(ns))
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        sys.exit(1)
