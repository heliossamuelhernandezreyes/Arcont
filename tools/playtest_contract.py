"""Bounded input/observation sessions for game-owned Godot playtest adapters."""
from __future__ import annotations

import math
import re

ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
MAX_FRAMES = 3600


def validate(session):
    errors = []
    if not isinstance(session, dict) or session.get("version") != 1 or isinstance(session.get("version"), bool):
        return ["session requires version 1"]
    if set(session) - {"version", "id", "actor", "seed", "stop_on_failure", "commands"}:
        errors.append("session contains unsupported fields")

    def name(value, path):
        if not isinstance(value, str) or not ID.fullmatch(value): errors.append(path + ": invalid identifier")

    def node(value, path):
        if (not isinstance(value, str) or not value or value.startswith("/")
                or any(part in ("", ".", "..") for part in value.split("/")) or ":" in value or "\\" in value):
            errors.append(path + ": requires a relative child NodePath")

    def number(value, path, minimum, maximum):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not minimum <= value <= maximum or not math.isfinite(value):
            errors.append(path + ": number outside supported range")

    name(session.get("id"), "id")
    node(session.get("actor"), "actor")
    seed = session.get("seed", 0)
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**31:
        errors.append("seed: requires a 31-bit nonnegative integer")
    if not isinstance(session.get("stop_on_failure", True), bool): errors.append("stop_on_failure: requires boolean")
    commands = session.get("commands")
    if not isinstance(commands, list) or not commands or len(commands) > 64:
        return errors + ["commands: requires 1 to 64 commands"]
    frames = 0
    identifiers = set()
    for index, command in enumerate(commands):
        path = f"commands/{index}"
        if not isinstance(command, dict):
            errors.append(path + ": requires an object")
            continue
        if set(command) - {"id", "frames", "actions", "capture", "expect"}:
            errors.append(path + ": unsupported command fields")
        identifier = command.get("id")
        name(identifier, path + "/id")
        if isinstance(identifier, str):
            if identifier in identifiers: errors.append(path + ": duplicate command id")
            identifiers.add(identifier)
        count = command.get("frames")
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_FRAMES:
            errors.append(path + "/frames: requires a bounded positive integer")
        else: frames += count
        actions = command.get("actions", {})
        if not isinstance(actions, dict) or len(actions) > 16:
            errors.append(path + "/actions: requires up to 16 named strengths")
        else:
            for action, strength in actions.items():
                name(action, path + "/actions")
                number(strength, path + "/actions/" + action, 0, 1)
        if "capture" in command: node(command["capture"], path + "/capture")
        expect = command.get("expect", {})
        if not isinstance(expect, dict) or set(expect) - {"position", "tolerance_m", "interactions_min", "height_min"}:
            errors.append(path + "/expect: unknown or malformed expectation")
            continue
        if "position" in expect:
            position = expect["position"]
            if not isinstance(position, list) or len(position) != 3:
                errors.append(path + "/expect/position: requires [x,y,z]")
            else:
                for value in position: number(value, path + "/expect/position", -1e6, 1e6)
            number(expect.get("tolerance_m", 0.6), path + "/expect/tolerance_m", 0.001, 100)
        if "height_min" in expect: number(expect["height_min"], path + "/expect/height_min", -1e6, 1e6)
        if "interactions_min" in expect:
            count = expect["interactions_min"]
            if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= MAX_FRAMES:
                errors.append(path + "/expect/interactions_min: requires a nonnegative integer")
    if frames > MAX_FRAMES: errors.append("session exceeds 3600 physics frames")
    return errors
