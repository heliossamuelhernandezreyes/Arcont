#!/usr/bin/env python3
"""Download a small, provenance-tracked Poly Haven forest pack for Arcont.

The script intentionally treats Poly Haven as an authoring source, not a runtime
service. It downloads bounded 1K derivatives and refuses unexpectedly large
files so a source photogrammetry asset cannot silently bloat the mobile repo.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

API = "https://api.polyhaven.com"
UA = "ArcontForestAssetIngest/0.1 (github.com/heliossamuelhernandezreyes/Arcont)"
ROOT = Path("assets/cc0/polyhaven/forest")
MAX_FILE_BYTES = 48 * 1024 * 1024
MAX_PACK_BYTES = 150 * 1024 * 1024
ASSETS = {
    "forrest_ground_01": "texture",
    "rock_moss_set_01": "model",
    "tree_stump_01": "model",
    "pine_tree_01": "model",
}


def request_json(path: str) -> dict:
    req = urllib.request.Request(API + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


def safe_name(url: str) -> str:
    name = urllib.request.url2pathname(url.split("?", 1)[0]).rsplit("/", 1)[-1]
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def file_objects(node):
    if isinstance(node, dict):
        if isinstance(node.get("url"), str) and node["url"].startswith("https://"):
            yield node
        for value in node.values():
            yield from file_objects(value)
    elif isinstance(node, list):
        for value in node:
            yield from file_objects(value)


def find_resolution_branch(files: dict, kind: str):
    # Poly Haven's file tree changes shape by asset type. Prefer a 1K glTF
    # branch for models, then any glTF branch carrying a 1K descendant.
    if kind == "model":
        gltf = files.get("gltf")
        if isinstance(gltf, dict):
            if "1k" in gltf:
                return gltf["1k"]
            for key, value in gltf.items():
                if str(key).lower() in {"1k", "1024"}:
                    return value
        return gltf
    # Textures: retain only 1K material maps useful on mobile.
    selected = {}
    wanted = ("diff", "albedo", "nor_gl", "normal_gl", "rough", "arm", "ao")
    for key, value in files.items():
        low = str(key).lower()
        if not any(token in low for token in wanted):
            continue
        if isinstance(value, dict):
            branch = value.get("1k") or value.get("1024")
            if branch is not None:
                selected[key] = branch
    return selected or files


def download(obj: dict, dest: Path) -> dict | None:
    url = obj["url"]
    declared = int(obj.get("size") or 0)
    if declared and declared > MAX_FILE_BYTES:
        print(f"SKIP oversize {declared / 1048576:.1f} MiB: {url}")
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as response:
        length = int(response.headers.get("Content-Length") or 0)
        if length and length > MAX_FILE_BYTES:
            print(f"SKIP oversize response {length / 1048576:.1f} MiB: {url}")
            return None
        data = response.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        print(f"SKIP file crossed cap: {url}")
        return None
    dest.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    return {"file": dest.name, "bytes": len(data), "sha256": digest, "source_url": url}


def ingest(asset_id: str, kind: str) -> dict:
    info = request_json(f"/info/{asset_id}")
    files = request_json(f"/files/{asset_id}")
    branch = find_resolution_branch(files, kind)
    candidates = []
    seen = set()
    for obj in file_objects(branch):
        url = obj["url"]
        if url not in seen:
            seen.add(url)
            candidates.append(obj)
    out = ROOT / asset_id
    records = []
    for obj in candidates:
        record = download(obj, out / safe_name(obj["url"]))
        if record:
            records.append(record)
    return {
        "asset_id": asset_id,
        "name": info.get("name", asset_id),
        "kind": kind,
        "license": "CC0-1.0",
        "source": f"https://polyhaven.com/a/{asset_id}",
        "files_hash": info.get("files_hash"),
        "authors": info.get("authors", {}),
        "files": records,
    }


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": "Poly Haven",
        "source_api": API,
        "api_credit": "Powered by Poly Haven",
        "runtime_dependency": False,
        "policy": "1K/mobile authoring derivatives; per-file and pack size capped",
        "assets": [],
    }
    for asset_id, kind in ASSETS.items():
        print(f"Ingesting {asset_id}...")
        try:
            manifest["assets"].append(ingest(asset_id, kind))
        except Exception as exc:
            print(f"WARN {asset_id}: {exc}", file=sys.stderr)
            manifest["assets"].append({"asset_id": asset_id, "kind": kind, "error": str(exc)})
    total = sum(f.get("bytes", 0) for a in manifest["assets"] for f in a.get("files", []))
    manifest["total_bytes"] = total
    if total > MAX_PACK_BYTES:
        raise RuntimeError(f"forest pack exceeds cap: {total} bytes")
    (ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "README.md").write_text(
        "# Arcont Poly Haven forest authoring pack\n\n"
        "Selected source assets are CC0. The live API is used only by the ingest tool; "
        "the game has no runtime network dependency. Powered by Poly Haven.\n\n"
        "The committed derivatives are intentionally bounded for mobile evaluation. "
        "See `MANIFEST.json` for source URLs, authorship metadata and SHA-256 hashes.\n",
        encoding="utf-8",
    )
    print(f"POLYHAVEN_FOREST_INGEST_OK bytes={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
