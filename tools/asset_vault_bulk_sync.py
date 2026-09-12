#!/usr/bin/env python3
"""Stable bulk synchronization for the ARCONT Asset Vault.

This orchestrator is intentionally metadata-only. It imports provider metadata,
preserves acquisition timestamps for unchanged records, rebuilds a stable index,
and avoids noisy commits when upstream data has not changed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from asset_vault_indexer import (
    POLYHAVEN_API,
    build_index,
    dump_json,
    fetch_json,
    load_json,
    now_utc,
    polyhaven_record,
)


def _preserve_stable_fields(new: dict[str, Any], old: dict[str, Any]) -> dict[str, Any]:
    new_source = new.get("source") or {}
    old_source = old.get("source") or {}
    if old_source.get("acquired_at"):
        new_source["acquired_at"] = old_source["acquired_at"]
    new["source"] = new_source

    new_review = new.get("review") or {}
    old_review = old.get("review") or {}
    if old_review.get("last_checked"):
        new_review["last_checked"] = old_review["last_checked"]
    new["review"] = new_review
    return new


def _without_review_clock(record: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(record))
    review = clone.get("review") or {}
    review["last_checked"] = None
    clone["review"] = review
    return clone


def sync_polyhaven(root: Path, limit: int | None = None) -> tuple[int, int]:
    data = fetch_json(POLYHAVEN_API)
    if not isinstance(data, dict):
        raise RuntimeError("Poly Haven API returned an unexpected payload")

    target = root / "assets" / "catalog" / "polyhaven"
    target.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    changed = 0
    total = 0

    for external_id, meta in sorted(data.items()):
        if limit is not None and total >= limit:
            break
        if not isinstance(meta, dict):
            continue
        total += 1
        seen.add(external_id)
        path = target / f"{external_id}.asset.json"
        record = polyhaven_record(external_id, meta)

        if path.exists():
            old = load_json(path)
            record = _preserve_stable_fields(record, old)
            if _without_review_clock(record) == _without_review_clock(old):
                continue
            record["review"]["last_checked"] = now_utc()

        dump_json(path, record)
        changed += 1

    # Do not delete unseen records during limited/test syncs. During a full sync,
    # upstream removals are retained rather than silently deleted; provenance is
    # more important than mirroring current listing state. A later review can
    # mark them unavailable explicitly.
    return total, changed


def build_stable_index(root: Path) -> tuple[int, bool]:
    index, errors = build_index(root)
    if errors:
        raise RuntimeError("\n".join(errors))

    out = root / "assets" / "index.json"
    changed = True
    if out.exists():
        old = load_json(out)
        if isinstance(old, dict) and old.get("records") == index.get("records"):
            index["generated_at"] = old.get("generated_at")
            changed = False

    if changed or not out.exists():
        dump_json(out, index)
    return int(index.get("record_count", 0)), changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Bulk-sync ARCONT Asset Vault metadata")
    parser.add_argument("--root", default=".")
    parser.add_argument("--polyhaven-limit", type=int)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    total, changed = sync_polyhaven(root, args.polyhaven_limit)
    count, index_changed = build_stable_index(root)
    print(f"Poly Haven: {total} seen, {changed} records changed")
    print(f"Asset index: {count} records, changed={index_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
