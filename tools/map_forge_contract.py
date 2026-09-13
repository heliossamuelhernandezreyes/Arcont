#!/usr/bin/env python3
"""ARCONT Map Forge contract validator.

This tool validates engine-neutral semantic map contracts. It intentionally does
not import Godot, Terrain3D, Cyclops, ProtonScatter, FuncGodot, or any game code.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL = ("version", "id", "bounds", "anchors", "routes", "regions", "authoring")


def _vec3(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 3
        and all(isinstance(v, (int, float)) and math.isfinite(float(v)) for v in value)
    )


def validate_contract(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"missing top-level key '{key}'")

    if not isinstance(data.get("version"), int) or int(data.get("version", 0)) < 1:
        errors.append("version must be an integer >= 1")

    map_id = data.get("id")
    if not isinstance(map_id, str) or not map_id.strip():
        errors.append("id must be a non-empty string")

    bounds = data.get("bounds")
    if not isinstance(bounds, dict):
        errors.append("bounds must be an object")
    else:
        for axis in ("width", "depth"):
            value = bounds.get(axis)
            if not isinstance(value, (int, float)) or float(value) <= 0 or not math.isfinite(float(value)):
                errors.append(f"bounds.{axis} must be a finite positive number")

    seen: set[str] = set()
    for collection in ("anchors", "routes", "regions"):
        values = data.get(collection)
        if not isinstance(values, list):
            errors.append(f"{collection} must be an array")
            continue
        for index, value in enumerate(values):
            if not isinstance(value, dict):
                errors.append(f"{collection}[{index}] must be an object")
                continue
            item_id = value.get("id")
            if not isinstance(item_id, str) or not item_id.strip():
                errors.append(f"{collection}[{index}] requires a non-empty id")
            elif item_id in seen:
                errors.append(f"duplicate semantic id '{item_id}'")
            else:
                seen.add(item_id)

    anchors = data.get("anchors", [])
    if isinstance(anchors, list):
        for index, anchor in enumerate(anchors):
            if not isinstance(anchor, dict):
                continue
            if not isinstance(anchor.get("kind"), str) or not anchor.get("kind", "").strip():
                errors.append(f"anchors[{index}].kind must be non-empty")
            if not _vec3(anchor.get("position")):
                errors.append(f"anchors[{index}].position must be [x,y,z]")
            if "radius" in anchor and (
                not isinstance(anchor["radius"], (int, float)) or float(anchor["radius"]) < 0
            ):
                errors.append(f"anchors[{index}].radius cannot be negative")

    routes = data.get("routes", [])
    if isinstance(routes, list):
        for index, route in enumerate(routes):
            if not isinstance(route, dict):
                continue
            if not isinstance(route.get("kind"), str) or not route.get("kind", "").strip():
                errors.append(f"routes[{index}].kind must be non-empty")
            width = route.get("width")
            if not isinstance(width, (int, float)) or float(width) <= 0:
                errors.append(f"routes[{index}].width must be positive")
            points = route.get("points")
            if not isinstance(points, list) or len(points) < 2 or not all(_vec3(p) for p in points):
                errors.append(f"routes[{index}].points requires at least two valid [x,y,z] points")

    regions = data.get("regions", [])
    if isinstance(regions, list):
        for index, region in enumerate(regions):
            if not isinstance(region, dict):
                continue
            if not isinstance(region.get("kind"), str) or not region.get("kind", "").strip():
                errors.append(f"regions[{index}].kind must be non-empty")
            if not _vec3(region.get("center")):
                errors.append(f"regions[{index}].center must be [x,y,z]")
            if "size" in region and not _vec3(region["size"]):
                errors.append(f"regions[{index}].size must be [x,y,z]")
            if "width" in region and (
                not isinstance(region["width"], (int, float)) or float(region["width"]) <= 0
            ):
                errors.append(f"regions[{index}].width must be positive")

    authoring = data.get("authoring")
    if not isinstance(authoring, dict):
        errors.append("authoring must be an object")
    else:
        for collection in ("structure_guides", "scatter_zones"):
            if collection in authoring and not isinstance(authoring[collection], list):
                errors.append(f"authoring.{collection} must be an array")
        providers = authoring.get("providers")
        if providers is not None and not isinstance(providers, dict):
            errors.append("authoring.providers must be an object when present")

    return errors


def validate_path(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI should report parse failures
        return [f"invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return ["root must be an object"]
    return validate_contract(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ARCONT Map Forge semantic contracts")
    parser.add_argument("paths", nargs="+", type=Path, help="JSON map contracts to validate")
    args = parser.parse_args()

    failed = 0
    for path in args.paths:
        errors = validate_path(path)
        if errors:
            failed += 1
            print(f"FAIL {path}")
            for error in errors:
                print(f"  ERROR: {error}")
        else:
            print(f"PASS {path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
