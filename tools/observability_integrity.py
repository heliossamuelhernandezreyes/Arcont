#!/usr/bin/env python3
"""Integrity checks for ARCONT's unified observability layer. Stdlib-only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED_PROVIDERS = ["runtime-lab", "godot-benchmarks", "perfetto", "tracy"]


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    repo = root()
    errors: list[str] = []
    manifest = json.loads((repo / "arcont.manifest.json").read_text(encoding="utf-8"))
    obs = manifest.get("observability") or {}
    refs = {
        "architecture": obs.get("architecture"),
        "instrument_registry": obs.get("instrument_registry"),
        "unified_ingest": obs.get("unified_ingest"),
        "evidence_record_schema": obs.get("evidence_record_schema"),
        "evidence_bundle_schema": obs.get("evidence_bundle_schema"),
        "trace_extract_schema": obs.get("trace_extract_schema"),
    }
    for name, rel in refs.items():
        if not rel or not (repo / rel).exists():
            errors.append(f"observability.{name} references missing path: {rel!r}")
    if obs.get("providers") != EXPECTED_PROVIDERS:
        errors.append(f"observability.providers must equal {EXPECTED_PROVIDERS}")
    if obs.get("semantic_equivalence_assumed") is not False:
        errors.append("semantic_equivalence_assumed must be false")
    if obs.get("auto_promotion_allowed") is not False:
        errors.append("auto_promotion_allowed must be false")
    for key in ("evidence_record_schema", "evidence_bundle_schema", "trace_extract_schema"):
        rel = obs.get(key)
        if rel and (repo / rel).exists():
            try:
                schema = json.loads((repo / rel).read_text(encoding="utf-8"))
                if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                    errors.append(f"{rel}: must declare JSON Schema draft 2020-12")
            except Exception as exc:
                errors.append(f"{rel}: invalid JSON: {exc}")
    ingest = repo / str(obs.get("unified_ingest", ""))
    if ingest.exists():
        text = ingest.read_text(encoding="utf-8")
        for provider in EXPECTED_PROVIDERS:
            if f'"{provider}"' not in text:
                errors.append(f"unified ingest kernel does not register provider {provider}")
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
