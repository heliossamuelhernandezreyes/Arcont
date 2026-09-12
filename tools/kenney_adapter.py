#!/usr/bin/env python3
"""Index Kenney game-asset metadata into the ARCONT Asset Vault.

The adapter is intentionally metadata-only. It discovers public asset pages from
Kenney's paginated catalog and indexes only pages that explicitly state a
Creative Commons CC0 license. Asset binaries remain upstream.
"""

from __future__ import annotations

import argparse
import html
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from asset_vault_indexer import dump_json, load_json, now_utc, stable_id

BASE = "https://kenney.nl"
CATALOG = f"{BASE}/assets"
USER_AGENT = "ARCONT-Asset-Vault/1.0 (+https://github.com/heliossamuelhernandezreyes/Arcont)"

CC0 = {
    "name": "CC0-1.0",
    "version": "1.0",
    "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
    "commercial_use": True,
    "modification": True,
    "attribution_required": False,
    "redistribution_allowed": True,
    "share_alike": False,
    "ai_training_allowed": None,
    "notes": "Kenney states game assets on its asset pages are public-domain licensed (CC0); attribution is not required. This adapter additionally requires the individual asset page to contain an explicit Creative Commons CC0 marker before indexing it.",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.text: list[str] = []
        self.h1: list[str] = []
        self._in_h1 = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "h1":
            self._in_h1 = True
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

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
    with urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_page(raw: str) -> PageParser:
    parser = PageParser()
    parser.feed(raw)
    return parser


def slug_from_link(href: str) -> str | None:
    absolute = urljoin(BASE + "/", href)
    parsed = urlparse(absolute)
    if parsed.netloc.lower() not in {"kenney.nl", "www.kenney.nl"}:
        return None
    match = re.fullmatch(r"/assets/([a-z0-9][a-z0-9-]*)/?", parsed.path, re.IGNORECASE)
    return match.group(1).lower() if match else None


def discover_asset_slugs(max_pages: int = 100) -> list[str]:
    slugs: set[str] = set()
    empty_pages = 0
    for page in range(1, max_pages + 1):
        url = CATALOG if page == 1 else f"{CATALOG}/page:{page}"
        parser = parse_page(fetch_text(url))
        before = len(slugs)
        for href in parser.links:
            slug = slug_from_link(href)
            if slug:
                slugs.add(slug)
        if len(slugs) == before:
            empty_pages += 1
        else:
            empty_pages = 0
        if empty_pages >= 2:
            break
        time.sleep(0.10)
    return sorted(slugs)


def value_after(tokens: list[str], label: str) -> str | None:
    label_l = label.lower()
    for index, token in enumerate(tokens):
        if token.lower().rstrip(":") == label_l:
            for value in tokens[index + 1 : index + 5]:
                if value and value.lower().rstrip(":") not in {"tags", "category", "files", "license", "tile size", "features", "updates"}:
                    return value
    return None


def infer_type(category: str | None) -> tuple[str, list[str]]:
    text = (category or "").lower()
    if "audio" in text:
        return "audio", ["shared", "2d", "2_5d", "3d"]
    if "3d" in text:
        return "model", ["3d", "2_5d"]
    if "texture" in text:
        return "texture", ["shared", "2d", "2_5d", "3d"]
    if "ui" in text:
        return "ui", ["shared", "2d", "2_5d", "3d"]
    if "2d" in text or "pixel" in text:
        return "2d_asset", ["2d", "2_5d"]
    return "game_asset_pack", ["shared", "2d", "2_5d", "3d"]


def split_categories(category: str | None) -> list[str]:
    if not category:
        return []
    normalized = category.replace("•", "|")
    return [part.strip() for part in normalized.split("|") if part.strip()]


def parse_record(slug: str, raw: str) -> dict[str, Any] | None:
    parser = parse_page(raw)
    joined = " ".join(parser.text)
    if "Creative Commons CC0" not in joined:
        return None

    title = " ".join(parser.h1).strip() or slug.replace("-", " ").title()
    tags_raw = value_after(parser.text, "Tags")
    category_raw = value_after(parser.text, "Category")
    files_raw = value_after(parser.text, "Files")
    tile_size = value_after(parser.text, "Tile size")
    features = value_after(parser.text, "Features")

    tags = ["kenney"]
    if tags_raw:
        tags.append(tags_raw.lower())

    categories = split_categories(category_raw)
    asset_type, dimensions = infer_type(category_raw)
    file_count = None
    if files_raw:
        m = re.search(r"(\d+)", files_raw.replace(",", ""))
        if m:
            file_count = int(m.group(1))

    page_url = f"{BASE}/assets/{slug}"
    return {
        "schema_version": 1,
        "id": stable_id("KENNEY", slug),
        "title": html.unescape(title),
        "asset_type": asset_type,
        "dimensions": dimensions,
        "themes": categories,
        "styles": [],
        "tags": tags,
        "source": {
            "provider": "Kenney",
            "author": "Kenney",
            "external_id": slug,
            "asset_url": page_url,
            "download_url": None,
            "acquired_at": now_utc(),
        },
        "license": dict(CC0),
        "technical": {
            "formats": [],
            "texture_resolution": tile_size,
            "triangle_count": None,
            "rigged": None,
            "animated": True if features and "animation" in features.lower() else None,
            "animation_count": None,
            "pbr": None,
            "lods": None,
            "collision": None,
            "audio_sample_rate": None,
            "audio_channels": None,
            "font_formats": [],
            "pack_file_count": file_count,
            "category_raw": category_raw,
            "features_raw": features,
        },
        "compatibility": {"godot": True, "unreal": True, "unity": True, "web": True, "android": True},
        "archive": {"mirrored_in_arcont": False, "local_path": None, "sha256": None, "size_bytes": None},
        "review": {
            "license_verified": True,
            "metadata_verified": True,
            "last_checked": now_utc(),
            "notes": "Metadata extracted from the individual official Kenney asset page. Record created only when that page explicitly states Creative Commons CC0.",
        },
        "kenney_metadata": {
            "category": categories,
            "tile_size": tile_size,
            "features": features,
            "file_count": file_count,
        },
    }


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
    ap = argparse.ArgumentParser(description="Index official Kenney CC0 asset metadata")
    ap.add_argument("--root", default=".")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--max-pages", type=int, default=100)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    target = root / "assets" / "catalog" / "kenney"
    target.mkdir(parents=True, exist_ok=True)

    slugs = discover_asset_slugs(args.max_pages)
    if args.limit is not None:
        slugs = slugs[: args.limit]

    changed = 0
    skipped = 0
    for index, slug in enumerate(slugs, start=1):
        try:
            raw = fetch_text(f"{BASE}/assets/{slug}")
            record = parse_record(slug, raw)
            if record is None:
                skipped += 1
                continue
            if stable_merge(target / f"{slug}.asset.json", record):
                changed += 1
        except Exception as exc:
            skipped += 1
            print(f"WARN {slug}: {exc}")
        if index < len(slugs):
            time.sleep(0.10)

    print(f"Kenney: {len(slugs)} asset pages considered, {changed} changed, {skipped} skipped")
    return 0 if skipped == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
