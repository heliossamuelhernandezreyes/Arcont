#!/usr/bin/env python3
"""Inventory Arcont source/runtime assets without importing Godot.

Produces JSON/CSV grouped by extension and top-level asset family. Useful for spotting
what is already stored before acquiring more material.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ASSET_EXTENSIONS = {
    ".gltf", ".glb", ".fbx", ".obj", ".blend", ".dae", ".usd", ".usda", ".usdc",
    ".png", ".jpg", ".jpeg", ".webp", ".exr", ".hdr", ".tga", ".bmp", ".svg",
    ".wav", ".ogg", ".mp3", ".flac", ".m4a",
    ".ttf", ".otf", ".woff", ".woff2",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--out", default="warehouse/repo_inventory")
    p.add_argument("--hash", action="store_true", help="SHA-256 every asset; slower on large warehouses")
    args = p.parse_args()

    root = Path(args.root).resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    records = []
    ext_counts = Counter()
    family_counts = Counter()
    ext_bytes = Counter()
    family_bytes = Counter()

    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or ".godot" in path.parts:
            continue
        if path.suffix.lower() not in ASSET_EXTENSIONS:
            continue
        rel = path.relative_to(root).as_posix()
        size = path.stat().st_size
        parts = Path(rel).parts
        family = "/".join(parts[:3]) if len(parts) >= 3 else "/".join(parts[:-1]) or "."
        rec = {
            "path": rel,
            "extension": path.suffix.lower(),
            "bytes": size,
            "family": family,
        }
        if args.hash:
            rec["sha256"] = sha256(path)
        records.append(rec)
        ext_counts[rec["extension"]] += 1
        ext_bytes[rec["extension"]] += size
        family_counts[family] += 1
        family_bytes[family] += size

    records.sort(key=lambda r: r["path"])
    summary = {
        "asset_count": len(records),
        "total_bytes": sum(r["bytes"] for r in records),
        "extensions": {k: {"count": ext_counts[k], "bytes": ext_bytes[k]} for k in sorted(ext_counts)},
        "families": {k: {"count": family_counts[k], "bytes": family_bytes[k]} for k in sorted(family_counts)},
    }
    (out / "inventory.json").write_text(json.dumps({"summary": summary, "assets": records}, indent=2), encoding="utf-8")
    with (out / "inventory.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "extension", "bytes", "family", "sha256"])
        writer.writeheader()
        for rec in records:
            writer.writerow({**rec, "sha256": rec.get("sha256", "")})
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
