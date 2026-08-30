#!/usr/bin/env python3
"""Arcont realistic asset warehouse collector for Poly Haven.

Catalogs the public Poly Haven API and optionally downloads selected source files
into a disposable warehouse directory. It never promotes files into runtime.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

API = "https://api.polyhaven.com"
UA = "ArcontAssetWarehouse/1.0 (github.com/heliossamuelhernandezreyes/Arcont)"
CC0 = "CC0-1.0"
LICENSE_URL = "https://polyhaven.com/license"

DEFAULT_TERMS = [
    "forest", "ground", "dirt", "mud", "soil", "gravel", "rock", "stone",
    "boulder", "moss", "bark", "tree", "log", "wood", "grass", "fern",
    "leaf", "branch", "root", "brick", "concrete", "plaster", "stucco",
    "roof", "metal", "rust", "asphalt", "road", "wall", "door", "window",
    "fence", "industrial", "factory", "pipe", "barrel", "crate", "debris",
    "rubble", "abandoned", "rural", "farm", "shed", "barn", "workshop",
    "overcast", "cloudy", "sunset", "dusk", "night", "interior"
]


def request_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.load(response)


def text_blob(asset_id: str, meta: dict[str, Any]) -> str:
    bits: list[str] = [asset_id]
    for key in ("name", "description", "category", "type"):
        value = meta.get(key)
        if value:
            bits.append(str(value))
    bits.extend(str(x) for x in meta.get("tags", []) or [])
    return " ".join(bits).lower()


def score(meta_text: str, terms: list[str]) -> int:
    return sum(1 for term in terms if term.lower() in meta_text)


def flatten_downloads(node: Any, path: tuple[str, ...] = ()) -> Iterable[dict[str, Any]]:
    if isinstance(node, dict):
        if isinstance(node.get("url"), str):
            yield {
                "key": "/".join(path),
                "url": node["url"],
                "size": node.get("size"),
                "md5": node.get("md5"),
            }
        for key, value in node.items():
            if key not in {"url", "size", "md5"}:
                yield from flatten_downloads(value, path + (str(key),))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from flatten_downloads(value, path + (str(index),))


def resolution_rank(key: str, target: str) -> int:
    key = key.lower()
    m = re.search(r"(?:^|/)(\d+k)(?:/|$)", key)
    if not m:
        return 1000
    value = int(m.group(1)[:-1])
    target_value = int(target[:-1])
    return abs(value - target_value)


def choose_files(files: list[dict[str, Any]], target: str, mode: str) -> list[dict[str, Any]]:
    if mode == "all":
        return files
    preferred_ext = (".gltf", ".glb", ".fbx", ".blend", ".png", ".jpg", ".jpeg", ".hdr", ".exr")
    candidates = [f for f in files if f["url"].lower().split("?")[0].endswith(preferred_ext)] or files
    candidates.sort(key=lambda f: (resolution_rank(f["key"], target), int(f.get("size") or 0)))
    if mode == "representative":
        # Keep several distinct file families, but avoid recursively pulling every source variant.
        result: list[dict[str, Any]] = []
        families: set[str] = set()
        for item in candidates:
            family = item["key"].split("/")[0] if item["key"] else "file"
            if family not in families:
                families.add(family)
                result.append(item)
        return result[:12]
    return candidates[:1]


def download(url: str, destination: Path, expected_md5: str | None = None) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    sha = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    with urllib.request.urlopen(req, timeout=180) as src, destination.open("wb") as dst:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            dst.write(chunk)
            sha.update(chunk)
            md5.update(chunk)
            size += len(chunk)
    actual_md5 = md5.hexdigest()
    if expected_md5 and actual_md5.lower() != expected_md5.lower():
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"MD5 mismatch for {url}: expected {expected_md5}, got {actual_md5}")
    return {"path": str(destination), "bytes": size, "sha256": sha.hexdigest(), "md5": actual_md5}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="warehouse/polyhaven")
    p.add_argument("--terms", default=",".join(DEFAULT_TERMS))
    p.add_argument("--min-score", type=int, default=1)
    p.add_argument("--limit", type=int, default=0, help="0 = all matching assets")
    p.add_argument("--download", action="store_true")
    p.add_argument("--resolution", choices=["1k", "2k", "4k", "8k", "16k", "24k"], default="4k")
    p.add_argument("--file-mode", choices=["single", "representative", "all"], default="representative")
    p.add_argument("--max-total-gb", type=float, default=20.0)
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    terms = [x.strip().lower() for x in args.terms.split(",") if x.strip()]
    now = datetime.now(timezone.utc).isoformat()

    raw_assets = request_json(f"{API}/assets")
    if not isinstance(raw_assets, dict):
        raise RuntimeError("Unexpected /assets response")

    records: list[dict[str, Any]] = []
    for asset_id, meta in raw_assets.items():
        if not isinstance(meta, dict):
            continue
        blob = text_blob(asset_id, meta)
        s = score(blob, terms)
        if s < args.min_score:
            continue
        records.append({
            "provider": "Poly Haven",
            "asset_id": asset_id,
            "name": meta.get("name", asset_id),
            "type": meta.get("type"),
            "category": meta.get("category"),
            "tags": meta.get("tags", []),
            "description": meta.get("description"),
            "score": s,
            "license": CC0,
            "license_url": LICENSE_URL,
            "source_url": f"https://polyhaven.com/a/{asset_id}",
            "api_files_url": f"{API}/files/{asset_id}",
            "status": "warehouse",
            "indexed_at": now,
            "source_metadata": meta,
        })

    records.sort(key=lambda r: (-r["score"], str(r["category"] or ""), r["asset_id"]))
    if args.limit > 0:
        records = records[: args.limit]

    catalog_path = out / "catalog.json"
    catalog_path.write_text(json.dumps({
        "provider": "Poly Haven",
        "api": API,
        "license": CC0,
        "generated_at": now,
        "terms": terms,
        "count": len(records),
        "assets": records,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    with (out / "catalog.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["asset_id", "name", "type", "category", "score", "source_url", "license"])
        for r in records:
            writer.writerow([r["asset_id"], r["name"], r["type"], r["category"], r["score"], r["source_url"], r["license"]])

    acquisitions: list[dict[str, Any]] = []
    total = 0
    cap = int(args.max_total_gb * 1024**3)
    if args.download:
        for i, record in enumerate(records, 1):
            print(f"[{i}/{len(records)}] {record['asset_id']}")
            try:
                file_tree = request_json(record["api_files_url"])
                available = list(flatten_downloads(file_tree))
                selected = choose_files(available, args.resolution, args.file_mode)
                for item in selected:
                    expected_size = int(item.get("size") or 0)
                    if cap and total + expected_size > cap:
                        print("Download cap reached; stopping cleanly.")
                        raise StopIteration
                    filename = os.path.basename(item["url"].split("?")[0]) or "asset.bin"
                    dest = out / "masters" / record["asset_id"] / filename
                    result = download(item["url"], dest, item.get("md5"))
                    total += result["bytes"]
                    acquisitions.append({**record, "file_key": item["key"], "download_url": item["url"], **result})
            except StopIteration:
                break
            except Exception as exc:
                acquisitions.append({"asset_id": record["asset_id"], "error": str(exc), "status": "download_error"})

    (out / "acquisitions.json").write_text(json.dumps({
        "generated_at": now,
        "downloaded_bytes": total,
        "count": len(acquisitions),
        "files": acquisitions,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Indexed {len(records)} matching assets -> {catalog_path}")
    print(f"Downloaded {total / 1024**3:.2f} GiB across {len(acquisitions)} records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
