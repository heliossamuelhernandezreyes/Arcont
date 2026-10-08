#!/usr/bin/env python3
"""ARCONT: semantic vertical-slice mission contract validator.

Engine-neutral. Checks design structure and references, NOT Godot gameplay,
physical paths, encounter balance, visual quality, or Android performance.
No production game logic is allowed in this repository.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _number(value: Any, positive: bool = False) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and (not positive or value > 0)


def _identifier(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_contract(data: Any) -> list[str]:
    errors: list[str] = []
    def report(where: str, why: str) -> None:
        errors.append(f"{where}: {why}")

    if not isinstance(data, dict):
        return ["root: mission must be a JSON object"]
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        report("schema_version", "must be 1")
    for key in ("id", "title", "project"):
        if not _identifier(data.get(key)):
            report(key, "non-empty string required")
    if data.get("implementation_status") not in ("design_only", "in_development", "implemented"):
        report("implementation_status", "use design_only / in_development / implemented")

    duration = data.get("duration_minutes")
    if not isinstance(duration, dict) or not _number(duration.get("min"), True) or not _number(duration.get("max"), True):
        report("duration_minutes", "numeric positive min and max required")
    elif duration["min"] > duration["max"]:
        report("duration_minutes", "min cannot exceed max")

    world = data.get("map")
    bound_x = bound_z = None
    if not isinstance(world, dict):
        report("map", "object with ref/status/bounds required")
    else:
        if not _identifier(world.get("ref")):
            report("map.ref", "non-empty path required")
        if world.get("status") not in ("planned", "implemented"):
            report("map.status", "planned or implemented required")
        bounds = world.get("bounds")
        if not isinstance(bounds, dict) or not _number(bounds.get("width"), True) or not _number(bounds.get("depth"), True):
            report("map.bounds", "finite positive width and depth required")
        else:
            bound_x, bound_z = bounds["width"] / 2, bounds["depth"] / 2

    caps = data.get("caps")
    global_cap = wave_cap = None
    if not isinstance(caps, dict):
        report("caps", "caps object required")
    else:
        for name in ("global_hostiles", "preferred_mobile_hostiles", "spawns_per_wave"):
            if type(caps.get(name)) is not int or caps[name] <= 0:
                report(f"caps.{name}", "positive integer required")
        if all(type(caps.get(k)) is int and caps[k] > 0 for k in ("global_hostiles", "preferred_mobile_hostiles", "spawns_per_wave")):
            global_cap = caps["global_hostiles"]
            wave_cap = caps["spawns_per_wave"]
            if caps["preferred_mobile_hostiles"] > global_cap:
                report("caps", "preferred_mobile_hostiles exceeds global_hostiles")
            if wave_cap > global_cap:
                report("caps", "spawns_per_wave exceeds global_hostiles")

    # IDs are unique globally to avoid contradictory anchor/phase/objective references.
    records: dict[str, dict[str, Any]] = {}
    sets: dict[str, dict[str, dict[str, Any]]] = {}
    for collection in ("zones", "anchors", "roles", "objectives", "phases", "encounters", "transitions", "qa_gates"):
        values = data.get(collection)
        if not isinstance(values, list):
            report(collection, "array required")
            sets[collection] = {}
            continue
        items: dict[str, dict[str, Any]] = {}
        for index, item in enumerate(values):
            where = f"{collection}[{index}]"
            if not isinstance(item, dict):
                report(where, "must be an object")
                continue
            if collection == "transitions":
                continue
            identifier = item.get("id")
            if not _identifier(identifier):
                report(where, "non-empty id required")
            elif identifier in records:
                report(where, f"duplicate global id '{identifier}' also in {records[identifier]['collection']}")
            else:
                items[identifier] = item
                records[identifier] = {"collection": collection}
        sets[collection] = items

    zones = sets["zones"]
    for zid, zone in zones.items():
        rect = zone.get("rect")
        if not isinstance(rect, dict):
            report(f"zone.{zid}", "rect missing")
            continue
        vals = [rect.get(k) for k in ("min_x", "max_x", "min_z", "max_z")]
        if not all(_number(v) for v in vals):
            report(f"zone.{zid}.rect", "four finite numbers required")
            continue
        min_x, max_x, min_z, max_z = vals
        if min_x >= max_x or min_z >= max_z:
            report(f"zone.{zid}.rect", "minimum must precede maximum")
        if bound_x is not None and (min_x < -bound_x or max_x > bound_x or min_z < -bound_z or max_z > bound_z):
            report(f"zone.{zid}.rect", "extends beyond map bounds")
        if type(zone.get("cover_targets")) is not int or zone["cover_targets"] < 0:
            report(f"zone.{zid}.cover_targets", "nonnegative integer required")

    anchors = sets["anchors"]
    for aid, anchor in anchors.items():
        zid = anchor.get("zone")
        if zid not in zones:
            report(f"anchor.{aid}.zone", "unknown zone")
        pos = anchor.get("position")
        if not isinstance(pos, list) or len(pos) != 3 or not all(_number(v) for v in pos):
            report(f"anchor.{aid}.position", "finite [x,y,z] required")
        elif zid in zones:
            rect = zones[zid].get("rect")
            if isinstance(rect, dict) and all(_number(rect.get(k)) for k in ("min_x", "max_x", "min_z", "max_z")):
                if not (rect["min_x"] <= pos[0] <= rect["max_x"] and rect["min_z"] <= pos[2] <= rect["max_z"]):
                    report(f"anchor.{aid}.position", f"outside declared zone {zid}")
        if anchor.get("kind") not in ("player_spawn", "enemy_spawn", "gate", "interact", "defense", "extraction"):
            report(f"anchor.{aid}.kind", "unknown anchor kind")

    roles = sets["roles"]
    for rid, role in roles.items():
        if role.get("status") not in ("existing", "planned", "in_development"):
            report(f"role.{rid}.status", "invalid implementation status")
        if not _number(role.get("telegraph_seconds")) or role["telegraph_seconds"] < 0:
            report(f"role.{rid}.telegraph_seconds", "must be nonnegative")

    phases = sets["phases"]
    ordered: list[tuple[int, str]] = []
    for pid, phase in phases.items():
        order = phase.get("order")
        if type(order) is not int or order < 1:
            report(f"phase.{pid}.order", "positive integer required")
        else:
            ordered.append((order, pid))
        if phase.get("zone") not in zones:
            report(f"phase.{pid}.zone", "unknown zone")
        budget = phase.get("expected_seconds")
        if not isinstance(budget, dict) or not _number(budget.get("min"), True) or not _number(budget.get("max"), True) or budget["min"] > budget["max"]:
            report(f"phase.{pid}.expected_seconds", "positive min <= max required")
        for key, lookup in (("objective_ids", sets["objectives"]), ("encounter_ids", sets["encounters"])):
            refs = phase.get(key)
            if not isinstance(refs, list) or not refs or len(refs) != len(set(map(str, refs))):
                report(f"phase.{pid}.{key}", "nonempty unique list required")
                continue
            for ref in refs:
                if ref not in lookup:
                    report(f"phase.{pid}.{key}", f"unknown reference {ref}")
                elif lookup[ref].get("phase") != pid:
                    report(f"phase.{pid}.{key}", f"reference {ref} belongs to another phase")
    ordered.sort()
    if not ordered or [i for i, _ in ordered] != list(range(1, len(ordered) + 1)):
        report("phases", "order must be contiguous from 1 with no duplicates")

    objectives = sets["objectives"]
    for oid, objective in objectives.items():
        if objective.get("phase") not in phases:
            report(f"objective.{oid}.phase", "unknown phase")
        target = objective.get("target")
        kind = objective.get("kind")
        if kind == "reach_zone":
            if target not in zones:
                report(f"objective.{oid}.target", "unknown zone")
        elif kind in ("interact", "hold_and_clear"):
            if target not in anchors:
                report(f"objective.{oid}.target", "unknown anchor")
        else:
            report(f"objective.{oid}.kind", "unsupported objective type")
        if not _number(objective.get("duration_seconds")) or objective["duration_seconds"] < 0:
            report(f"objective.{oid}.duration_seconds", "nonnegative number required")
        if type(objective.get("required")) is not bool:
            report(f"objective.{oid}.required", "boolean required")

    encounters = sets["encounters"]
    for eid, encounter in encounters.items():
        if encounter.get("phase") not in phases:
            report(f"encounter.{eid}.phase", "unknown phase")
        n = encounter.get("max_concurrent")
        if type(n) is not int or n <= 0:
            report(f"encounter.{eid}.max_concurrent", "positive integer required")
        elif global_cap is not None and n > global_cap:
            report(f"encounter.{eid}.max_concurrent", "exceeds global hostile cap")
        if not _number(encounter.get("telegraph_seconds")) or encounter["telegraph_seconds"] < 0:
            report(f"encounter.{eid}.telegraph_seconds", "nonnegative number required")
        spawns = encounter.get("spawn_anchor_ids")
        if not isinstance(spawns, list) or not spawns:
            report(f"encounter.{eid}.spawn_anchor_ids", "nonempty list required")
        else:
            for spawn in spawns:
                if spawn not in anchors or anchors[spawn].get("kind") != "enemy_spawn":
                    report(f"encounter.{eid}.spawn_anchor_ids", f"{spawn} not an enemy spawn anchor")
        units = encounter.get("units")
        count = 0
        if not isinstance(units, list) or not units:
            report(f"encounter.{eid}.units", "nonempty list required")
        else:
            for unit in units:
                if not isinstance(unit, dict) or unit.get("role") not in roles:
                    report(f"encounter.{eid}.units", "unknown enemy role")
                if not isinstance(unit, dict) or type(unit.get("count")) is not int or unit["count"] < 1:
                    report(f"encounter.{eid}.units", "count must be positive integer")
                else:
                    count += unit["count"]
        if type(n) is int and count > n:
            report(f"encounter.{eid}", "units exceed max_concurrent; waves must be split explicitly")
        if wave_cap is not None and count > wave_cap:
            report(f"encounter.{eid}", "units exceed spawns_per_wave")
        trigger = encounter.get("trigger")
        if not isinstance(trigger, dict) or not _identifier(trigger.get("event")) or not _identifier(trigger.get("target")):
            report(f"encounter.{eid}.trigger", "event and target strings required")
        elif trigger["event"] == "objective_started" or trigger["event"] == "objective_available":
            if trigger["target"] not in objectives:
                report(f"encounter.{eid}.trigger", "unknown objective target")
        elif trigger["event"] == "phase_enter":
            if trigger["target"] not in phases:
                report(f"encounter.{eid}.trigger", "unknown phase target")
        elif trigger["event"] == "zone_enter":
            if trigger["target"] not in zones:
                report(f"encounter.{eid}.trigger", "unknown zone target")

    terminals = data.get("terminal_states")
    if not isinstance(terminals, list) or not {"victory", "failed"}.issubset(set(map(str, terminals))):
        report("terminal_states", "victory and failed required")
    failures = data.get("failure_conditions")
    if not isinstance(failures, list) or not failures or not all(_identifier(e) for e in failures):
        report("failure_conditions", "nonempty failure list required")

    transitions = data.get("transitions", [])
    adjacency: dict[str, set[str]] = {id_: set() for id_ in phases}
    for i, transition in enumerate(transitions if isinstance(transitions, list) else []):
        where = f"transitions[{i}]"
        if not isinstance(transition, dict):
            report(where, "object required")
            continue
        source, target = transition.get("from"), transition.get("to")
        if source not in phases:
            report(where, "unknown source phase")
            continue
        if target not in phases and target != "victory":
            report(where, "target must be a declared phase or victory")
            continue
        adjacency[source].add(target)
        condition = transition.get("condition")
        refs = condition.get("objective_ids") if isinstance(condition, dict) else None
        if not isinstance(condition, dict) or not _identifier(condition.get("event")) or not isinstance(refs, list) or not refs:
            report(where, "condition.event and condition.objective_ids required")
        else:
            for oid in refs:
                if oid not in objectives or objectives[oid].get("phase") != source:
                    report(where, f"objective {oid} not part of source phase {source}")
            required_here = {oid for oid, obj in objectives.items() if obj.get("phase") == source and obj.get("required")}
            if not required_here.issubset(set(refs)):
                report(where, f"transition skips required objectives {sorted(required_here - set(refs))}")

    if ordered:
        first_phase = ordered[0][1]
        reachable = set()
        frontier = [first_phase]
        while frontier:
            current = frontier.pop()
            if current in reachable:
                continue
            reachable.add(current)
            frontier.extend(adjacency.get(current, ()))
        for pid in phases:
            if pid not in reachable:
                report("transitions", f"unreachable phase {pid}")
        if "victory" not in reachable:
            report("transitions", "no route to victory")
        for pid in phases:
            if not adjacency.get(pid):
                report("transitions", f"phase {pid} has no outgoing transition")

    gates = sets["qa_gates"]
    if not gates:
        report("qa_gates", "at least one gate required")
    for gid, gate in gates.items():
        if gate.get("status") not in ("planned", "in_progress", "verified", "failed", "blocked"):
            report(f"qa_gate.{gid}", "unsupported status")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="game-owned mission contract JSON path")
    args = parser.parse_args()
    try:
        contract = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"VERTICAL_SLICE FAIL: {exc}")
        return 1
    errors = validate_contract(contract)
    if errors:
        for issue in errors:
            print("VERTICAL_SLICE FAIL", issue)
        return 1
    print("VERTICAL_SLICE PASS id=%s phases=%d encounters=%d qa_gates=%d status=%s" %
        (contract["id"], len(contract["phases"]), len(contract["encounters"]), len(contract["qa_gates"]), contract["implementation_status"]))
    print("NOTE: semantic validation only; runtime, art, user experience and Android require separate tests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
