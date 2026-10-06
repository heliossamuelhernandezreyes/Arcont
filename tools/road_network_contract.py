#!/usr/bin/env python3
"""Validate explicit RoadGenerator source data, without choosing geometry."""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import sys


def validate(network):
    errors = []
    identifiers = set()

    def number(value, path, minimum=0, strict=False):
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < minimum or (strict and value == minimum)):
            errors.append(f"{path}: requires a finite number {'>' if strict else '>='} {minimum}")
            return False
        return True

    def identifier(value, path):
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value):
            errors.append(f"{path}: requires a stable Godot-safe identifier")
        elif value in identifiers:
            errors.append(f"{path}: duplicate identifier {value}")
        else:
            identifiers.add(value)

    def vector(value, path, tangent=False):
        if not isinstance(value, list) or len(value) != 3:
            errors.append(f"{path}: requires [x, y, z]")
            return
        good = all(number(v, f"{path}/{i}", minimum=-math.inf) for i, v in enumerate(value))
        if good and tangent and value[0] ** 2 + value[2] ** 2 < 1e-12:
            errors.append(f"{path}: tangent must have a horizontal component")

    if not isinstance(network, dict) or network.get("version") != 1 or isinstance(network.get("version"), bool):
        return ["network requires version 1"]
    roads = network.get("roads")
    if not isinstance(roads, list) or not roads:
        return ["roads requires a non-empty array"]
    for i, road in enumerate(roads):
        path = f"roads/{i}"
        if not isinstance(road, dict):
            errors.append(f"{path}: requires an object")
            continue
        identifier(road.get("id"), path + "/id")
        lanes = road.get("lanes")
        if not isinstance(lanes, list) or not lanes or any(v not in ("forward", "reverse") for v in lanes):
            errors.append(f"{path}/lanes: requires ordered forward/reverse lanes")
        number(road.get("lane_width", 3.5), path + "/lane_width", strict=True)
        number(road.get("shoulder_width", 1.0), path + "/shoulder_width")
        number(road.get("thickness", 0.3), path + "/thickness")
        number(road.get("density", 2.0), path + "/density", strict=True)
        if not isinstance(road.get("closed", False), bool):
            errors.append(f"{path}/closed: requires a boolean")
        points = road.get("points")
        if not isinstance(points, list) or len(points) < (3 if road.get("closed") else 2):
            errors.append(f"{path}/points: insufficient points for this chain")
            continue
        for j, point in enumerate(points):
            prefix = f"{path}/points/{j}"
            if not isinstance(point, dict):
                errors.append(f"{prefix}: requires an object")
                continue
            identifier(point.get("id"), prefix + "/id")
            vector(point.get("position"), prefix + "/position")
            vector(point.get("tangent"), prefix + "/tangent", tangent=True)
            number(point.get("handle_in", 12.0), prefix + "/handle_in")
            number(point.get("handle_out", 12.0), prefix + "/handle_out")
    return errors


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else sys.stdin.read())
    errors = validate(data)
    print(json.dumps({"ok": not errors, "errors": errors}))
    raise SystemExit(bool(errors))
