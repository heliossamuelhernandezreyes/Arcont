#!/usr/bin/env python3
"""Structured, revision-checked Godot project editing for fresh external projects.

This capability fills the gap between ARCONT's generic recipe authoring and a
newly bootstrapped project that has no custom adapter yet. It uses Godot itself
for scene/resource/input mutations and a bounded source editor for GDScript.

V1 deliberately exposes structured operations rather than arbitrary shell or
raw file writes. GDScript is restricted to a gameplay-oriented subset that
rejects editor tooling, host process execution, direct filesystem access and
network APIs. This denylist is defense-in-depth, not a complete language
sandbox.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path, PurePosixPath
from typing import Any

PROTOCOL_VERSION = 1
OPERATIONS = (
    "capabilities",
    "validate",
    "script.inspect",
    "script.create",
    "script.replace",
    "script.function.replace",
    "scene.inspect",
    "scene.edit",
    "resource.inspect",
    "resource.edit",
    "input.action.set",
)
MAX_SCRIPT_BYTES = 256 * 1024
MAX_ENGINE_REQUEST_BYTES = 1024 * 1024
MAX_CHANGES = 128
MAX_INSPECT_PROPERTIES = 64
SCRIPT_PATH = re.compile(r"^scripts/[A-Za-z0-9_./-]+\.gd$")
SCENE_PATH = re.compile(r"^scenes/[A-Za-z0-9_./-]+\.tscn$")
RESOURCE_PATH = re.compile(r"^(?:materials|resources|assets/generated)/[A-Za-z0-9_./-]+\.tres$")
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,127}$")
FUNCTION_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
PROPERTY_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
DENIED_SCRIPT_PATTERNS = {
    "@tool": "editor-time execution is not allowed in structured GDScript v1",
    "EditorPlugin": "editor plugins are outside the gameplay-safe subset",
    "EditorInterface": "editor APIs are outside the gameplay-safe subset",
    "OS.": "host OS APIs are outside the gameplay-safe subset",
    "FileAccess": "direct filesystem access is outside the gameplay-safe subset",
    "DirAccess": "direct filesystem access is outside the gameplay-safe subset",
    "HTTPRequest": "network APIs are outside the gameplay-safe subset",
    "HTTPClient": "network APIs are outside the gameplay-safe subset",
    "TCPServer": "network APIs are outside the gameplay-safe subset",
    "StreamPeerTCP": "network APIs are outside the gameplay-safe subset",
    "PacketPeerUDP": "network APIs are outside the gameplay-safe subset",
    "UDPServer": "network APIs are outside the gameplay-safe subset",
    "WebSocketPeer": "network APIs are outside the gameplay-safe subset",
    "JavaScriptBridge": "host/browser bridge APIs are outside the gameplay-safe subset",
    "ProjectSettings.save": "project settings writes must use structured operations",
    "ResourceSaver.save": "resource writes must use structured operations",
}
DENIED_NODE_TYPES = {"HTTPRequest", "EditorPlugin"}
RUNNER_TIMEOUT_SECONDS = 120

RUNNER_SOURCE = r'''extends SceneTree

var request_data: Dictionary = {}
var response: Dictionary = {"ok": false}

func _initialize() -> void:
    var args := OS.get_cmdline_user_args()
    if args.size() != 2:
        _finish({"ok": false, "error": "runner requires request and response res:// paths"})
        return
    var request_path: String = args[0]
    var response_path: String = args[1]
    var text := FileAccess.get_file_as_string(request_path)
    var parsed = JSON.parse_string(text)
    if typeof(parsed) != TYPE_DICTIONARY:
        _write_response(response_path, {"ok": false, "error": "request JSON must be an object"})
        quit(2)
        return
    request_data = parsed
    var op: String = str(request_data.get("operation", ""))
    var result: Dictionary
    match op:
        "scene.inspect":
            result = _scene_inspect()
        "scene.edit":
            result = _scene_edit()
        "resource.inspect":
            result = _resource_inspect()
        "resource.edit":
            result = _resource_edit()
        "input.action.set":
            result = _input_action_set()
        "validate.resource":
            result = _validate_resource()
        _:
            result = {"ok": false, "error": "unsupported runner operation"}
    _write_response(response_path, result)
    quit(0 if result.get("ok", false) else 1)

func _write_response(path: String, value: Dictionary) -> void:
    var file := FileAccess.open(path, FileAccess.WRITE)
    if file == null:
        push_error("cannot open runner response file")
        return
    file.store_string(JSON.stringify(value))
    file.close()

func _finish(value: Dictionary) -> void:
    push_error(str(value.get("error", "runner failed")))
    quit(2)

func _valid_res_path(path: String, suffix: String) -> bool:
    return path.begins_with("res://") and path.ends_with(suffix) and not path.contains("..") and not path.contains("\\")

func _variant(value):
    if typeof(value) == TYPE_DICTIONARY and value.has("$type"):
        var kind := str(value["$type"])
        var raw = value.get("value")
        match kind:
            "Vector2":
                if typeof(raw) != TYPE_ARRAY or raw.size() != 2: return null
                return Vector2(float(raw[0]), float(raw[1]))
            "Vector2i":
                if typeof(raw) != TYPE_ARRAY or raw.size() != 2: return null
                return Vector2i(int(raw[0]), int(raw[1]))
            "Vector3":
                if typeof(raw) != TYPE_ARRAY or raw.size() != 3: return null
                return Vector3(float(raw[0]), float(raw[1]), float(raw[2]))
            "Vector3i":
                if typeof(raw) != TYPE_ARRAY or raw.size() != 3: return null
                return Vector3i(int(raw[0]), int(raw[1]), int(raw[2]))
            "Color":
                if typeof(raw) != TYPE_ARRAY or raw.size() < 3 or raw.size() > 4: return null
                return Color(float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3]) if raw.size() == 4 else 1.0)
            "NodePath":
                if typeof(raw) != TYPE_STRING: return null
                return NodePath(raw)
            "Resource":
                var path := str(value.get("path", ""))
                if not _valid_res_path(path, ""): return null
                return load(path)
            _:
                return null
    if typeof(value) == TYPE_ARRAY:
        var out := []
        for item in value:
            out.append(_variant(item))
        return out
    if typeof(value) == TYPE_DICTIONARY:
        var out := {}
        for key in value:
            out[key] = _variant(value[key])
        return out
    return value

func _json_variant(value):
    match typeof(value):
        TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_FLOAT, TYPE_STRING:
            return value
        TYPE_VECTOR2:
            return {"$type":"Vector2","value":[value.x,value.y]}
        TYPE_VECTOR2I:
            return {"$type":"Vector2i","value":[value.x,value.y]}
        TYPE_VECTOR3:
            return {"$type":"Vector3","value":[value.x,value.y,value.z]}
        TYPE_VECTOR3I:
            return {"$type":"Vector3i","value":[value.x,value.y,value.z]}
        TYPE_COLOR:
            return {"$type":"Color","value":[value.r,value.g,value.b,value.a]}
        TYPE_NODE_PATH:
            return {"$type":"NodePath","value":str(value)}
        TYPE_OBJECT:
            if value is Resource and not value.resource_path.is_empty():
                return {"$type":"Resource","path":value.resource_path,"class":value.get_class()}
            return {"$type":"Object","class":value.get_class() if value != null else "null"}
        TYPE_ARRAY:
            var out := []
            for item in value:
                out.append(_json_variant(item))
            return out
        TYPE_DICTIONARY:
            var out := {}
            for key in value:
                out[str(key)] = _json_variant(value[key])
            return out
        _:
            return str(value)

func _node(root: Node, path: String) -> Node:
    if path == "." or path.is_empty():
        return root
    return root.get_node_or_null(NodePath(path))

func _tree_rows(root: Node) -> Array:
    var rows := []
    var stack := [root]
    while not stack.is_empty():
        var current: Node = stack.pop_front()
        var script_path := ""
        var script = current.get_script()
        if script is Script and not script.resource_path.is_empty():
            script_path = script.resource_path
        rows.append({
            "path": "." if current == root else str(root.get_path_to(current)),
            "name": current.name,
            "type": current.get_class(),
            "script": script_path
        })
        for child in current.get_children():
            if child is Node:
                stack.append(child)
    return rows

func _scene_inspect() -> Dictionary:
    var path := str(request_data.get("scene", ""))
    if not _valid_res_path(path, ".tscn"):
        return {"ok": false, "error": "invalid scene path"}
    var packed = load(path)
    if not (packed is PackedScene):
        return {"ok": false, "error": "scene could not be loaded"}
    var root = packed.instantiate()
    if root == null:
        return {"ok": false, "error": "scene could not be instantiated"}
    var result := {"ok": true, "root_type": root.get_class(), "root_name": root.name, "nodes": _tree_rows(root)}
    root.free()
    return result

func _scene_edit() -> Dictionary:
    var path := str(request_data.get("scene", ""))
    if not _valid_res_path(path, ".tscn"):
        return {"ok": false, "error": "invalid scene path"}
    var root: Node
    if ResourceLoader.exists(path):
        var packed = load(path)
        if not (packed is PackedScene):
            return {"ok": false, "error": "existing scene is not PackedScene"}
        root = packed.instantiate()
    else:
        var root_type := str(request_data.get("root_type", ""))
        var root_name := str(request_data.get("root_name", "Main"))
        var created = ClassDB.instantiate(root_type)
        if not (created is Node):
            return {"ok": false, "error": "root_type must instantiate a Node"}
        root = created
        root.name = root_name
    if root == null:
        return {"ok": false, "error": "scene root unavailable"}
    var changes = request_data.get("changes", [])
    if typeof(changes) != TYPE_ARRAY:
        root.free()
        return {"ok": false, "error": "changes must be an array"}
    for change in changes:
        if typeof(change) != TYPE_DICTIONARY:
            root.free()
            return {"ok": false, "error": "scene change must be an object"}
        var op := str(change.get("op", ""))
        if op == "add":
            var parent := _node(root, str(change.get("parent", ".")))
            if parent == null:
                root.free()
                return {"ok": false, "error": "scene add parent not found"}
            var kind := str(change.get("type", ""))
            var child = ClassDB.instantiate(kind)
            if not (child is Node):
                root.free()
                return {"ok": false, "error": "scene add type must instantiate a Node"}
            child.name = str(change.get("name", ""))
            parent.add_child(child)
            child.owner = root
        elif op == "remove":
            var target := _node(root, str(change.get("path", "")))
            if target == null or target == root:
                root.free()
                return {"ok": false, "error": "scene remove target invalid"}
            var parent := target.get_parent()
            parent.remove_child(target)
            target.free()
        elif op == "set":
            var target := _node(root, str(change.get("path", ".")))
            if target == null:
                root.free()
                return {"ok": false, "error": "scene set target not found"}
            var prop := str(change.get("property", ""))
            var found := false
            for descriptor in target.get_property_list():
                if str(descriptor.get("name", "")) == prop:
                    found = true
                    break
            if not found:
                root.free()
                return {"ok": false, "error": "scene property not found: " + prop}
            target.set(prop, _variant(change.get("value")))
        elif op == "attach_script":
            var target := _node(root, str(change.get("path", ".")))
            var script_path := str(change.get("script", ""))
            if target == null or not _valid_res_path(script_path, ".gd"):
                root.free()
                return {"ok": false, "error": "invalid script attachment"}
            var script = load(script_path)
            if not (script is Script):
                root.free()
                return {"ok": false, "error": "script attachment could not be loaded"}
            target.set_script(script)
        elif op == "rename":
            var target := _node(root, str(change.get("path", ".")))
            if target == null:
                root.free()
                return {"ok": false, "error": "rename target not found"}
            target.name = str(change.get("name", ""))
        else:
            root.free()
            return {"ok": false, "error": "unsupported scene change: " + op}
    var packed := PackedScene.new()
    var pack_error := packed.pack(root)
    if pack_error != OK:
        root.free()
        return {"ok": false, "error": "PackedScene.pack failed: " + str(pack_error)}
    var save_error := ResourceSaver.save(packed, path)
    var rows := _tree_rows(root)
    root.free()
    if save_error != OK:
        return {"ok": false, "error": "scene save failed: " + str(save_error)}
    return {"ok": true, "nodes": rows}

func _resource_inspect() -> Dictionary:
    var path := str(request_data.get("resource", ""))
    if not _valid_res_path(path, ".tres"):
        return {"ok": false, "error": "invalid resource path"}
    var resource = load(path)
    if not (resource is Resource):
        return {"ok": false, "error": "resource could not be loaded"}
    var requested = request_data.get("properties", [])
    if typeof(requested) != TYPE_ARRAY:
        return {"ok": false, "error": "properties must be an array"}
    var values := {}
    for prop in requested:
        values[str(prop)] = _json_variant(resource.get(str(prop)))
    return {"ok": true, "class": resource.get_class(), "properties": values}

func _resource_edit() -> Dictionary:
    var path := str(request_data.get("resource", ""))
    if not _valid_res_path(path, ".tres"):
        return {"ok": false, "error": "invalid resource path"}
    var resource: Resource
    if ResourceLoader.exists(path):
        var loaded = load(path)
        if not (loaded is Resource):
            return {"ok": false, "error": "existing resource could not be loaded"}
        resource = loaded
    else:
        var kind := str(request_data.get("resource_type", ""))
        var created = ClassDB.instantiate(kind)
        if not (created is Resource):
            return {"ok": false, "error": "resource_type must instantiate a Resource"}
        resource = created
    var changes = request_data.get("changes", [])
    if typeof(changes) != TYPE_ARRAY:
        return {"ok": false, "error": "resource changes must be an array"}
    for change in changes:
        if typeof(change) != TYPE_DICTIONARY or str(change.get("op", "")) != "set":
            return {"ok": false, "error": "resource v1 supports set changes only"}
        var prop := str(change.get("property", ""))
        var found := false
        for descriptor in resource.get_property_list():
            if str(descriptor.get("name", "")) == prop:
                found = true
                break
        if not found:
            return {"ok": false, "error": "resource property not found: " + prop}
        resource.set(prop, _variant(change.get("value")))
    var save_error := ResourceSaver.save(resource, path)
    if save_error != OK:
        return {"ok": false, "error": "resource save failed: " + str(save_error)}
    return {"ok": true, "class": resource.get_class()}

func _input_event(spec: Dictionary):
    var kind := str(spec.get("type", ""))
    if kind == "key":
        var event := InputEventKey.new()
        var key_name := str(spec.get("keycode", ""))
        var code = OS.find_keycode_from_string(key_name)
        if code == KEY_NONE:
            return null
        if bool(spec.get("physical", true)):
            event.physical_keycode = code
        else:
            event.keycode = code
        return event
    if kind == "mouse_button":
        var mouse := InputEventMouseButton.new()
        mouse.button_index = int(spec.get("button_index", 0))
        return mouse
    if kind == "joypad_button":
        var joy := InputEventJoypadButton.new()
        joy.button_index = int(spec.get("button_index", -1))
        return joy
    return null

func _input_action_set() -> Dictionary:
    var action := str(request_data.get("action", ""))
    var deadzone := float(request_data.get("deadzone", 0.2))
    var specs = request_data.get("events", [])
    if action.is_empty() or typeof(specs) != TYPE_ARRAY:
        return {"ok": false, "error": "invalid input action request"}
    var events := []
    for spec in specs:
        if typeof(spec) != TYPE_DICTIONARY:
            return {"ok": false, "error": "input event must be an object"}
        var event = _input_event(spec)
        if event == null:
            return {"ok": false, "error": "unsupported input event"}
        events.append(event)
    ProjectSettings.set_setting("input/" + action, {"deadzone": deadzone, "events": events})
    var err := ProjectSettings.save()
    if err != OK:
        return {"ok": false, "error": "ProjectSettings.save failed: " + str(err)}
    return {"ok": true, "action": action, "event_count": events.size(), "deadzone": deadzone}

func _validate_resource() -> Dictionary:
    var path := str(request_data.get("path", ""))
    if not _valid_res_path(path, str(request_data.get("suffix", ""))):
        return {"ok": false, "error": "invalid validation path"}
    var loaded = load(path)
    return {"ok": loaded != null, "class": loaded.get_class() if loaded != null else ""}
'''

SCRIPT_VALIDATOR_SOURCE = r'''extends SceneTree

func _initialize() -> void:
    var args := OS.get_cmdline_user_args()
    if args.size() != 2:
        quit(2)
        return
    var script_path: String = args[0]
    var output_path: String = args[1]
    var loaded = load(script_path)
    var result := {"ok": loaded is Script, "class": loaded.get_class() if loaded != null else ""}
    var file := FileAccess.open(output_path, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(result))
        file.close()
    quit(0 if result["ok"] else 1)
'''


class StructuredError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise StructuredError("target must be a regular non-symlink file")
    return _sha_bytes(path.read_bytes())


def _safe_rel(value: Any, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise StructuredError(f"invalid {label} path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "\\" in value:
        raise StructuredError(f"unsafe {label} path")
    return pure.as_posix()


def _project_file(project: Path, relative: str) -> Path:
    root = project.resolve()
    lexical = root / Path(*PurePosixPath(relative).parts)
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise StructuredError("symlink paths are not accepted")
    resolved_parent = lexical.parent.resolve()
    if resolved_parent != root and root not in resolved_parent.parents:
        raise StructuredError("target path escapes project")
    return lexical


def _revision_guard(path: Path, expected: Any) -> str | None:
    current = _sha_file(path)
    if current is None:
        if expected is not None:
            raise StructuredError("target does not exist; if_revision must be null")
    else:
        if not isinstance(expected, str) or not SHA256.fullmatch(expected):
            raise StructuredError("existing target requires if_revision SHA-256")
        if expected != current:
            raise StructuredError("revision conflict; inspect target before editing")
    return current


def _godot_bin() -> str:
    configured = os.environ.get("GODOT_BIN")
    if configured:
        path = Path(configured)
        if path.is_file():
            return str(path)
    for name in ("godot4", "godot"):
        found = shutil.which(name)
        if found:
            return found
    raise StructuredError("Godot executable not found; set GODOT_BIN or install godot4/godot")


def _run_godot_script(project: Path, source: str, request: dict[str, Any], timeout: int = RUNNER_TIMEOUT_SECONDS) -> dict[str, Any]:
    payload = _canonical(request)
    if len(payload) > MAX_ENGINE_REQUEST_BYTES:
        raise StructuredError("structured engine request exceeds size limit")
    root = project.resolve()
    run = _project_file(root, f".arcont/runs/structured/{uuid.uuid4().hex}")
    run.mkdir(parents=True, exist_ok=False)
    runner = run / "runner.gd"
    request_path = run / "request.json"
    response_path = run / "response.json"
    runner.write_text(source, encoding="utf-8")
    request_path.write_bytes(payload)
    runner_res = "res://" + runner.relative_to(root).as_posix()
    request_res = "res://" + request_path.relative_to(root).as_posix()
    response_res = "res://" + response_path.relative_to(root).as_posix()
    command = [
        _godot_bin(),
        "--headless",
        "--path",
        str(root),
        "--script",
        runner_res,
        "--",
        request_res,
        response_res,
    ]
    try:
        proc = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise StructuredError(f"Godot structured operation timed out after {timeout}s") from exc
    (run / "stdout.log").write_text(proc.stdout, encoding="utf-8")
    (run / "stderr.log").write_text(proc.stderr, encoding="utf-8")
    if not response_path.is_file():
        raise StructuredError(f"Godot structured runner produced no response; evidence={run.relative_to(root)}")
    try:
        result = json.loads(response_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StructuredError("Godot structured runner returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise StructuredError("Godot structured runner response must be an object")
    return {
        "ok": proc.returncode == 0 and result.get("ok") is True,
        "exit_code": proc.returncode,
        "result": result,
        "evidence": str(run.relative_to(root)),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def _validate_script_source(source: Any) -> str:
    if not isinstance(source, str):
        raise StructuredError("script source must be a string")
    raw = source.encode("utf-8")
    if not raw or len(raw) > MAX_SCRIPT_BYTES:
        raise StructuredError("script source must be non-empty and <=256 KiB")
    for token, reason in DENIED_SCRIPT_PATTERNS.items():
        if token in source:
            raise StructuredError(f"GDScript token {token!r} refused: {reason}")
    if "\x00" in source:
        raise StructuredError("script source contains NUL")
    return source if source.endswith("\n") else source + "\n"


def _function_spans(source: str) -> dict[str, tuple[int, int]]:
    lines = source.splitlines(keepends=True)
    starts: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
        if match:
            starts.append((match.group(1), index))
    spans: dict[str, tuple[int, int]] = {}
    for pos, (name, start) in enumerate(starts):
        if name in spans:
            raise StructuredError(f"duplicate top-level function name: {name}")
        end = len(lines)
        for index in range(start + 1, len(lines)):
            line = lines[index]
            stripped = line.strip()
            if not stripped:
                continue
            if line[0].isspace():
                continue
            end = index
            break
        spans[name] = (start, end)
    return spans


def _script_inspect(project: Path, relative: str) -> dict[str, Any]:
    path = _project_file(project, relative)
    if not path.is_file() or path.is_symlink():
        raise StructuredError("script does not exist")
    source = path.read_text(encoding="utf-8")
    raw = source.encode("utf-8")
    if len(raw) > MAX_SCRIPT_BYTES:
        raise StructuredError("script exceeds structured editor size limit")
    spans = _function_spans(source)
    extends_match = re.search(r"(?m)^extends\s+(.+?)\s*$", source)
    class_match = re.search(r"(?m)^class_name\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", source)
    return {
        "ok": True,
        "write_performed": False,
        "result": {
            "path": relative,
            "revision": _sha_bytes(raw),
            "bytes": len(raw),
            "lines": len(source.splitlines()),
            "extends": extends_match.group(1).strip() if extends_match else None,
            "class_name": class_match.group(1) if class_match else None,
            "functions": [
                {"name": name, "start_line": start + 1, "end_line": end}
                for name, (start, end) in spans.items()
            ],
            "source": source,
        },
    }


def _validate_script_with_godot(project: Path, relative: str) -> dict[str, Any]:
    root = project.resolve()
    run = _project_file(root, f".arcont/runs/structured/{uuid.uuid4().hex}")
    run.mkdir(parents=True, exist_ok=False)
    runner = run / "validator.gd"
    response = run / "response.json"
    runner.write_text(SCRIPT_VALIDATOR_SOURCE, encoding="utf-8")
    command = [
        _godot_bin(),
        "--headless",
        "--path",
        str(root),
        "--script",
        "res://" + runner.relative_to(root).as_posix(),
        "--",
        "res://" + relative,
        "res://" + response.relative_to(root).as_posix(),
    ]
    try:
        proc = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=RUNNER_TIMEOUT_SECONDS, check=False)
    except subprocess.TimeoutExpired as exc:
        raise StructuredError("GDScript validation timed out") from exc
    (run / "stdout.log").write_text(proc.stdout, encoding="utf-8")
    (run / "stderr.log").write_text(proc.stderr, encoding="utf-8")
    payload: dict[str, Any] = {}
    if response.is_file():
        try:
            parsed = json.loads(response.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            pass
    parse_error = any(marker in (proc.stdout + "\n" + proc.stderr) for marker in ("SCRIPT ERROR", "Parse Error", "Failed to load script"))
    ok = proc.returncode == 0 and payload.get("ok") is True and not parse_error
    return {
        "ok": ok,
        "exit_code": proc.returncode,
        "result": payload,
        "evidence": str(run.relative_to(root)),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def _commit_script(project: Path, relative: str, source: str, expected: Any) -> dict[str, Any]:
    path = _project_file(project, relative)
    before_revision = _revision_guard(path, expected)
    before_bytes = path.read_bytes() if path.exists() else None
    source = _validate_script_source(source)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".arcont-{uuid.uuid4().hex}.tmp")
    temp.write_text(source, encoding="utf-8")
    os.replace(temp, path)
    validation = _validate_script_with_godot(project, relative)
    if not validation["ok"]:
        if before_bytes is None:
            path.unlink(missing_ok=True)
        else:
            rollback = path.with_name(path.name + f".arcont-rollback-{uuid.uuid4().hex}.tmp")
            rollback.write_bytes(before_bytes)
            os.replace(rollback, path)
        raise StructuredError("GDScript validation failed and edit was rolled back")
    after_revision = _sha_file(path)
    return {
        "ok": True,
        "write_performed": True,
        "result": {
            "path": relative,
            "previous_revision": before_revision,
            "revision": after_revision,
            "validation": validation,
        },
    }


def _script_function_replace(project: Path, relative: str, function: Any, replacement: Any, expected: Any) -> dict[str, Any]:
    if not isinstance(function, str) or not FUNCTION_NAME.fullmatch(function):
        raise StructuredError("invalid function name")
    path = _project_file(project, relative)
    current = _revision_guard(path, expected)
    if current is None:
        raise StructuredError("script.function.replace requires an existing script")
    source = path.read_text(encoding="utf-8")
    spans = _function_spans(source)
    if function not in spans:
        raise StructuredError("target function not found")
    replacement = _validate_script_source(replacement)
    replacement_spans = _function_spans(replacement)
    if set(replacement_spans) != {function}:
        raise StructuredError("replacement must contain exactly the target top-level function")
    lines = source.splitlines(keepends=True)
    start, end = spans[function]
    new_source = "".join(lines[:start]) + replacement + "".join(lines[end:])
    return _commit_script(project, relative, new_source, current)


def _validate_scene_change(change: Any) -> dict[str, Any]:
    if not isinstance(change, dict):
        raise StructuredError("scene change must be an object")
    op = change.get("op")
    if op not in {"add", "remove", "set", "attach_script", "rename"}:
        raise StructuredError(f"unsupported scene change: {op!r}")
    if op == "add":
        if not isinstance(change.get("name"), str) or not IDENTIFIER.fullmatch(change["name"]):
            raise StructuredError("scene add requires safe node name")
        kind = change.get("type")
        if not isinstance(kind, str) or not IDENTIFIER.fullmatch(kind):
            raise StructuredError("scene add requires safe node type")
        if kind in DENIED_NODE_TYPES:
            raise StructuredError(f"node type refused in structured v1: {kind}")
    if op in {"set"}:
        prop = change.get("property")
        if not isinstance(prop, str) or not PROPERTY_NAME.fullmatch(prop):
            raise StructuredError("scene set requires safe property name")
    if op == "attach_script":
        script = _safe_rel(change.get("script", "").removeprefix("res://") if isinstance(change.get("script"), str) else None, SCRIPT_PATH, "script")
        change = dict(change)
        change["script"] = "res://" + script
    if op == "rename":
        if not isinstance(change.get("name"), str) or not IDENTIFIER.fullmatch(change["name"]):
            raise StructuredError("scene rename requires safe node name")
    for field in ("parent", "path"):
        if field in change:
            value = change[field]
            if not isinstance(value, str) or ".." in PurePosixPath(value).parts or "\\" in value:
                raise StructuredError(f"scene {field} must be a safe relative node path")
    return change


def _engine_target_edit(
    project: Path,
    operation: str,
    relative: str,
    expected: Any,
    request: dict[str, Any],
) -> dict[str, Any]:
    path = _project_file(project, relative)
    before_revision = _revision_guard(path, expected)
    before_bytes = path.read_bytes() if path.exists() else None
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = _run_godot_script(project, RUNNER_SOURCE, request)
    if not engine["ok"]:
        if before_bytes is None:
            path.unlink(missing_ok=True)
        else:
            rollback = path.with_name(path.name + f".arcont-rollback-{uuid.uuid4().hex}.tmp")
            rollback.write_bytes(before_bytes)
            os.replace(rollback, path)
        raise StructuredError(f"{operation} failed and target was rolled back")
    after_revision = _sha_file(path)
    if after_revision is None:
        raise StructuredError(f"{operation} reported success but target file is missing")
    return {
        "ok": True,
        "write_performed": True,
        "result": {
            "path": relative,
            "previous_revision": before_revision,
            "revision": after_revision,
            "engine": engine,
        },
    }


def execute(project: Path, request: dict[str, Any]) -> dict[str, Any]:
    if request.get("protocol_version") != PROTOCOL_VERSION:
        raise StructuredError("request requires protocol_version=1")
    operation = request.get("operation")
    if operation not in OPERATIONS:
        raise StructuredError(f"unsupported operation: {operation}")
    root = Path(project).resolve()
    if not root.is_dir():
        raise StructuredError("external project root must exist")
    if not (root / "project.godot").is_file():
        raise StructuredError("structured Godot editing requires project.godot")

    if operation == "capabilities":
        return {
            "ok": True,
            "write_performed": False,
            "operations": list(OPERATIONS),
            "scene_changes": ["add", "remove", "set", "attach_script", "rename"],
            "resource_changes": ["set"],
            "script_patch_modes": ["replace-whole-script", "replace-top-level-function"],
            "input_events": ["key", "mouse_button", "joypad_button"],
            "revision_checked": True,
            "rollback_on_validation_failure": True,
            "arbitrary_shell": False,
            "raw_arbitrary_file_write": False,
            "script_privileged_api_denylist": sorted(DENIED_SCRIPT_PATTERNS),
            "limits": [
                "GDScript denylist is defense-in-depth, not a complete sandbox.",
                "Structured v1 does not expose network/editor/host filesystem APIs.",
                "Scene/resource writes require Godot to be available.",
            ],
        }

    if operation == "validate":
        return {
            "ok": True,
            "write_performed": False,
            "result": {
                "godot_bin": _godot_bin(),
                "project_revision": _sha_file(root / "project.godot"),
            },
        }

    if operation.startswith("script."):
        relative = _safe_rel(request.get("path"), SCRIPT_PATH, "script")
        if operation == "script.inspect":
            return _script_inspect(root, relative)
        if operation == "script.create":
            if _project_file(root, relative).exists():
                raise StructuredError("script already exists")
            return _commit_script(root, relative, request.get("source"), request.get("if_revision"))
        if operation == "script.replace":
            return _commit_script(root, relative, request.get("source"), request.get("if_revision"))
        if operation == "script.function.replace":
            return _script_function_replace(
                root,
                relative,
                request.get("function"),
                request.get("source"),
                request.get("if_revision"),
            )

    if operation.startswith("scene."):
        relative = _safe_rel(request.get("scene"), SCENE_PATH, "scene")
        path = _project_file(root, relative)
        if operation == "scene.inspect":
            if not path.is_file():
                raise StructuredError("scene does not exist")
            engine = _run_godot_script(
                root,
                RUNNER_SOURCE,
                {"operation": "scene.inspect", "scene": "res://" + relative},
            )
            if not engine["ok"]:
                raise StructuredError("scene inspection failed")
            return {
                "ok": True,
                "write_performed": False,
                "result": {
                    "scene": relative,
                    "revision": _sha_file(path),
                    "engine": engine,
                },
            }
        changes = request.get("changes", [])
        if not isinstance(changes, list) or not 1 <= len(changes) <= MAX_CHANGES:
            raise StructuredError(f"scene.edit changes must contain 1..{MAX_CHANGES} entries")
        validated = [_validate_scene_change(change) for change in changes]
        payload = {
            "operation": "scene.edit",
            "scene": "res://" + relative,
            "changes": validated,
        }
        if not path.exists():
            root_type = request.get("root_type")
            root_name = request.get("root_name", "Main")
            if not isinstance(root_type, str) or not IDENTIFIER.fullmatch(root_type) or root_type in DENIED_NODE_TYPES:
                raise StructuredError("new scene requires safe root_type")
            if not isinstance(root_name, str) or not IDENTIFIER.fullmatch(root_name):
                raise StructuredError("new scene requires safe root_name")
            payload["root_type"] = root_type
            payload["root_name"] = root_name
        return _engine_target_edit(root, "scene.edit", relative, request.get("if_revision"), payload)

    if operation.startswith("resource."):
        relative = _safe_rel(request.get("resource"), RESOURCE_PATH, "resource")
        path = _project_file(root, relative)
        if operation == "resource.inspect":
            if not path.is_file():
                raise StructuredError("resource does not exist")
            properties = request.get("properties", [])
            if not isinstance(properties, list) or len(properties) > MAX_INSPECT_PROPERTIES:
                raise StructuredError("resource.inspect properties must be a bounded array")
            if not all(isinstance(v, str) and PROPERTY_NAME.fullmatch(v) for v in properties):
                raise StructuredError("resource.inspect property names must be safe identifiers")
            engine = _run_godot_script(
                root,
                RUNNER_SOURCE,
                {"operation": "resource.inspect", "resource": "res://" + relative, "properties": properties},
            )
            if not engine["ok"]:
                raise StructuredError("resource inspection failed")
            return {
                "ok": True,
                "write_performed": False,
                "result": {
                    "resource": relative,
                    "revision": _sha_file(path),
                    "engine": engine,
                },
            }
        changes = request.get("changes", [])
        if not isinstance(changes, list) or not 1 <= len(changes) <= MAX_CHANGES:
            raise StructuredError(f"resource.edit changes must contain 1..{MAX_CHANGES} entries")
        for change in changes:
            if not isinstance(change, dict) or change.get("op") != "set":
                raise StructuredError("resource.edit v1 supports set changes only")
            prop = change.get("property")
            if not isinstance(prop, str) or not PROPERTY_NAME.fullmatch(prop):
                raise StructuredError("resource set requires safe property name")
        payload = {"operation": "resource.edit", "resource": "res://" + relative, "changes": changes}
        if not path.exists():
            resource_type = request.get("resource_type")
            if not isinstance(resource_type, str) or not IDENTIFIER.fullmatch(resource_type):
                raise StructuredError("new resource requires safe resource_type")
            payload["resource_type"] = resource_type
        return _engine_target_edit(root, "resource.edit", relative, request.get("if_revision"), payload)

    if operation == "input.action.set":
        project_godot = root / "project.godot"
        before_revision = _revision_guard(project_godot, request.get("if_revision"))
        before_bytes = project_godot.read_bytes()
        action = request.get("action")
        events = request.get("events", [])
        if not isinstance(action, str) or not IDENTIFIER.fullmatch(action):
            raise StructuredError("input action requires safe action identifier")
        if not isinstance(events, list) or not 1 <= len(events) <= 16:
            raise StructuredError("input action requires 1..16 events")
        for event in events:
            if not isinstance(event, dict) or event.get("type") not in {"key", "mouse_button", "joypad_button"}:
                raise StructuredError("unsupported structured input event")
        engine = _run_godot_script(
            root,
            RUNNER_SOURCE,
            {
                "operation": "input.action.set",
                "action": action,
                "deadzone": request.get("deadzone", 0.2),
                "events": events,
            },
        )
        if not engine["ok"]:
            rollback = project_godot.with_name(project_godot.name + f".arcont-rollback-{uuid.uuid4().hex}.tmp")
            rollback.write_bytes(before_bytes)
            os.replace(rollback, project_godot)
            raise StructuredError("input action edit failed and project.godot was rolled back")
        return {
            "ok": True,
            "write_performed": True,
            "result": {
                "action": action,
                "previous_revision": before_revision,
                "revision": _sha_file(project_godot),
                "engine": engine,
            },
        }

    raise StructuredError("unreachable structured operation")


def respond(project: Path, request: Any) -> dict[str, Any]:
    try:
        if not isinstance(request, dict):
            raise StructuredError("request must be an object")
        return {"protocol_version": PROTOCOL_VERSION, **execute(project, request)}
    except (OSError, StructuredError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "ok": False,
            "write_performed": False,
            "error": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--request", default="-")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.request == "-" else Path(args.request).read_text(encoding="utf-8")
        request = json.loads(raw)
        result = respond(Path(args.project), request)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"protocol_version": 1, "ok": False, "write_performed": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
