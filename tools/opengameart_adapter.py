#!/usr/bin/env python3
"""Index vetted OpenGameArt metadata into the ARCONT Asset Vault.

The source registry is discovery-only. Every official asset page is fetched at
runtime and its license is classified by tools/license_policy.py. By default,
only GREEN licenses are written to the canonical catalog.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from asset_vault_indexer import dump_json, load_json, now_utc, stable_id
from license_policy import classify

USER_AGENT = "ARCONT-Asset-Vault/1.0 (+https://github.com/heliossamuelhernandezreyes/Arcont)"
HOSTS = {"opengameart.org", "www.opengameart.org"}


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.h1: list[str] = []
        self._in_h1 = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "h1":
            self._in_h1 = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "h1":
            self._in_h1 = False

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if not value:
            return
        self.text.append(value)
        if self._in_h1:
            self.h1.append(value)


def fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def official_slug(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() not in HOSTS:
        return None
    m = re.fullmatch(r"/content/([A-Za-z0-9._~-]+)", parsed.path.rstrip("/"))
    return m.group(1).lower() if m else None


def parser(raw: str) -> Parser:
    p = Parser()
    p.feed(raw)
    return p


def values_between(tokens: list[str], label: str, stop_labels: set[str]) -> list[str]:
    wanted = label.lower().rstrip(":")
    for i, token in enumerate(tokens):
        if token.lower().rstrip(":") != wanted:
            continue
        out: list[str] = []
        for value in tokens[i + 1 :]:
            key = value.lower().rstrip(":")
            if key in stop_labels:
                break
            if value:
                out.append(value)
        return out
    return []


def first_after(tokens: list[str], label: str, stop_labels: set[str]) -> str | None:
    values = values_between(tokens, label, stop_labels)
    return values[0] if values else None


def infer_type(art_type: str | None, tags: list[str]) -> tuple[str, list[str]]:
    text = " ".join([art_type or "", *tags]).lower()
    if "music" in text or "sound" in text or "audio" in text:
        return "audio", ["shared", "2d", "2_5d", "3d"]
    if "3d" in text:
        return "model", ["3d", "2_5d"]
    if "texture" in text:
        return "texture", ["shared", "2d", "2_5d", "3d"]
    if "font" in text:
        return "font", ["shared", "2d", "2_5d", "3d"]
    if "ui" in text or "gui" in text:
        return "ui", ["shared", "2d", "2_5d", "3d"]
    if "2d" in text or "sprite" in text or "tile" in text or "pixel" in text:
        return "2d_asset", ["2d", "2_5d"]
    return "game_asset", ["shared", "2d", "2_5d", "3d"]


def detect_license(tokens: list[str], stop_labels: set[str]) -> tuple[str | None, Any | None]:
    values = values_between(tokens, "License(s)", stop_labels)
    joined = " | ".join(values[:6])
    policy = classify(joined)
    return joined or None, policy


def parse_record(url: str, raw: str) -> tuple[dict[str, Any] | None, str]:
    slug = official_slug(url)
    if not slug:
        return None, "invalid_official_url"
    p = parser(raw)
    stops = {
        "author", "art type", "tags", "license(s)", "collections", "favorites", "preview",
        "copyright/attribution notice", "attribution instructions", "file(s)", "comments",
    }
    license_raw, policy = detect_license(p.text, stops)
    if policy is None:
        return None, f"unknown_license:{license_raw or 'missing'}"
    if policy.tier != "green" or not policy.portable_commercial_default:
        return None, f"policy_{policy.tier}:{policy.canonical_name}"

    title = " ".join(p.h1).strip() or slug.replace("-", " ").title()
    author = first_after(p.text, "Author", stops)
    art_type = first_after(p.text, "Art Type", stops)
    tags = values_between(p.text, "Tags", stops)
    files = values_between(p.text, "File(s)", {"comments"})
    asset_type, dimensions = infer_type(art_type, tags)

    file_count = 0
    for item in files:
        if re.search(r"\b(image|audio|application|model|text)/", item, re.IGNORECASE):
            file_count += 1
    if not file_count:
        file_count = None

    license_data = {
        "name": policy.canonical_name,
        "version": "1.0" if policy.canonical_name == "CC0-1.0" else None,
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/" if policy.canonical_name == "CC0-1.0" else None,
        "commercial_use": policy.commercial_use,
        "modification": policy.modification,
        "attribution_required": policy.attribution_required,
        "redistribution_allowed": policy.redistribution_allowed,
        "share_alike": policy.share_alike,
        "ai_training_allowed": None,
        "policy_tier": policy.tier,
        "drm_risk": policy.drm_risk,
        "portable_commercial_default": policy.portable_commercial_default,
        "notes": policy.notes,
        "source_label": license_raw,
    }

    record = {
        "schema_version": 1,
        "id": stable_id("OPENGAMEART", slug),
        "title": html.unescape(title),
        "asset_type": asset_type,
        "dimensions": dimensions,
        "themes": [art_type] if art_type else [],
        "styles": [],
        "tags": [t.lower() for t in tags[:64]],
        "source": {
            "provider": "OpenGameArt",
            "author": author,
            "external_id": slug,
            "asset_url": url,
            "download_url": None,
            "acquired_at": now_utc(),
        },
        "license": license_data,
        "technical": {
            "formats": [], "texture_resolution": None, "triangle_count": None,
            "rigged": None, "animated": None, "animation_count": None, "pbr": None,
            "lods": None, "collision": None, "audio_sample_rate": None, "audio_channels": None,
            "font_formats": [], "pack_file_count": file_count, "art_type_raw": art_type,
        },
        "compatibility": {"godot": True, "unreal": True, "unity": True, "web": True, "android": True},
        "archive": {"mirrored_in_arcont": False, "local_path": None, "sha256": None, "size_bytes": None},
        "review": {
            "license_verified": True,
            "metadata_verified": True,
            "last_checked": now_utc(),
            "notes": "Official OpenGameArt page re-fetched at sync time; automatic ingestion allowed only by GREEN license policy.",
        },
        "opengameart_metadata": {"art_type": art_type, "file_count": file_count, "license_raw": license_raw},
    }
    return record, "accepted"


def stable_merge(path: Path, record: dict[str, Any]) -> bool:
    if not path.exists():
        dump_json(path, record)
        return True
    old = load_json(path)
    record["source"]["acquired_at"] = (old.get("source") or {}).get("acquired_at") or record["source"]["acquired_at"]
    record["review"]["last_checked"] = (old.get("review") or {}).get("last_checked") or record["review"]["last_checked"]
    if old == record:
        return False
    record["review"]["last_checked"] = now_utc()
    dump_json(path, record)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Index license-gated OpenGameArt metadata")
    ap.add_argument("--root", default=".")
    ap.add_argument("--seeds", default="assets/sources/opengameart-seeds.json")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    seed_path = root / args.seeds
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    urls = data.get("assets", []) if isinstance(data, dict) else []
    if not isinstance(urls, list):
        print("ERROR: OpenGameArt seed registry must contain an assets array")
        return 1
    if args.limit is not None:
        urls = urls[: args.limit]

    target = root / "assets" / "catalog" / "opengameart"
    target.mkdir(parents=True, exist_ok=True)
    changed = 0
    skipped = 0
    reasons: dict[str, int] = {}
    for i, url in enumerate(urls):
        try:
            record, reason = parse_record(str(url), fetch_text(str(url)))
            if record is None:
                skipped += 1
                reasons[reason] = reasons.get(reason, 0) + 1
                print(f"SKIP {url}: {reason}")
            else:
                slug = official_slug(str(url))
                if stable_merge(target / f"{slug}.asset.json", record):
                    changed += 1
        except Exception as exc:
            skipped += 1
            key = f"error:{type(exc).__name__}"
            reasons[key] = reasons.get(key, 0) + 1
            print(f"WARN {url}: {exc}")
        if i + 1 < len(urls):
            time.sleep(0.15)

    print(f"OpenGameArt: {len(urls)} seeds considered, {changed} changed, {skipped} skipped")
    if reasons:
        print("Skip reasons: " + ", ".join(f"{k}={v}" for k, v in sorted(reasons.items())))
    return 0 if skipped == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
