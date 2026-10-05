#!/usr/bin/env python3
"""Audit a Godot 2D sprite manifest using only the Python standard library."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


def _parse_svg_dimension(value: str | None) -> int | None:
    if not value:
        return None
    match = re.match(r"^\s*(\d+(?:\.\d+)?)", value)
    if not match:
        return None
    return int(round(float(match.group(1))))


def _resolve_resource(project_root: Path, resource_path: str) -> Path:
    if not resource_path.startswith("res://"):
        raise ValueError(f"resource path must start with res://: {resource_path}")
    return project_root / resource_path.removeprefix("res://")


def audit(manifest_path: Path, project_root: Path) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    characters = manifest.get("characters", {})
    errors: list[str] = []
    warnings: list[str] = []
    checked = 0

    if not isinstance(characters, dict) or not characters:
        errors.append("manifest.characters must contain at least one character")

    for character_name, spec in characters.items():
        canvas = spec.get("canvas")
        baseline_y = spec.get("baseline_y")
        states = spec.get("states", {})
        if not (isinstance(canvas, list) and len(canvas) == 2 and all(isinstance(v, int) and v > 0 for v in canvas)):
            errors.append(f"{character_name}: invalid canvas declaration {canvas!r}")
            continue
        if not isinstance(baseline_y, (int, float)):
            errors.append(f"{character_name}: baseline_y must be numeric")
        elif not 0 <= float(baseline_y) <= canvas[1]:
            errors.append(f"{character_name}: baseline_y {baseline_y} outside canvas height {canvas[1]}")
        if not isinstance(states, dict) or not states:
            errors.append(f"{character_name}: no states declared")
            continue

        for state_name, resource_path in states.items():
            checked += 1
            if not isinstance(resource_path, str):
                errors.append(f"{character_name}.{state_name}: resource path is not a string")
                continue
            try:
                file_path = _resolve_resource(project_root, resource_path)
            except ValueError as exc:
                errors.append(f"{character_name}.{state_name}: {exc}")
                continue
            if not file_path.is_file():
                errors.append(f"{character_name}.{state_name}: missing file {file_path}")
                continue

            if file_path.suffix.lower() == ".svg":
                try:
                    root = ElementTree.parse(file_path).getroot()
                    width = _parse_svg_dimension(root.attrib.get("width"))
                    height = _parse_svg_dimension(root.attrib.get("height"))
                except Exception as exc:  # malformed source should fail the audit
                    errors.append(f"{character_name}.{state_name}: invalid SVG: {exc}")
                    continue
                if width is None or height is None:
                    warnings.append(f"{character_name}.{state_name}: SVG has no numeric width/height")
                elif [width, height] != canvas:
                    errors.append(
                        f"{character_name}.{state_name}: canvas {width}x{height} != declared {canvas[0]}x{canvas[1]}"
                    )

    print(json.dumps({
        "manifest": str(manifest_path),
        "project_root": str(project_root),
        "characters": len(characters) if isinstance(characters, dict) else 0,
        "states_checked": checked,
        "warnings": warnings,
        "errors": errors,
        "ok": not errors,
    }, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a Godot 2D sprite manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    return audit(args.manifest.resolve(), args.project_root.resolve())


if __name__ == "__main__":
    sys.exit(main())
