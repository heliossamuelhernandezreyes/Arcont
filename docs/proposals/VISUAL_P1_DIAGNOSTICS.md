# ARCONT P1 — Native Visual Scene Diagnostics

**Status:** experimental read-only engineering analyzer; not ARCONT 1.2 release.

This extends P0/P1 with the machine-auditable operation `visual.scene.diagnose`,
implemented by `tools/visual_scene_diagnostics.py`, registered as **read-only** and
exposed through Universal Agent Bridge without project-write authorization.

## Input / invocation

ARCONT requires a **real external game root**, its normal `visual.intent.json`,
an exact `.tscn` game scene, a semantic map and a **native tree snapshot**
previously emitted from a running Godot process.

```bash
python tools/visual_scene_diagnostics.py \
  --project-root /games/fisura \
  --scene scenes/reactivo_13.tscn \
  --snapshot /games/fisura/reactivo-13-native-scene-snapshot.json \
  --intent /games/fisura/visual.intent.json
```

Bridge request (all paths project-relative; no arbitrary network or shell):

```json
{
  "protocol":"arcont-bridge","version":1,
  "request_id":"diagnose-visual",
  "operation":"visual.scene.diagnose",
  "arguments":{
    "scene":"scenes/reactivo_13.tscn",
    "intent_path":"visual.intent.json",
    "snapshot_path":"reactivo-13-native-scene-snapshot.json"
  }
}
```

The analyzer accepts the ARCONT P1 snapshot format. For spatial analysis,
each native `Node3D` should additionally expose `world_position: [x,y,z]`;
`MeshInstance3D` / `MultiMeshInstance3D` should expose `geometry_type`.
Older snapshots without these fields remain readable, but **cannot** justify
spatial lighting or named-mesh-category conclusions.

## Metrics and provenance

- **Counts** of instantiated native classes, light classes, visible and shadowed
  lights, MeshInstance/MultiMesh instances, reported geometry resource kinds.
- Material **parameter signatures** (rounded scalar values, flags, colors,
  texture paths). Equal parameter signatures are not necessarily visually
  similar objects, nor distinct authored .tres assets.
- Local-light **sphere/range intersections** with map-owned anchor centers
  referenced by each visual zone, with a project-defined `sample_radius_m`
  for nearby mesh center counts.
- Stage grouping by path classification for the initial FISURA adapter
  (`Direccion artistica - Crisol`, `cinematic industrial dressing`);
  fallback `gameplay_and_other`. Group names are **not** portable truth
  and may need project-specific adapters in future.
- Suspicious physics/collision nodes nested under presentation-only stages.
- Warnings when per-zone **planning budgets** are exceeded or when no local
  light's radius reaches an objective. These are *review signals*, not failures
  of image composition, safety, renderer capability, or actual brightness.
- Strict snapshot SHA-vs-scene and source commit-format checks. The runtime
  JSON still self-declares origin; reproducible CI logs and hashes in the
  external game's run provide the additional evidence context.

**Explicit nonclaims:** ARCONT does **not** estimate actual draw calls, unique
GPU materials, true per-pixel luminance, physically correct light transport,
shadow fidelity, film-quality appearance, FPS, input responsiveness or
Android thermal performance from the snapshot.

The output always declares
`evidence_status=externally_supplied_runtime_snapshot_unverified` and includes
`budget_warnings` separately from `facts`.

## Validation

`tests/test_visual_production.py` includes positive/negative controls for:
- foreign map anchor, unsafe project path, renderer/scene/hash mismatch;
- material signature counts, instance types, physically bounded zone sampling;
- missing local light at a zone's center as **warning**;
- physics node inside render-only stage as review signal;
- nonfinite native `world_position` refusal and read-only Bridge invocation.

The existing ARCONT `Knowledge Integrity` workflow includes these tests;
release remains draft pending full visual capture comparisons and Android.
