#!/usr/bin/env python3
"""ARCONT Asset Vault indexer.

Stdlib-only tool for catalog ingestion, validation, deduplication, indexing,
querying, and source adapters. It never assumes a license: every imported
record carries explicit license metadata and a review state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1
CATALOG_GLOB = "*.asset.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._:-]{2,127}$")
POLYHAVEN_API = "https://api.polyhaven.com/assets"
USER_AGENT = "ARCONT-Asset-Vault/1.0 (+https://github.com/heliossamuelhernandezreyes/Arcont)"

REQUIRED_TOP = {"schema_version", "id", "title", "asset_type", "source", "license", "technical", "compatibility", "archive", "review"}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(provider: str, external_id: str) -> str:
    raw = f"{provider}:{external_id}".encode("utf-8")
    return f"ARC-ASSET-{provider.upper()}-{hashlib.sha256(raw).hexdigest()[:16].upper()}"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP - set(record))
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    rid = record.get("id")
    if not isinstance(rid, str) or not ID_RE.match(rid):
        errors.append("id must be a stable uppercase ARCONT-style identifier")
    if not isinstance(record.get("title"), str) or not record.get("title", "").strip():
        errors.append("title must be a non-empty string")
    source = record.get("source") or {}
    if not isinstance(source, dict) or not source.get("provider") or not source.get("asset_url"):
        errors.append("source.provider and source.asset_url are required")
    license_data = record.get("license") or {}
    if not isinstance(license_data, dict) or not license_data.get("name"):
        errors.append("license.name is required; unknown licenses must not be guessed")
    review = record.get("review") or {}
    if not isinstance(review, dict) or "license_verified" not in review:
        errors.append("review.license_verified is required")
    archive = record.get("archive") or {}
    if isinstance(archive, dict):
        digest = archive.get("sha256")
        if digest is not None and (not isinstance(digest, str) or not SHA256_RE.match(digest)):
            errors.append("archive.sha256 must be null or lowercase 64-char SHA-256")
        if archive.get("mirrored_in_arcont") and not license_data.get("redistribution_allowed"):
            errors.append("mirrored asset requires license.redistribution_allowed=true")
    else:
        errors.append("archive must be an object")
    return errors


def iter_catalog(root: Path) -> Iterable[tuple[Path, dict[str, Any]]]:
    catalog = root / "assets" / "catalog"
    if not catalog.exists():
        return
    for path in sorted(catalog.rglob(CATALOG_GLOB)):
        obj = load_json(path)
        if not isinstance(obj, dict):
            raise ValueError(f"{path}: record must be a JSON object")
        yield path, obj


def dedupe_key(record: dict[str, Any]) -> tuple[str, str]:
    source = record.get("source") or {}
    provider = str(source.get("provider") or "").strip().lower()
    external_id = str(source.get("external_id") or source.get("asset_url") or "").strip().lower()
    return provider, external_id


def build_index(root: Path) -> tuple[dict[str, Any], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}
    seen_sources: dict[tuple[str, str], Path] = {}
    seen_hashes: dict[str, Path] = {}

    for path, record in iter_catalog(root) or []:
        for err in validate_record(record):
            errors.append(f"{path}: {err}")
        rid = record.get("id")
        if isinstance(rid, str):
            if rid in seen_ids:
                errors.append(f"duplicate id {rid}: {seen_ids[rid]} and {path}")
            else:
                seen_ids[rid] = path
        key = dedupe_key(record)
        if all(key):
            if key in seen_sources:
                errors.append(f"duplicate source identity {key}: {seen_sources[key]} and {path}")
            else:
                seen_sources[key] = path
        digest = (record.get("archive") or {}).get("sha256")
        if digest:
            if digest in seen_hashes:
                errors.append(f"duplicate binary sha256 {digest}: {seen_hashes[digest]} and {path}")
            else:
                seen_hashes[digest] = path
        records.append(record)

    records.sort(key=lambda r: (str(r.get("asset_type")), str(r.get("title")).casefold(), str(r.get("id"))))
    index = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now_utc(),
        "record_count": len(records),
        "records": records,
    }
    return index, errors


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    index, errors = build_index(root)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    print(f"Asset Vault valid: {index['record_count']} records")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    index, errors = build_index(root)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    out = root / args.output
    dump_json(out, index)
    print(f"Wrote {out} with {index['record_count']} records")
    return 0


def match(record: dict[str, Any], query: str, asset_type: str | None, commercial: bool, no_attribution: bool, android: bool) -> bool:
    if asset_type and record.get("asset_type") != asset_type:
        return False
    lic = record.get("license") or {}
    if commercial and lic.get("commercial_use") is not True:
        return False
    if no_attribution and lic.get("attribution_required") is not False:
        return False
    if android and (record.get("compatibility") or {}).get("android") is not True:
        return False
    if not query:
        return True
    haystack = " ".join(str(x) for x in [record.get("title"), record.get("asset_type"), *(record.get("themes") or []), *(record.get("styles") or []), *(record.get("tags") or [])]).casefold()
    return all(token.casefold() in haystack for token in query.split())


def cmd_query(args: argparse.Namespace) -> int:
    index = load_json(Path(args.index))
    records = index.get("records", [])
    selected = [r for r in records if match(r, args.query or "", args.type, args.commercial, args.no_attribution, args.android)]
    for record in selected[: args.limit]:
        print(json.dumps({
            "id": record.get("id"), "title": record.get("title"), "type": record.get("asset_type"),
            "provider": (record.get("source") or {}).get("provider"), "url": (record.get("source") or {}).get("asset_url"),
            "license": (record.get("license") or {}).get("name")
        }, ensure_ascii=False))
    return 0


def polyhaven_record(external_id: str, meta: dict[str, Any]) -> dict[str, Any]:
    asset_type = str(meta.get("type") or meta.get("asset_type") or "unknown")
    tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
    categories = meta.get("categories") or meta.get("category")
    if isinstance(categories, str):
        categories = [categories]
    if not isinstance(categories, list):
        categories = []
    authors = meta.get("authors")
    author = None
    if isinstance(authors, dict):
        author = ", ".join(str(v) for v in authors.values())
    elif isinstance(authors, list):
        author = ", ".join(str(v) for v in authors)
    return {
        "schema_version": 1,
        "id": stable_id("POLYHAVEN", external_id),
        "title": meta.get("name") or external_id,
        "asset_type": asset_type,
        "dimensions": ["2_5d", "3d"] if asset_type in {"models", "model"} else ["shared", "2d", "2_5d", "3d"],
        "themes": categories,
        "styles": [],
        "tags": tags,
        "source": {
            "provider": "Poly Haven",
            "author": author,
            "external_id": external_id,
            "asset_url": f"https://polyhaven.com/a/{external_id}",
            "download_url": None,
            "acquired_at": now_utc(),
        },
        "license": {
            "name": "CC0-1.0",
            "version": "1.0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "commercial_use": True,
            "modification": True,
            "attribution_required": False,
            "redistribution_allowed": True,
            "share_alike": False,
            "ai_training_allowed": True,
            "notes": "Asset license is CC0. Live API usage has separate service attribution/User-Agent terms.",
        },
        "technical": {
            "formats": [], "texture_resolution": None, "triangle_count": meta.get("polycount"),
            "rigged": None, "animated": None, "animation_count": None, "pbr": asset_type in {"textures", "texture", "models", "model"},
            "lods": None, "collision": None, "audio_sample_rate": None, "audio_channels": None, "font_formats": []
        },
        "compatibility": {"godot": True, "unreal": True, "unity": True, "web": True, "android": True},
        "archive": {"mirrored_in_arcont": False, "local_path": None, "sha256": None, "size_bytes": None},
        "review": {"license_verified": True, "metadata_verified": False, "last_checked": now_utc(), "notes": "Imported from Poly Haven public API metadata."},
    }


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def cmd_polyhaven_sync(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    data = fetch_json(POLYHAVEN_API)
    if not isinstance(data, dict):
        print("ERROR: Poly Haven API returned unexpected payload", file=sys.stderr)
        return 1
    target = root / "assets" / "catalog" / "polyhaven"
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    for external_id, meta in sorted(data.items()):
        if args.limit is not None and count >= args.limit:
            break
        if not isinstance(meta, dict):
            continue
        record = polyhaven_record(external_id, meta)
        dump_json(target / f"{external_id}.asset.json", record)
        count += 1
    print(f"Synced {count} Poly Haven metadata records into {target}")
    return 0


def cmd_ingest_manifest(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    payload = load_json(Path(args.file))
    records = payload if isinstance(payload, list) else payload.get("records", []) if isinstance(payload, dict) else []
    if not isinstance(records, list):
        print("ERROR: manifest must be a JSON array or {records:[...]}", file=sys.stderr)
        return 1
    target = root / "assets" / "catalog" / args.provider.lower().replace(" ", "-")
    target.mkdir(parents=True, exist_ok=True)
    written = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        errors = validate_record(record)
        if errors:
            print(f"ERROR: manifest record rejected: {'; '.join(errors)}", file=sys.stderr)
            return 1
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", str(record["id"]))
        dump_json(target / f"{name}.asset.json", record)
        written += 1
    print(f"Ingested {written} records into {target}")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ARCONT Asset Vault indexer")
    sub = p.add_subparsers(dest="command", required=True)

    for name in ("validate", "build"):
        sp = sub.add_parser(name)
        sp.add_argument("--root", default=".")
        if name == "build":
            sp.add_argument("--output", default="assets/index.json")
        sp.set_defaults(func=cmd_validate if name == "validate" else cmd_build)

    q = sub.add_parser("query")
    q.add_argument("--index", default="assets/index.json")
    q.add_argument("query", nargs="?", default="")
    q.add_argument("--type")
    q.add_argument("--commercial", action="store_true")
    q.add_argument("--no-attribution", action="store_true")
    q.add_argument("--android", action="store_true")
    q.add_argument("--limit", type=int, default=25)
    q.set_defaults(func=cmd_query)

    ph = sub.add_parser("polyhaven-sync")
    ph.add_argument("--root", default=".")
    ph.add_argument("--limit", type=int)
    ph.set_defaults(func=cmd_polyhaven_sync)

    im = sub.add_parser("ingest-manifest")
    im.add_argument("file")
    im.add_argument("--provider", required=True)
    im.add_argument("--root", default=".")
    im.set_defaults(func=cmd_ingest_manifest)
    return p


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
