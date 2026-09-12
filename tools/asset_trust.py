#!/usr/bin/env python3
"""ARCONT Asset Vault trust audit.

Separates declared compatibility from evidence strength without breaking legacy
records. Existing records without compatibility evidence are classified as
`legacy-unverified`; new records may declare per-target evidence levels.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ALLOWED_LEVELS = {"inferred", "format", "runtime"}


def iter_records(root: Path) -> Iterable[tuple[Path, dict[str, Any]]]:
    catalog = root / "assets" / "catalog"
    if not catalog.exists():
        return
    for path in sorted(catalog.rglob("*.asset.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj, dict):
            yield path, obj


def compatibility_level(record: dict[str, Any], target: str) -> str:
    compatibility = record.get("compatibility") or {}
    if compatibility.get(target) is not True:
        return "not-declared"
    evidence = record.get("compatibility_evidence") or {}
    item = evidence.get(target)
    if not isinstance(item, dict):
        return "legacy-unverified"
    level = item.get("level")
    return level if level in ALLOWED_LEVELS else "invalid"


def validate_record_trust(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    review = record.get("review") or {}
    license_data = record.get("license") or {}
    archive = record.get("archive") or {}

    if archive.get("mirrored_in_arcont") and review.get("license_verified") is not True:
        errors.append("mirrored asset requires review.license_verified=true")
    if archive.get("mirrored_in_arcont") and license_data.get("redistribution_allowed") is not True:
        errors.append("mirrored asset requires license.redistribution_allowed=true")

    compatibility = record.get("compatibility") or {}
    evidence = record.get("compatibility_evidence")
    if evidence is not None and not isinstance(evidence, dict):
        errors.append("compatibility_evidence must be an object when present")
        return errors

    for target, item in (evidence or {}).items():
        if not isinstance(item, dict):
            errors.append(f"compatibility_evidence.{target} must be an object")
            continue
        level = item.get("level")
        if level not in ALLOWED_LEVELS:
            errors.append(f"compatibility_evidence.{target}.level must be one of {sorted(ALLOWED_LEVELS)}")
            continue
        if compatibility.get(target) is not True:
            errors.append(f"compatibility_evidence.{target} exists but compatibility.{target} is not true")
        if level == "runtime":
            if not item.get("tested_at"):
                errors.append(f"runtime compatibility for {target} requires tested_at")
            if not item.get("evidence_ref"):
                errors.append(f"runtime compatibility for {target} requires evidence_ref")
    return errors


def audit(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    level_counts: Counter[str] = Counter()
    record_count = 0
    declared_targets = 0
    license_verified = 0

    for path, record in iter_records(root) or []:
        record_count += 1
        if (record.get("review") or {}).get("license_verified") is True:
            license_verified += 1
        for err in validate_record_trust(record):
            errors.append(f"{path.relative_to(root)}: {err}")
        compatibility = record.get("compatibility") or {}
        for target, declared in compatibility.items():
            if declared is True:
                declared_targets += 1
                level_counts[compatibility_level(record, str(target))] += 1

    return {
        "ok": not errors,
        "records": record_count,
        "license_verified_records": license_verified,
        "declared_compatibility_targets": declared_targets,
        "compatibility_evidence_levels": dict(sorted(level_counts.items())),
        "errors": errors,
        "note": "legacy-unverified means compatibility was declared before per-target evidence levels existed; it is not runtime proof",
    }


def main() -> int:
    p = argparse.ArgumentParser(prog="asset-trust")
    p.add_argument("--root", default=".")
    p.add_argument("--report", action="store_true", help="print full JSON report")
    args = p.parse_args()
    result = audit(Path(args.root).resolve())
    if args.report or not result["ok"]:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(
            f"Asset trust valid: {result['records']} records; "
            f"compatibility evidence={result['compatibility_evidence_levels']}"
        )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
