#!/usr/bin/env python3
"""ARCONT laboratory utility.

Stdlib-only tooling for validating the knowledge bank, tracing impact from
changed Godot source paths, estimating evidence confidence, and comparing
benchmark result files.

This tool does not execute Godot and does not contain game code.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

ARC_ID_RE = re.compile(r"\bARC-[A-Z0-9][A-Z0-9_-]*\b")
HEX40_RE = re.compile(r"\b[0-9a-f]{40}\b", re.I)
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

DEPENDENCY_RELATIONS = {
    "depends_on",
    "implemented_by",
    "measured_by",
    "derived_from",
    "supports",
    "valid_on",
    "related_to",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _scalar(value: str) -> Any:
    value = value.strip()
    if value in {"null", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_simple_graph(path: Path) -> dict[str, Any]:
    """Parse ARCONT's deliberately simple YAML graph subset without PyYAML."""
    graph: dict[str, Any] = {"nodes": [], "edges": []}
    section: str | None = None
    current: dict[str, Any] | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            if key in {"nodes", "edges"}:
                section = key
                current = None
            else:
                graph[key] = _scalar(value)
            continue
        stripped = line.strip()
        if section and stripped.startswith("- "):
            current = {}
            graph[section].append(current)
            stripped = stripped[2:]
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                current[key.strip()] = _scalar(value)
            continue
        if section and current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = _scalar(value)
    return graph


def canonical_engine_commit(root: Path) -> str | None:
    pin = root / "docs" / "godot" / "SOURCE_PIN.md"
    if not pin.exists():
        return None
    matches = HEX40_RE.findall(pin.read_text(encoding="utf-8", errors="ignore"))
    return matches[0].lower() if matches else None


def iter_text_files(root: Path):
    ignored = {".git", "__pycache__"}
    for path in root.rglob("*"):
        if any(part in ignored for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in {".md", ".yaml", ".yml", ".json", ".py"}:
            yield path


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    id_locations: dict[str, list[str]] = defaultdict(list)

    for path in iter_text_files(root):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for arc_id in set(ARC_ID_RE.findall(text)):
            id_locations[arc_id].append(rel)

        if path.suffix.lower() == ".md":
            for link in MD_LINK_RE.findall(text):
                if link.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                target = link.split("#", 1)[0]
                if not target:
                    continue
                if not (path.parent / target).resolve().exists():
                    errors.append(f"broken-link: {rel} -> {link}")

    # Same ID appearing in prose and graph is legitimate; duplicates only become
    # errors when the same graph declares the same node more than once.
    graph_dir = root / "docs" / "godot" / "knowledge"
    canonical_commit = canonical_engine_commit(root)
    if graph_dir.exists():
        for graph_path in sorted(graph_dir.glob("*.y*ml")):
            graph = parse_simple_graph(graph_path)
            rel = graph_path.relative_to(root).as_posix()
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])
            ids = [str(n.get("id")) for n in nodes if n.get("id")]
            if len(ids) != len(set(ids)):
                errors.append(f"duplicate-node-id: {rel}")
            node_ids = set(ids)
            for node in nodes:
                node_id = node.get("id", "<missing-id>")
                kind = node.get("kind")
                if not node.get("id") or not kind:
                    errors.append(f"invalid-node: {rel}: {node}")
                if kind == "source-symbol":
                    if not node.get("path") or not node.get("symbol"):
                        errors.append(f"incomplete-source-node: {rel}: {node_id}")
                if node.get("status") in {"validated", "reproduced"} and not node.get("evidence"):
                    warnings.append(f"status-without-inline-evidence: {rel}: {node_id}")
            for edge in edges:
                src = edge.get("from")
                dst = edge.get("to")
                if src not in node_ids:
                    errors.append(f"dangling-edge-from: {rel}: {src}")
                if dst not in node_ids:
                    errors.append(f"dangling-edge-to: {rel}: {dst}")
                if not edge.get("relation"):
                    errors.append(f"missing-edge-relation: {rel}: {edge}")
            graph_commit = str(graph.get("engine_commit") or "").lower()
            if canonical_commit and graph_commit and graph_commit != canonical_commit:
                warnings.append(
                    f"engine-commit-mismatch: {rel}: graph={graph_commit} canonical={canonical_commit}"
                )

    return errors, warnings


