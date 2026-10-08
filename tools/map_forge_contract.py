#!/usr/bin/env python3
"""ARCONT Map Forge contract validator.

This tool validates engine-neutral semantic map contracts. It intentionally does
not import Godot, Terrain3D, Cyclops, ProtonScatter, FuncGodot, or any game code.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL = ("version", "id", "bounds", "anchors", "routes", "regions", "authoring")


def _vec3(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 3
        and all(_finite_number(v) for v in value)
    )


def _positive_number(value: Any) -> bool:
    return _finite_number(value) and value > 0


def _finite_number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def validate_contract(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be an object"]

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"missing top-level key '{key}'")

    if type(data.get("version")) is not int or data["version"] < 1:
        errors.append("version must be an integer >= 1")

    map_id = data.get("id")
    if not isinstance(map_id, str) or not map_id.strip():
        errors.append("id must be a non-empty string")

    bounds = data.get("bounds")
    if not isinstance(bounds, dict):
        errors.append("bounds must be an object")
    else:
        for axis in ("width", "depth"):
            if not _positive_number(bounds.get(axis)):
                errors.append(f"bounds.{axis} must be a finite positive number")
        if "height" in bounds and not _positive_number(bounds["height"]):
            errors.append("bounds.height must be a finite positive number")
    if "display_name" in data and not isinstance(data["display_name"], str):
        errors.append("display_name must be a string")

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
                not _finite_number(anchor["radius"]) or anchor["radius"] < 0
            ):
                errors.append(f"anchors[{index}].radius must be finite and nonnegative")
            if "team" in anchor and anchor["team"] is not None and not isinstance(anchor["team"], str):
                errors.append(f"anchors[{index}].team must be a string or null for neutral anchors")

    routes = data.get("routes", [])
    if isinstance(routes, list):
        for index, route in enumerate(routes):
            if not isinstance(route, dict):
                continue
            if not isinstance(route.get("kind"), str) or not route.get("kind", "").strip():
                errors.append(f"routes[{index}].kind must be non-empty")
            if not _positive_number(route.get("width")):
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
            if "width" in region and not _positive_number(region["width"]):
                errors.append(f"regions[{index}].width must be positive")
            if "radius" in region and (not _finite_number(region["radius"]) or region["radius"] < 0):
                errors.append(f"regions[{index}].radius must be finite and nonnegative")

    authoring = data.get("authoring")
    if not isinstance(authoring, dict):
        errors.append("authoring must be an object")
    else:
        for collection in ("structure_guides", "scatter_zones"):
            if collection in authoring and not isinstance(authoring[collection], list):
                errors.append(f"authoring.{collection} must be an array")
            elif collection in authoring and not all(isinstance(item, dict) for item in authoring[collection]):
                errors.append(f"authoring.{collection} items must be objects")
        providers = authoring.get("providers")
        if "providers" in authoring and not isinstance(providers, dict):
            errors.append("authoring.providers must be an object when present")
        elif isinstance(providers, dict) and any(v is not None and not isinstance(v, str) for v in providers.values()):
            errors.append("authoring.providers values must be strings or null")
        if "terrain" in authoring and not isinstance(authoring["terrain"], dict):
            errors.append("authoring.terrain must be an object")

        navigation = authoring.get("navigation")
        if "navigation" in authoring:
            if not isinstance(navigation, dict):
                errors.append("authoring.navigation must be an object when present")
            else:
                for field in ("agent_radius", "agent_height", "cell_size", "cell_height"):
                    if field in navigation and not _positive_number(navigation[field]):
                        errors.append(f"authoring.navigation.{field} must be a finite positive number")
                if "agent_max_climb" in navigation:
                    value = navigation["agent_max_climb"]
                    if not _finite_number(value) or value < 0:
                        errors.append("authoring.navigation.agent_max_climb must be finite and >= 0")
                if "agent_max_slope" in navigation:
                    value = navigation["agent_max_slope"]
                    if not _finite_number(value) or not 0 <= value <= 90:
                        errors.append("authoring.navigation.agent_max_slope must be between 0 and 90")

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
