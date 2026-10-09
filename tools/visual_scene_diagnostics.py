#!/usr/bin/env python3
"""ARCONT P1 visual diagnostic metrics, computed from real external Godot tree snapshots.

Read only. Distinguishes structural facts, planning-budget warnings and hypotheses
that need camera review. Neither engine performance nor artistic quality is scored.
The supplied snapshot is NOT independently authenticated by this CLI.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
from typing import Any

try:
    from tools.visual_production_contract import _safe_path, validate_intent
    from tools.visual_scene_inventory import _runtime_snapshot, LIGHTS, MESHES
except ModuleNotFoundError:
    from visual_production_contract import _safe_path, validate_intent
    from visual_scene_inventory import _runtime_snapshot, LIGHTS, MESHES

MAX_NODES = 20000
MAX_BYTES = 16 * 1024 * 1024
STAGES = {
    "art": "Direccion artistica - Crisol",
    "cinematic": "cinematic industrial dressing",
}
METRIC_KEYS = ("kind", "resource_path", "albedo_color", "metallic", "roughness",
               "normal_enabled", "emission_enabled", "albedo_texture")


def _vec3(v: Any, *, field: str) -> tuple[float, float, float] | None:
    if v is None:
        return None
    if not isinstance(v, list) or len(v) != 3 or any(type(a) not in (int, float) or not math.isfinite(a) for a in v):
        raise ValueError(f"{field}: world_position must contain three finite numbers")
    return (float(v[0]), float(v[1]), float(v[2]))


def _distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _signature(mat: dict) -> str:
    vals = {}
    for k in METRIC_KEYS:
        val = mat.get(k)
        if isinstance(val, float):
            val = round(val, 3)
        vals[k] = val
    return json.dumps(vals, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _stage(path: str) -> str:
    if STAGES["cinematic"] in path:
        return "cinematic_dressing"
    if STAGES["art"] in path:
        return "industrial_art"
    return "gameplay_and_other"


def analyze(project: Path, scene_path: str, snapshot_path: Path, intent_path: Path) -> dict:
    root = project.resolve()
    scene_file = _safe_path(root, scene_path)
    if not scene_file.is_file():
        raise ValueError("scene file missing")
    raw = snapshot_path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("native snapshot too large")
    payload = json.loads(raw)
    expected_sha = hashlib.sha256(scene_file.read_bytes()).hexdigest()
    runtime = _runtime_snapshot(snapshot_path, scene_path, expected_sha)
    intent = json.loads(intent_path.read_text(encoding="utf-8"))
    errors, warnings = validate_intent(intent, root)
    if errors:
        raise ValueError("visual intent errors: " + "; ".join(errors[:8]))
    if runtime["renderer"] != intent["render_profile"]["renderer"]:
        raise ValueError("renderer does not match visual intent")
    game_map = json.loads(_safe_path(root, intent["semantic_map"]["path"]).read_text(encoding="utf-8"))
    anchors = {row["id"]: row for row in game_map.get("anchors", [])}
    semantic_props = {row["id"]: row for row in game_map.get("authoring", {}).get("world_props", [])
                      if isinstance(row, dict) and isinstance(row.get("id"), str)}
    nodes = payload["nodes"]
    if len(nodes) > MAX_NODES:
        raise ValueError("node limit exceeded")

    types: Counter = Counter()
    stages: dict[str, Counter] = defaultdict(Counter)
    geometry: Counter = Counter()
    material_signatures: Counter = Counter()
    texture_refs: Counter = Counter()
    asset_source_labels: set[str] = set()
    material_total = normal_count = emissive_count = albedo_textured = 0
    generated_materials = 0
    meshes: list[dict] = []
    local_lights: list[dict] = []
    all_lights: list[dict] = []
    suspicious_colliders: list[str] = []
    semantic_collision_nodes: list[str] = []
    semantic_collider_mismatches: list[str] = []
    unmeasured_semantic_box_sizes = 0
    missing_light_positions = 0

    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("type"), str) or not isinstance(node.get("path"), str):
            raise ValueError("malformed node record")
        typ = node["type"]
        node_path = node["path"]
        stage = _stage(node_path)
        types[typ] += 1
        stages[stage]["nodes"] += 1
        if typ in ("StaticBody3D", "RigidBody3D", "CharacterBody3D", "CollisionShape3D", "Area3D"):
            stages[stage]["physical_or_area_nodes"] += 1
            if stage != "gameplay_and_other":
                # An art authoring stage can contain legitimate GAMEPLAY colliders
                # materialized from the canonical Map Forge world_props entries.
                # Their placement and dimensions, not their subtree label, decide.
                parts = node_path.split(STAGES["art"] + "/", 1)
                suffix = parts[1].split("/") if len(parts) == 2 else []
                prop_id = suffix[0][:-len(" colision")] if suffix and suffix[0].endswith(" colision") else None
                semantic = semantic_props.get(prop_id) if stage == "industrial_art" else None
                body_node = typ == "StaticBody3D" and len(suffix) == 1
                box_node = typ == "CollisionShape3D" and len(suffix) == 2 and suffix[1].startswith("@CollisionShape3D")
                if semantic is not None and (body_node or box_node):
                    center = _vec3(semantic.get("position"), field=prop_id + ".position")
                    declared_size = _vec3(semantic.get("collider_size"), field=prop_id + ".collider_size")
                    observed = _vec3(node.get("world_position"), field=node_path)
                    expected = center if body_node else (center[0], center[1] + declared_size[1] * 0.5, center[2])
                    if observed is None or _distance(observed, expected) > 0.15:
                        semantic_collider_mismatches.append(node_path + ": position disagrees with Map Forge")
                    elif box_node and node.get("box_shape_size") is not None and _distance(_vec3(node["box_shape_size"], field=node_path), declared_size) > 0.02:
                        semantic_collider_mismatches.append(node_path + ": collision dimensions disagree with Map Forge")
                    else:
                        semantic_collision_nodes.append(node_path)
                        if box_node and node.get("box_shape_size") is None:
                            unmeasured_semantic_box_sizes += 1
                else:
                    suspicious_colliders.append(node_path)
        if "Poly Haven CC0 |" in node_path:
            # A model has many child nodes. Report labels, NOT asset count.
            asset_source_labels.add(node_path.split("Poly Haven CC0 |", 1)[1].split("/", 1)[0])
        if typ in LIGHTS:
            pos = _vec3(node.get("world_position"), field=node_path)
            if pos is None:
                missing_light_positions += 1
            color = node.get("light_color", "")
            energy = node.get("light_energy")
            if color and (not isinstance(color, str) or len(color) != 6):
                raise ValueError("malformed light color")
            if energy is not None and (type(energy) not in (int, float) or not math.isfinite(energy) or energy < 0):
                raise ValueError("invalid light energy")
            rng = node.get("light_range")
            if rng is not None and (type(rng) not in (int, float) or not math.isfinite(rng) or rng < 0):
                raise ValueError("invalid light range")
            info = {"path": node_path, "type": typ, "shadow_enabled": node.get("shadow_enabled"),
                    "color": color, "energy": energy, "range_m": rng,
                    "world_position": list(pos) if pos is not None else None}
            all_lights.append(info)
            stages[stage]["lights"] += 1
            if node.get("shadow_enabled"):
                stages[stage]["shadowed_lights"] += 1
            if typ in {"OmniLight3D", "SpotLight3D"}:
                local_lights.append(info)
        if typ in MESHES:
            pos = _vec3(node.get("world_position"), field=node_path)
            instances = node.get("instance_count", 1)
            if type(instances) is not int or instances < 0 or instances > 1_000_000:
                raise ValueError("invalid mesh instance_count")
            stages[stage]["mesh_nodes"] += 1
            stages[stage]["instances"] += instances
            mesh_type = node.get("geometry_type", "unrecorded")
            if not isinstance(mesh_type, str) or len(mesh_type) > 150:
                raise ValueError("invalid geometry type")
            geometry[mesh_type] += instances
            meshes.append({"path": node_path, "stage": stage, "position": pos,
                           "geometry_type": mesh_type, "instances": instances})
            records = node.get("material_descriptors", [])
            if not isinstance(records, list) or len(records) > 100:
                raise ValueError("invalid material descriptors")
            for material in records:
                if not isinstance(material, dict):
                    raise ValueError("invalid material descriptor")
                material_total += 1
                material_signatures[_signature(material)] += 1
                if material.get("normal_enabled") is True:
                    normal_count += 1
                if material.get("emission_enabled") is True:
                    emissive_count += 1
                if material.get("albedo_texture"):
                    albedo_textured += 1
                    texture_refs[str(material["albedo_texture"])] += 1
                if not material.get("resource_path"):
                    generated_materials += 1

    zones: list[dict] = []
    budget_warnings: list[dict] = []
    for zone in intent["zones"]:
        anchor_id = zone.get("anchor_id")
        radius = zone.get("sample_radius_m", 8)
        row = {"id": zone["id"], "role": zone["role"], "lighting_profile_id": zone["lighting_profile_id"],
               "anchor_id": anchor_id, "sample_radius_m": radius,
               "sampling_status": "unavailable", "mesh_centers_in_radius": None,
               "lights_reaching_anchor": None}
        if anchor_id is not None:
            if anchor_id not in anchors:
                raise ValueError(f"zone {zone['id']} references unknown map anchor {anchor_id}")
            p = anchors[anchor_id].get("position")
            point = _vec3(p, field=anchor_id)
            if point is None:
                raise ValueError("map anchor lacks 3D position")
            near = [mesh for mesh in meshes if mesh["position"] is not None and
                    _distance(point, mesh["position"]) <= radius]
            reaching = [light for light in local_lights if light["world_position"] is not None
                        and light["range_m"] is not None and
                        _distance(point, light["world_position"]) <= light["range_m"]]
            row["sampling_status"] = "anchor_center_only_not_camera_visibility"
            row["mesh_centers_in_radius"] = len(near)
            row["mesh_centers_by_stage"] = dict(Counter(m["stage"] for m in near))
            row["lights_reaching_anchor"] = len(reaching)
            row["light_colors_reaching_anchor"] = [l["color"] for l in reaching]
            row["max_light_range_intersections_not_occlusion_aware"] = True
            matching_profile = next(x for x in intent["lighting_profiles"] if x["id"] == zone["lighting_profile_id"])
            if len(reaching) > matching_profile["local_light_budget"]:
                budget_warnings.append({
                    "code": "ZONE_LOCAL_LIGHT_OVERLAP_ESTIMATE",
                    "zone": zone["id"], "observed_reaching_anchor": len(reaching),
                    "design_budget": matching_profile["local_light_budget"],
                    "message": "Light-range intersection exceeds zone planning budget; requires Godot/GPU review"
                })
            if len(reaching) == 0:
                budget_warnings.append({
                    "code": "ZONE_WITHOUT_LOCAL_LIGHT_AT_ANCHOR",
                    "zone": zone["id"],
                    "message": "No local light reaches objective anchor center; directional/emission may still provide sufficient light"
                })
        zones.append(row)

    budget = intent["budgets"]
    if len(local_lights) > budget["max_local_lights"]:
        budget_warnings.append({"code": "TOTAL_LOCAL_LIGHTS_EXCEED_DESIGN_BUDGET",
                                "observed": len(local_lights), "budget": budget["max_local_lights"]})
    shadowed = sum(x["shadow_enabled"] is True for x in all_lights)
    if shadowed > budget["max_shadowed_lights"]:
        budget_warnings.append({"code": "SHADOWED_LIGHTS_EXCEED_DESIGN_BUDGET",
                                "observed": shadowed, "budget": budget["max_shadowed_lights"]})
    instances = sum(m["instances"] for m in meshes)
    if instances > budget["max_visible_instances"]:
        budget_warnings.append({"code": "TOTAL_INSTANCES_EXCEED_VISIBLE_DESIGN_BUDGET",
                                "observed_total_not_visible": instances,
                                "budget_visible_instances": budget["max_visible_instances"],
                                "message": "Total instanced meshes != visible instances; comparison is conservative and not a failed render gate"})

    facts = {
        "node_count": len(nodes), "node_classes": dict(types.most_common()),
        "mesh_nodes": len(meshes), "total_mesh_instances": instances,
        "mesh_instances_by_geometry_type": dict(geometry.most_common()),
        "stage_breakdown": {k: dict(v) for k, v in sorted(stages.items())},
        "local_light_count": len(local_lights), "all_light_count": len(all_lights),
        "shadowed_light_count": shadowed, "lights": all_lights,
        "materials": {"observed_descriptors": material_total,
                      "unique_parameter_signatures": len(material_signatures),
                      "most_repeated_signature_counts": material_signatures.most_common(8),
                      "normal_enabled_descriptors": normal_count,
                      "emission_enabled_descriptors": emissive_count,
                      "textured_albedo_descriptors": albedo_textured,
                      "unpathed_material_descriptors": generated_materials,
                      "unique_albedo_texture_paths": len(texture_refs),
                      "albedo_texture_references_top": texture_refs.most_common(12)},
        "source_labeled_prop_roots": len(asset_source_labels),
        "source_labels": sorted(asset_source_labels)[:60],
        "suspicious_collider_paths_in_art_stages": suspicious_colliders[:40],
        "total_suspicious_colliders": len(suspicious_colliders),
        "gameplay_semantic_collision_nodes_in_art_stage": len(semantic_collision_nodes),
        "gameplay_semantic_collider_paths_in_art_stage": semantic_collision_nodes[:40],
        "semantic_collider_mismatches": semantic_collider_mismatches[:40],
        "unmeasured_semantic_box_sizes": unmeasured_semantic_box_sizes,
        "light_positions_missing": missing_light_positions,
    }
    observations = [
        {"code": "STATIC_VS_DYNAMIC", "note": "Counts describe executed scene snapshot, NOT static .tscn inventory"},
        {"code": "MATERIAL_REPETITION", "note": "Unique parameter signatures are not equivalent to unique authored materials or visual similarity"},
        {"code": "GPU_COST_UNKNOWN", "note": "Draw calls, actual visibility, frame pacing, shadows, HDR and Android performance were NOT measured"},
        {"code": "EXTERNAL_EVIDENCE", "note": "Source_commit/native flags in JSON are supplied metadata; verify GitHub Actions receipt and artifact hashes"}
    ]
    if missing_light_positions:
        observations.append({"code": "MISSING_LIGHT_POSITIONS",
                             "note": "No safe spatial lighting claim for lights without world_position"})
    if semantic_collider_mismatches:
        budget_warnings.append({"code": "GAMEPLAY_MAP_COLLIDER_MISMATCH",
                                "count": len(semantic_collider_mismatches),
                                "message": "Game-owned collider differs from its Map Forge world_props position/size; verify before modifying"})
    if suspicious_colliders:
        budget_warnings.append({"code": "PHYSICS_INSIDE_RENDER_STAGES",
                                "count": len(suspicious_colliders),
                                "message": "Inspect geometry physically, do not infer all descendants are gameplay-authoritative"})
    return {
        "ok": True, "protocol": "arcont-visual-scene-diagnostics", "version": 1,
        "writes_performed": False, "engine_executed": False, "network_used": False,
        "evidence_status": "externally_supplied_runtime_snapshot_unverified",
        "scene_path": scene_path, "scene_sha256": expected_sha,
        "source_commit": runtime["source_commit"],
        "snapshot_sha256": runtime["snapshot_sha256"],
        "renderer": runtime["renderer"],
        "intent_sha256": hashlib.sha256(intent_path.read_bytes()).hexdigest(),
        "facts": facts, "zones": zones, "budget_warnings": budget_warnings,
        "limitations": warnings + observations,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--scene", required=True)
    p.add_argument("--snapshot", type=Path, required=True)
    p.add_argument("--intent", type=Path, required=True)
    args = p.parse_args()
    try:
        report = analyze(args.project_root, args.scene, args.snapshot, args.intent)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        report = {"ok": False, "error": str(exc), "writes_performed": False}
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