def load_all_graphs(root: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    graph_dir = root / "docs" / "godot" / "knowledge"
    if not graph_dir.exists():
        return nodes, edges
    for graph_path in sorted(graph_dir.glob("*.y*ml")):
        graph = parse_simple_graph(graph_path)
        for node in graph.get("nodes", []):
            if node.get("id"):
                enriched = dict(node)
                enriched["_graph"] = graph_path.relative_to(root).as_posix()
                nodes[str(node["id"])] = enriched
        edges.extend(graph.get("edges", []))
    return nodes, edges


def impact(root: Path, changed_paths: list[str]) -> dict[str, Any]:
    nodes, edges = load_all_graphs(root)
    starts: set[str] = set()
    normalized = {p.replace("\\", "/").lstrip("./") for p in changed_paths}

    for node_id, node in nodes.items():
        path = str(node.get("path") or "").replace("\\", "/").lstrip("./")
        if path and any(path == p or path.startswith(p.rstrip("/") + "/") or p.startswith(path.rstrip("/") + "/") for p in normalized):
            starts.add(node_id)

    reverse: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        rel = edge.get("relation")
        src = edge.get("from")
        dst = edge.get("to")
        if rel in DEPENDENCY_RELATIONS and src in nodes and dst in nodes:
            reverse[str(dst)].add(str(src))

    impacted = set(starts)
    q = deque(starts)
    while q:
        cur = q.popleft()
        for dependent in reverse.get(cur, set()):
            if dependent not in impacted:
                impacted.add(dependent)
                q.append(dependent)

    ordered = sorted(impacted)
    return {
        "changed_paths": sorted(normalized),
        "matched_source_nodes": sorted(starts),
        "impacted_nodes": [
            {
                "id": node_id,
                "kind": nodes[node_id].get("kind"),
                "status": nodes[node_id].get("status"),
                "claim": nodes[node_id].get("claim"),
                "path": nodes[node_id].get("path"),
                "graph": nodes[node_id].get("_graph"),
            }
            for node_id in ordered
        ],
        "needs_revalidation": [
            node_id
            for node_id in ordered
            if nodes[node_id].get("kind") in {"rule", "decision", "inference", "observation", "benchmark"}
        ],
    }


def confidence_score(
    source_quality: float,
    reproductions: int,
    hardware_profiles: int,
    engine_versions: int,
    age_days: int,
    contradictions: int,
) -> dict[str, Any]:
    """Heuristic confidence score. Not a statistical probability."""
    sq = max(0.0, min(1.0, source_quality))
    reproduction = 1.0 - math.exp(-max(0, reproductions) / 2.0)
    hardware = 1.0 - math.exp(-max(0, hardware_profiles) / 2.0)
    versions = 1.0 - math.exp(-max(0, engine_versions) / 1.5)
    recency = math.exp(-max(0, age_days) / 730.0)
    penalty = min(0.45, max(0, contradictions) * 0.12)

    raw = (
        0.30 * sq
        + 0.25 * reproduction
        + 0.15 * hardware
        + 0.15 * versions
        + 0.15 * recency
        - penalty
    )
    score = round(max(0.0, min(1.0, raw)) * 100.0, 1)
    if score >= 85:
        band = "strong"
    elif score >= 70:
        band = "moderate"
    elif score >= 50:
        band = "provisional"
    else:
        band = "weak"
    return {
        "score": score,
        "band": band,
        "note": "heuristic evidence-confidence index; not a probability",
        "components": {
            "source_quality": round(sq, 4),
            "reproduction": round(reproduction, 4),
            "hardware_diversity": round(hardware, 4),
            "version_diversity": round(versions, 4),
            "recency": round(recency, 4),
            "contradiction_penalty": round(penalty, 4),
        },
    }


def get_nested(obj: dict[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def compatibility(a: dict[str, Any], b: dict[str, Any]) -> tuple[bool, list[str]]:
    controlled = [
        "benchmark_id",
        "platform.os",
        "platform.device",
        "platform.cpu",
        "platform.gpu",
        "runtime.renderer",
        "runtime.resolution",
        "runtime.build_type",
    ]
    mismatches = []
    for field in controlled:
        va = get_nested(a, field)
        vb = get_nested(b, field)
        if va is not None and vb is not None and va != vb:
            mismatches.append(f"{field}: {va!r} != {vb!r}")
    return not mismatches, mismatches


def pct_delta(old: Any, new: Any) -> float | None:
    if not isinstance(old, (int, float)) or not isinstance(new, (int, float)) or old == 0:
        return None
    return round((new - old) / old * 100.0, 3)


def compare_results(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    direct, mismatches = compatibility(a, b)
    metrics = [
        "metrics.frame_time_ms.mean",
        "metrics.frame_time_ms.median",
        "metrics.frame_time_ms.p95",
        "metrics.frame_time_ms.p99",
        "metrics.frame_time_ms.max",
        "metrics.fps.mean",
        "metrics.fps.median",
        "metrics.memory_mb.rss",
        "metrics.memory_mb.peak",
        "metrics.cpu_ms",
        "metrics.gpu_ms",
        "metrics.draw_calls",
        "metrics.objects",
    ]
    rows = []
    for metric in metrics:
        va = get_nested(a, metric)
        vb = get_nested(b, metric)
        if va is None and vb is None:
            continue
        rows.append({"metric": metric, "a": va, "b": vb, "delta_percent": pct_delta(va, vb)})
    return {
        "directly_comparable": direct,
        "compatibility_warnings": mismatches,
        "run_a": a.get("run_id"),
        "run_b": b.get("run_id"),
        "engine_a": a.get("engine"),
        "engine_b": b.get("engine"),
        "metrics": rows,
        "interpretation_guard": (
            "Deltas are descriptive only. Do not label a regression without repeated samples, "
            "dispersion/uncertainty, and an engineering threshold appropriate to the benchmark."
        ),
    }


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    errors, warnings = validate(root)
    print(json.dumps({"errors": errors, "warnings": warnings, "ok": not errors}, indent=2))
    return 1 if errors else 0


def cmd_impact(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    print(json.dumps(impact(root, args.changed), indent=2))
    return 0


def cmd_confidence(args: argparse.Namespace) -> int:
    result = confidence_score(
        args.source_quality,
        args.reproductions,
        args.hardware_profiles,
        args.engine_versions,
        args.age_days,
        args.contradictions,
    )
    print(json.dumps(result, indent=2))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    a = json.loads(Path(args.a).read_text(encoding="utf-8"))
    b = json.loads(Path(args.b).read_text(encoding="utf-8"))
    print(json.dumps(compare_results(a, b), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="arcont-lab")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate ARCONT knowledge integrity")
    v.add_argument("--root", default=str(repo_root()))
    v.set_defaults(func=cmd_validate)

    i = sub.add_parser("impact", help="trace knowledge affected by changed source paths")
    i.add_argument("--root", default=str(repo_root()))
    i.add_argument("--changed", action="append", required=True, help="changed upstream path; repeat as needed")
    i.set_defaults(func=cmd_impact)

    c = sub.add_parser("confidence", help="compute a heuristic evidence-confidence index")
    c.add_argument("--source-quality", type=float, required=True, help="0..1")
    c.add_argument("--reproductions", type=int, default=0)
    c.add_argument("--hardware-profiles", type=int, default=0)
    c.add_argument("--engine-versions", type=int, default=1)
    c.add_argument("--age-days", type=int, default=0)
    c.add_argument("--contradictions", type=int, default=0)
    c.set_defaults(func=cmd_confidence)

    r = sub.add_parser("compare", help="compare two canonical benchmark JSON results")
    r.add_argument("a")
    r.add_argument("b")
    r.set_defaults(func=cmd_compare)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
