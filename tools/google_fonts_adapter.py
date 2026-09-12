#!/usr/bin/env python3
"""Index Google Fonts family metadata into the ARCONT Asset Vault.

The adapter expects a local git clone of google/fonts. It reads METADATA.pb via
`git show`, so the clone may be partial/no-checkout and does not need font
binaries materialized in the working tree.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from asset_vault_indexer import dump_json, load_json, now_utc, stable_id

LICENSES: dict[str, dict[str, Any]] = {
    "ofl": {
        "name": "OFL-1.1",
        "version": "1.1",
        "license_url": "https://openfontlicense.org/",
        "commercial_use": True,
        "modification": True,
        "attribution_required": False,
        "redistribution_allowed": True,
        "share_alike": True,
        "ai_training_allowed": None,
        "notes": "SIL Open Font License. Redistribution/modification must preserve the applicable copyright/license terms; Reserved Font Names may apply per family.",
    },
    "apache": {
        "name": "Apache-2.0",
        "version": "2.0",
        "license_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "commercial_use": True,
        "modification": True,
        "attribution_required": False,
        "redistribution_allowed": True,
        "share_alike": False,
        "ai_training_allowed": None,
        "notes": "Apache-2.0 notice and attribution obligations apply on redistribution as specified by the license.",
    },
    "ufl": {
        "name": "Ubuntu-Font-License-1.0",
        "version": "1.0",
        "license_url": "https://ubuntu.com/legal/font-licence",
        "commercial_use": True,
        "modification": True,
        "attribution_required": False,
        "redistribution_allowed": True,
        "share_alike": True,
        "ai_training_allowed": None,
        "notes": "Ubuntu Font Licence terms apply; preserve the original license and copyright notices when redistributing font software.",
    },
}


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, stderr=subprocess.DEVNULL)


def quoted_values(text: str, field: str) -> list[str]:
    pattern = re.compile(rf'^\s*{re.escape(field)}:\s*"(.*)"\s*$', re.MULTILINE)
    return [m.group(1).replace('\\"', '"') for m in pattern.finditer(text)]


def scalar(text: str, field: str) -> str | None:
    vals = quoted_values(text, field)
    return vals[0] if vals else None


def parse_family(path: str, text: str) -> dict[str, Any]:
    parts = path.split("/")
    license_dir = parts[0].lower()
    family_slug = parts[1] if len(parts) > 1 else Path(path).parent.name
    lic = dict(LICENSES[license_dir])
    name = scalar(text, "name") or family_slug
    designers = quoted_values(text, "designer")
    categories = quoted_values(text, "category")
    subsets = quoted_values(text, "subsets")
    filenames = quoted_values(text, "filename")
    formats = sorted({Path(x).suffix.lower().lstrip(".") for x in filenames if Path(x).suffix})
    copyright_lines = quoted_values(text, "copyright")
    variable = bool(re.search(r'^\s*axes\s*\{', text, re.MULTILINE))

    record = {
        "schema_version": 1,
        "id": stable_id("GOOGLEFONTS", f"{license_dir}/{family_slug}"),
        "title": name,
        "asset_type": "font",
        "dimensions": ["shared", "2d", "2_5d", "3d"],
        "themes": categories,
        "styles": ["variable"] if variable else [],
        "tags": sorted(set(["font", "typography", license_dir, *[x.lower() for x in subsets]])),
        "source": {
            "provider": "Google Fonts",
            "author": ", ".join(designers) if designers else None,
            "external_id": f"{license_dir}/{family_slug}",
            "asset_url": f"https://github.com/google/fonts/tree/main/{license_dir}/{family_slug}",
            "download_url": None,
            "acquired_at": now_utc(),
        },
        "license": lic,
        "technical": {
            "formats": formats,
            "texture_resolution": None,
            "triangle_count": None,
            "rigged": None,
            "animated": None,
            "animation_count": None,
            "pbr": None,
            "lods": None,
            "collision": None,
            "audio_sample_rate": None,
            "audio_channels": None,
            "font_formats": formats,
            "font_variable": variable,
            "font_files": filenames,
        },
        "compatibility": {"godot": True, "unreal": True, "unity": True, "web": True, "android": True},
        "archive": {"mirrored_in_arcont": False, "local_path": None, "sha256": None, "size_bytes": None},
        "review": {
            "license_verified": True,
            "metadata_verified": True,
            "last_checked": now_utc(),
            "notes": "Metadata parsed from the official google/fonts METADATA.pb. Family directory license class is preserved; family copyright metadata should be retained for redistribution.",
        },
        "font_metadata": {
            "subsets": subsets,
            "copyright": copyright_lines,
            "metadata_path": path,
        },
    }
    return record


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
    ap = argparse.ArgumentParser(description="Index metadata from official google/fonts repository")
    ap.add_argument("repo", help="local google/fonts git clone")
    ap.add_argument("--root", default=".")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    root = Path(args.root).resolve()
    paths = git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
    metadata_paths = [p for p in paths if p.endswith("/METADATA.pb") and p.split("/", 1)[0] in LICENSES]
    metadata_paths.sort()
    if args.limit is not None:
        metadata_paths = metadata_paths[: args.limit]

    target = root / "assets" / "catalog" / "google-fonts"
    target.mkdir(parents=True, exist_ok=True)
    changed = 0
    skipped = 0

    for path in metadata_paths:
        try:
            text = git(repo, "show", f"HEAD:{path}")
            record = parse_family(path, text)
        except Exception:
            skipped += 1
            continue
        slug = record["source"]["external_id"].replace("/", "--")
        if stable_merge(target / f"{slug}.asset.json", record):
            changed += 1

    print(f"Google Fonts: {len(metadata_paths)} families considered, {changed} changed, {skipped} skipped")
    return 0 if skipped == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
