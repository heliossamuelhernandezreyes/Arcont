#!/usr/bin/env python3
"""ARCONT engine-neutral bridge: mission anchors must match authored map anchors.

This is data reconciliation, NOT a physics/navmesh/pathfinding validation.
Neither Godot nor any game's production scripts are imported by ARCONT.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from map_forge_contract import validate_contract as validate_map
from vertical_slice_contract import validate_contract as validate_mission


def validate_pair(mission: Any, world: Any, world_path: str | None = None) -> list[str]:
    errors = []
    mission_errors = validate_mission(mission)
    map_errors = validate_map(world)
    if mission_errors:
        errors.extend("mission: " + e for e in mission_errors)
    if map_errors:
        errors.extend("map: " + e for e in map_errors)
    if errors:
        return errors
    assert isinstance(mission, dict) and isinstance(world, dict)
    ref = str(mission["map"]["ref"]).replace("\\", "/")
    if world_path and not world_path.replace("\\", "/").endswith(ref):
        errors.append(f"map.ref '{ref}' does not match provided map path '{world_path}'")
    for axis in ("width", "depth"):
        if abs(float(mission["map"]["bounds"][axis]) - float(world["bounds"][axis])) > 0.01:
            errors.append(f"map.bounds.{axis}: mission and world disagree")

    map_anchors = {str(item["id"]): item for item in world.get("anchors", []) if isinstance(item, dict)}
    mission_anchors = mission.get("anchors", [])
    for mission_anchor in mission_anchors:
        aid = str(mission_anchor["id"])
        if aid not in map_anchors:
            errors.append(f"anchor.{aid}: missing from game-authored map")
            continue
        map_anchor = map_anchors[aid]
        got = map_anchor.get("position")
        expect = mission_anchor.get("position")
        if not isinstance(got, list) or len(got) != 3:
            errors.append(f"anchor.{aid}: map position malformed")
        elif any(abs(float(x)-float(y)) > 0.11 for x, y in zip(got,expect)):
            errors.append(f"anchor.{aid}: spatial mismatch mission vs map")
        role = mission_anchor.get("kind")
        if role in ("enemy_spawn","player_spawn"):
            wanted = "enemy" if role == "enemy_spawn" else "player"
            if map_anchor.get("kind") != "spawn" or map_anchor.get("team") != wanted:
                errors.append(f"anchor.{aid}: invalid spawn team mapping (expected {wanted})")
        if role == "extraction" and map_anchor.get("kind") != "extraction":
            errors.append(f"anchor.{aid}: mission extraction should be map extraction")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mission", type=Path)
    parser.add_argument("map", type=Path)
    args = parser.parse_args()
    try:
        mission = json.loads(args.mission.read_text(encoding="utf-8"))
        world = json.loads(args.map.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("MISSION MAP FAIL:", exc)
        return 1
    errors = validate_pair(mission, world, args.map.as_posix())
    if errors:
        for error in errors:
            print("MISSION MAP FAIL:", error)
        return 1
    print("MISSION MAP PASS anchors=%d map=%s (semantic only; no path/physics/AAA claim)" %
        (len(mission["anchors"]), mission["map"]["ref"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
