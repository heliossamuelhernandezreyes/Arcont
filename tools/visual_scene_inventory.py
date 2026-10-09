#!/usr/bin/env python3
"""Read-only Godot scene inventory for ARCONT P1.

Only statically declared .tscn nodes can be counted without starting Godot.
Optional snapshots from external Godot CI are accepted as SUPPLIED evidence,
not as verified native execution. Never writes, invokes engine, or downloads.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shlex

try:
    from tools.visual_production_contract import _safe_path, validate_intent
except ModuleNotFoundError:
    from visual_production_contract import _safe_path, validate_intent

LIGHTS = {"OmniLight3D", "SpotLight3D", "DirectionalLight3D"}
MESHES = {"MeshInstance3D", "MultiMeshInstance3D", "CSGBox3D", "CSGMesh3D", "CSGCylinder3D"}
NODE_LIMIT = 20000

def _attrs(line: str) -> dict[str, str]:
    return dict(part.split("=", 1) for part in shlex.split(line) if "=" in part)

def _bounded(path: Path, limit: int) -> bytes:
    if path.stat().st_size > limit:
        raise ValueError("source exceeds read limit")
    return path.read_bytes()

def _scene_source(path: Path) -> dict:
    raw = _bounded(path, 4 * 1024 * 1024)
    source = raw.decode("utf-8-sig")
    if not source.lstrip().startswith("[gd_scene"):
        raise ValueError("expected a Godot text scene")
    nodes: list[dict] = []
    external: dict[str, dict] = {}
    active = None
    for line in source.splitlines():
        line = line.strip()
        if line.startswith("[ext_resource "):
            data = _attrs(line[len("[ext_resource "):-1])
            if "id" in data:
                external[data["id"]] = data
            active = None
        elif line.startswith("[node "):
            if len(nodes) >= NODE_LIMIT:
                raise ValueError("node limit exceeded")
            info = _attrs(line[len("[node "):-1])
            active = {"type": info.get("type", "PackedSceneInstance"),
                      "name": info.get("name", ""),
                      "scripted": False, "shadow_enabled": None}
            nodes.append(active)
        elif line.startswith("["):
            active = None
        elif active is not None and "=" in line:
            key, val = (s.strip() for s in line.split("=", 1))
            if key == "script":
                active["scripted"] = True
            if key == "shadow_enabled" and val in ("true", "false"):
                active["shadow_enabled"] = val == "true"
    types = Counter(n["type"] for n in nodes)
    script_paths = sorted(x.get("path", "") for x in external.values() if x.get("type") == "Script")
    return {
        "scene_sha256": hashlib.sha256(raw).hexdigest(),
        "node_count": len(nodes), "type_counts": dict(sorted(types.items())),
        "light_count": sum(types[t] for t in LIGHTS), "mesh_node_count": sum(types[t] for t in MESHES),
        "light_nodes": [{"name": n["name"], "type": n["type"], "shadow_enabled": n["shadow_enabled"]}
                        for n in nodes if n["type"] in LIGHTS],
        "scripted_nodes": sum(n["scripted"] for n in nodes),
        "external_script_paths": script_paths, "external_resources": len(external)
    }

def _runtime_snapshot(path: Path, scene_path: str, sha256: str) -> dict:
    raw = _bounded(path, 16 * 1024 * 1024)
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("protocol") != "arcont-godot-scene-snapshot" or data.get("version") != 1:
        raise ValueError("unknown snapshot protocol")
    if data.get("scene_path") != scene_path or data.get("scene_sha256") != sha256:
        raise ValueError("snapshot scene path/hash mismatch")
    if data.get("capture_source") != "native-godot" or not data.get("engine_version") or not data.get("renderer"):
        raise ValueError("incomplete snapshot engine provenance")
    if not re.fullmatch("[a-f0-9]{40}", str(data.get("source_commit", ""))):
        raise ValueError("snapshot source commit missing or invalid")
    nodes = data.get("nodes")
    if not isinstance(nodes, list) or len(nodes) > NODE_LIMIT:
        raise ValueError("invalid or unbounded snapshot nodes")
    paths: set[str] = set()
    lights = []
    meshes = 0
    instances = 0
    materials: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("path"), str) or not isinstance(node.get("type"), str):
            raise ValueError("malformed runtime node")
        if node["path"] in paths or len(node["path"]) > 500:
            raise ValueError("duplicated/oversized runtime path")
        paths.add(node["path"])
        if node["type"] in LIGHTS:
            if node.get("shadow_enabled") is not None and type(node["shadow_enabled"]) is not bool:
                raise ValueError("invalid shadow setting")
            lights.append({"path": node["path"], "type": node["type"], "shadow_enabled": node.get("shadow_enabled")})
        if node["type"] in MESHES:
            meshes += 1
            count = node.get("instance_count", 1)
            if type(count) is not int or not 0 <= count <= 1000000:
                raise ValueError("invalid instance count")
            instances += count
        refs = node.get("material_paths", [])
        if not isinstance(refs, list) or len(refs) > 100 or any(not isinstance(v, str) for v in refs):
            raise ValueError("invalid material paths")
        materials.update(refs)
    return {
        "evidence_status": "externally_supplied_runtime_snapshot_unverified",
        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "source_commit": data["source_commit"], "engine_version": data["engine_version"],
        "renderer": data["renderer"], "node_count": len(nodes),
        "light_count": len(lights), "light_nodes": lights, "mesh_nodes": meshes,
        "reported_instances": instances, "material_paths_count": len(materials)
    }

def inspect_scene(project: Path, scene: str, intent: dict | None = None,
                  snapshot: Path | None = None) -> dict:
    if not scene.endswith(".tscn"):
        raise ValueError("only .tscn scenes can be inspected")
    file = _safe_path(project.resolve(), scene)
    if not file.is_file():
        raise ValueError("scene not found")
    static = _scene_source(file)
    notes = []
    if static["scripted_nodes"] or static["external_script_paths"]:
        notes.append("Dynamic scripts present: static counts exclude runtime-generated geometry and lighting")
    if any(light["shadow_enabled"] is None for light in static["light_nodes"]):
        notes.append("Shadow defaults not inferred from scene source")
    result = {
        "ok": True, "protocol": "arcont-visual-scene-inventory", "version": 1,
        "writes_performed": False, "engine_executed": False, "network_used": False,
        "scene_path": scene, "scene_sha256": static["scene_sha256"],
        "static_source": static, "runtime": None, "runtime_complete": False,
        "limitations": notes
    }
    if intent is not None:
        problems, warnings = validate_intent(intent, project)
        if problems:
            raise ValueError("visual intent invalid: " + "; ".join(problems[:8]))
        result["intent_crosscheck"] = {
            "zones": len(intent["zones"]), "lighting_profiles": len(intent["lighting_profiles"]),
            "asset_roles": len(intent["asset_roles"])
        }
        result["limitations"].extend(warnings)
    if snapshot is not None:
        runtime = _runtime_snapshot(snapshot, scene, static["scene_sha256"])
        if intent is not None and runtime["renderer"] != intent["render_profile"]["renderer"]:
            raise ValueError("snapshot renderer mismatch")
        result["runtime"] = runtime
        result["limitations"].append("Snapshot self-describes native Godot but is not authenticated without external CI receipts")
    else:
        result["limitations"].append("Runtime node tree unavailable: no complete runtime asset/light inventory")
    result["limitations"].append("No frame-time, mobile-thermal, visibility or artistic-quality proof")
    return result

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--scene", required=True)
    p.add_argument("--intent", type=Path)
    p.add_argument("--snapshot", type=Path)
    args = p.parse_args()
    try:
        intent = json.loads(args.intent.read_text(encoding="utf-8")) if args.intent else None
        report = inspect_scene(args.project_root, args.scene, intent, args.snapshot)
    except (ValueError, OSError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        report = {"ok": False, "error": str(exc), "writes_performed": False,
                  "engine_executed": False, "network_used": False}
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
