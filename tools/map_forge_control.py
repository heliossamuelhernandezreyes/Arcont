#!/usr/bin/env python3
"""Portable Map Forge editor control protocol. No model, generator or runtime dependency.

An author supplies every map decision. The project adapter owns game validation
and Godot execution. This tool owns inspection, revisions and reversible edits.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__:
    from .map_forge_terrain import brush
    from .project_lock import document_lock
    from .process_supervisor import run as run_supervised
else:
    from map_forge_terrain import brush
    from project_lock import document_lock
    from process_supervisor import run as run_supervised

OPERATIONS = ("capabilities", "list", "inspect", "create", "replace", "patch", "brush", "edit", "restore", "validate", "analyze", "materialize", "capture")
MAP_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


class ControlError(ValueError):
    pass


def decode(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ControlError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ControlError(f"non-finite JSON number: {x}")))


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def revision(state):
    return hashlib.sha256(encoded(state).encode()).hexdigest()


def atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".map-forge-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def tokens(pointer):
    if pointer == "":
        return []
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ControlError("path must be a JSON pointer")
    return [s.replace("~1", "/").replace("~0", "~") for s in pointer[1:].split("/")]


def slot(container, token, adding=False):
    if isinstance(container, dict):
        return token
    if not isinstance(container, list):
        raise ControlError("path traverses a scalar")
    if token.startswith("@"):
        matches = [i for i, item in enumerate(container) if isinstance(item, dict) and item.get("id") == token[1:]]
        if len(matches) != 1:
            raise ControlError(f"stable ID selector must match exactly one item: {token}")
        return matches[0]
    if token == "-" and adding:
        return len(container)
    if not token.isdigit() or (len(token) > 1 and token[0] == "0"):
        raise ControlError(f"invalid array index: {token}")
    index = int(token)
    if index >= len(container) + int(adding):
        raise ControlError(f"array index out of range: {token}")
    return index


def get(document, pointer):
    current = document
    for token in tokens(pointer):
        key = slot(current, token)
        try:
            current = current[key]
        except (KeyError, IndexError) as exc:
            raise ControlError(f"path does not exist: {pointer}") from exc
    return current


def edit(document, pointer, operation, value=None):
    parts = tokens(pointer)
    if not parts:
        if operation == "remove":
            raise ControlError("cannot remove the state root")
        return copy.deepcopy(value)
    parent = document
    for token in parts[:-1]:
        try:
            parent = parent[slot(parent, token)]
        except (KeyError, IndexError) as exc:
            raise ControlError(f"parent path does not exist: {pointer}") from exc
    key = slot(parent, parts[-1], operation == "add")
    if isinstance(parent, dict):
        if operation != "add" and key not in parent:
            raise ControlError(f"path does not exist: {pointer}")
        if operation == "remove":
            del parent[key]
        else:
            parent[key] = copy.deepcopy(value)
    elif isinstance(parent, list):
        if operation == "add":
            parent.insert(key, copy.deepcopy(value))
        elif operation == "remove":
            parent.pop(key)
        else:
            parent[key] = copy.deepcopy(value)
    else:
        raise ControlError("path parent must be an object or array")
    return document


def apply_patch(state, operations):
    if not isinstance(operations, list):
        raise ControlError("patch must be an array")
    result = copy.deepcopy(state)
    for index, item in enumerate(operations):
        if not isinstance(item, dict):
            raise ControlError(f"patch[{index}] must be an object")
        op, path = item.get("op"), item.get("path")
        if op in ("add", "replace", "test") and "value" not in item:
            raise ControlError(f"patch[{index}] requires value")
        if op == "test":
            if encoded(get(result, path)) != encoded(item["value"]):
                raise ControlError(f"test failed at {path}")
        elif op in ("add", "replace", "remove"):
            result = edit(result, path, op, item.get("value"))
        elif op in ("copy", "move"):
            source = item.get("from")
            if op == "move" and tokens(path)[:len(tokens(source))] == tokens(source) and source != path:
                raise ControlError("cannot move a parent into its child")
            value = copy.deepcopy(get(result, source))
            if op == "move":
                result = edit(result, source, "remove")
            result = edit(result, path, "add", value)
        else:
            raise ControlError(f"unsupported patch operation: {op}")
    encoded(result)  # Reject NaN/Infinity from programmatic callers, too.
    return result


def changes(before, after, path=""):
    if type(before) is not type(after):
        return [path or "/"]
    if isinstance(before, dict):
        result = []
        for key in sorted(before.keys() | after.keys()):
            child = path + "/" + key.replace("~", "~0").replace("/", "~1")
            result.extend([child] if key not in before or key not in after else changes(before[key], after[key], child))
        return result
    if isinstance(before, list):
        if len(before) != len(after):
            return [path]
        return [p for i, (a, b) in enumerate(zip(before, after)) for p in changes(a, b, path + "/" + str(i))]
    return [] if before == after else [path]


class Editor:
    def __init__(self, project):
        self.root = Path(project).resolve()
        self.config = decode((self.root / "map-forge.authoring.json").read_text(encoding="utf-8"))
        if self.config.get("protocol_version") != 1:
            raise ControlError("unsupported project protocol_version")
        self.map_dir = self.contained(self.config.get("map_directory", "maps"))
        self.physical_dir = self.contained(self.config.get("physical_directory", "maps/physical"))
        self.history_dir = self.contained(".mapforge/history")
        self.head_dir = self.contained(".mapforge/heads")

    def contained(self, relative):
        path = (self.root / relative).resolve()
        if path != self.root and self.root not in path.parents:
            raise ControlError("project path escapes project root")
        return path

    def paths(self, map_id):
        if not isinstance(map_id, str) or not MAP_ID.fullmatch(map_id):
            raise ControlError("map_id must contain only letters, numbers, underscore or hyphen")
        return self.contained(str(self.map_dir.relative_to(self.root) / (map_id + ".json"))), self.contained(str(self.physical_dir.relative_to(self.root) / (map_id + ".json")))

    def read(self, map_id):
        map_path, physical_path = self.paths(map_id)
        head = self.head_dir / (map_id + ".json")
        if head.exists():
            pointer = decode(head.read_text(encoding="utf-8"))
            digest = pointer.get("revision")
            if pointer.get("version") != 2 or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ControlError("invalid Map Forge generation pointer")
            generation = self.contained(str(self.history_dir.relative_to(self.root) / map_id / (digest + ".json")))
            state = decode(generation.read_text(encoding="utf-8"))
            if revision(state) != digest:
                raise ControlError("Map Forge generation hash mismatch")
            return state
        if not map_path.is_file():
            raise ControlError(f"map does not exist: {map_id}")
        return {"map": decode(map_path.read_text(encoding="utf-8")), "physical": decode(physical_path.read_text(encoding="utf-8")) if physical_path.exists() else None}

    def adapter(self, operation, state, request):
        command = self.config.get("adapter_command")
        if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
            raise ControlError("project requires adapter_command argv")
        run = run_supervised(command, cwd=self.root, input=encoded({"operation": operation, "state": state, "options": request.get("options", {})}), timeout=int(self.config.get("adapter_timeout_seconds", 180)))
        try:
            result = decode(run.stdout)
        except (ValueError, TypeError) as exc:
            raise ControlError("adapter returned invalid JSON: " + run.stderr[-2000:]) from exc
        if not isinstance(result, dict):
            raise ControlError("adapter result must be an object")
        if run.returncode != 0:
            result["ok"] = False
        return result

    def validate(self, state, map_id):
        if not isinstance(state, dict) or set(state) != {"map", "physical"}:
            raise ControlError("state must contain exactly map and physical")
        if not isinstance(state["map"], dict) or state["map"].get("id") != map_id:
            raise ControlError("state.map.id must equal map_id; use create to author a different map")
        if state["physical"] is not None and (not isinstance(state["physical"], dict) or state["physical"].get("map_id") != map_id):
            raise ControlError("physical.map_id must equal map_id")
        encoded(state)
        return self.adapter("validate", state, {})

    def commit(self, map_id, before, after, expected):
        self.paths(map_id)
        with document_lock(self.root, "map-forge/" + map_id):
            current = self.read(map_id) if self.exists(map_id) else None
            if (revision(current) if current else None) != expected:
                raise ControlError("revision conflict; inspect the latest map before editing")
            if before is not None:
                self.publish_generation(map_id, before)
            digest = self.publish_generation(map_id, after)
            # One namespace publication owns BOTH logical and physical state.
            atomic_write(self.head_dir / (map_id + ".json"), {"version": 2, "revision": digest})

    def publish_generation(self, map_id, state):
        digest = revision(state)
        path = self.contained(str(self.history_dir.relative_to(self.root) / map_id / (digest + ".json")))
        if path.exists():
            if revision(decode(path.read_text(encoding="utf-8"))) != digest:
                raise ControlError("immutable Map Forge generation changed")
        else:
            atomic_write(path, state)
        return digest

    def exists(self, map_id):
        map_path, _ = self.paths(map_id)
        return (self.head_dir / (map_id + ".json")).exists() or map_path.exists()

    def execute(self, request):
        if not isinstance(request, dict) or request.get("protocol_version") != 1:
            raise ControlError("request requires protocol_version=1")
        op = request.get("operation")
        if op not in OPERATIONS:
            raise ControlError(f"unsupported operation: {op}")
        if op == "capabilities":
            return {"ok": True, "operations": list(OPERATIONS), "all_contract_fields_editable": True, "author_decides_geometry": True, "generative_model_required": False, "stable_id_pointer_example": "/map/routes/@main_lane/width", "revision_required_for_existing_writes": True, "configuration": self.config}
        if op == "list":
            ids = {p.stem for directory in (self.map_dir, self.head_dir) for p in directory.glob("*.json")}
            return {"ok": True, "maps": [{"map_id": name, "revision": revision(self.read(name))} for name in sorted(ids)]}
        map_id = request.get("map_id")
        map_path, _ = self.paths(map_id)
        before = self.read(map_id) if self.exists(map_id) else None
        if op == "inspect":
            if before is None:
                raise ControlError("map does not exist")
            return {"ok": True, "map_id": map_id, "revision": revision(before), "state": before,
                    "storage": "atomic-generation-v2" if (self.head_dir / (map_id + ".json")).exists() else "legacy-unverified"}
        if op in ("validate", "analyze", "materialize", "capture"):
            state = request.get("state", before)
            validation = self.validate(state, map_id)
            if op == "validate" or not validation.get("ok"):
                return {**validation, "map_id": map_id, "revision": revision(state)}
            return {**self.adapter(op, state, request), "map_id": map_id, "revision": revision(state)}
        if op == "create":
            if before is not None:
                raise ControlError("map already exists; inspect and patch it")
            after = request.get("state")
            expected = None
        else:
            if before is None:
                raise ControlError("map does not exist")
            expected = request.get("if_revision")
            if expected != revision(before):
                raise ControlError("revision conflict; inspect the latest map before editing")
            if op == "patch":
                after = apply_patch(before, request.get("patch"))
            elif op == "brush":
                after = brush(before, request.get("options", {}))
            elif op == "edit":
                prepared = self.adapter("edit", before, request)
                if not prepared.get("ok"):
                    return {**prepared, "committed": False}
                after = prepared.get("state")
            elif op == "restore":
                old = request.get("restore_revision", "")
                if not re.fullmatch(r"[0-9a-f]{64}", old):
                    raise ControlError("restore_revision must be SHA-256")
                after = decode((self.history_dir / map_id / (old + ".json")).read_text(encoding="utf-8"))
            else:
                after = request.get("state")
        validation = self.validate(after, map_id)
        if not validation.get("ok"):
            return {**validation, "committed": False, "map_id": map_id}
        dry_run = request.get("dry_run", True)
        if not isinstance(dry_run, bool):
            raise ControlError("dry_run must be a boolean")
        if not dry_run:
            self.commit(map_id, before, after, expected)
        return {"ok": True, "map_id": map_id, "committed": not dry_run, "revision": revision(after), "previous_revision": expected, "changed_paths": changes(before, after), "validation": validation, "state": after,
                "storage": "atomic-generation-v2", "legacy_views_updated": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--request", default="-", help="request JSON path, or - for stdin")
    parser.add_argument("--output", help="optional response JSON file")
    args = parser.parse_args()
    try:
        request = decode(sys.stdin.read() if args.request == "-" else Path(args.request).read_text(encoding="utf-8"))
        result = {"protocol_version": 1, **Editor(args.project).execute(request)}
    except (ControlError, ValueError, OSError, subprocess.SubprocessError) as exc:
        result = {"protocol_version": 1, "ok": False, "error": str(exc)}
    if args.output:
        atomic_write(Path(args.output), result)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
