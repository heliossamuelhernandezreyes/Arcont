#!/usr/bin/env python3
"""ARCONT Asset Vault trust audit.

Separates declared compatibility from evidence strength without breaking legacy
records. Existing records without compatibility evidence are classified as
`legacy-unverified`; new records may declare per-target evidence levels.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

ALLOWED_LEVELS = {"inferred", "format", "runtime"}


def _reference_kind(reference):
    if not isinstance(reference, str) or not reference.strip():
        return None
    if re.fullmatch(r"ARC-[A-Z0-9][A-Z0-9_-]*", reference):
        return "id"
    try:
        parsed = urlsplit(reference)
    except ValueError:
        return None
    if parsed.scheme:
        return "remote" if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password else None
    path = Path(reference.split("#", 1)[0])
    if not path.is_absolute() and ".." not in path.parts and path.suffix and "\\" not in reference:
        return "local"
    return None


def _local_evidence(item, root):
    path = (root / item["evidence_ref"].split("#", 1)[0]).resolve()
    return path if root.resolve() in path.parents and path.is_file() else None


def evidence_resolution(item, root: Path | None = None) -> str:
    """Do not equate a syntactically valid remote reference with fetched bytes."""
    if not isinstance(item, dict) or not item.get("evidence_ref"):
        return "not-provided"
    if root is not None and _reference_kind(item.get("evidence_ref")) == "local":
        path = _local_evidence(item, root)
        if path:
            expected = item.get("evidence_sha256")
            if expected and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
                return "bytes-verified"
            return "reference-verified" if not expected else "hash-mismatch"
        return "missing"
    return "declared"


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
    return level if isinstance(level, str) and level in ALLOWED_LEVELS else "invalid"


def validate_record_trust(record: dict[str, Any], root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["record must be an object"]
    for key in ("review", "license", "archive", "compatibility"):
        if key in record and not isinstance(record[key], dict):
            errors.append(f"{key} must be an object")
    if errors:
        return errors
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
        if not isinstance(level, str) or level not in ALLOWED_LEVELS:
            errors.append(f"compatibility_evidence.{target}.level must be one of {sorted(ALLOWED_LEVELS)}")
            continue
        if compatibility.get(target) is not True:
            errors.append(f"compatibility_evidence.{target} exists but compatibility.{target} is not true")
        if level == "runtime":
            tested = item.get("tested_at")
            try:
                if not isinstance(tested, str):
                    raise ValueError()
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", tested):
                    date.fromisoformat(tested)
                else:
                    parsed = datetime.fromisoformat(tested.replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        raise ValueError()
            except ValueError:
                errors.append(f"runtime compatibility for {target} requires ISO tested_at with date or timezone")
            if not _reference_kind(item.get("evidence_ref")):
                errors.append(f"runtime compatibility for {target} requires a valid evidence_ref (ID, HTTPS URL or local file)")
            digest = item.get("evidence_sha256")
            if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
                errors.append(f"runtime compatibility for {target} has invalid evidence_sha256")
            if evidence_resolution(item, root) in {"missing", "hash-mismatch"}:
                errors.append(f"runtime compatibility for {target} evidence_ref is missing or changed")
    return errors


def audit(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    level_counts: Counter[str] = Counter()
    resolution_counts: Counter[str] = Counter()
    record_count = 0
    declared_targets = 0
    license_verified = 0

    for path, record in iter_records(root) or []:
        record_count += 1
        record_errors = validate_record_trust(record, root)
        for err in record_errors:
            errors.append(f"{path.relative_to(root)}: {err}")
        if record_errors:
            continue
        if (record.get("review") or {}).get("license_verified") is True:
            license_verified += 1
        compatibility = record.get("compatibility") or {}
        for target, declared in compatibility.items():
            if declared is True:
                declared_targets += 1
                level_counts[compatibility_level(record, str(target))] += 1
                item = (record.get("compatibility_evidence") or {}).get(target, {})
                if item.get("level") == "runtime":
                    resolution_counts[evidence_resolution(item, root)] += 1

    return {
        "ok": not errors,
        "records": record_count,
        "license_verified_records": license_verified,
        "declared_compatibility_targets": declared_targets,
        "compatibility_evidence_levels": dict(sorted(level_counts.items())),
        "runtime_reference_resolution": dict(sorted(resolution_counts.items())),
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
