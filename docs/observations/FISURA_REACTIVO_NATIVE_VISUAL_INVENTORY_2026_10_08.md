# ARCONT field observation: native FISURA Reactivo-13 runtime visual tree

Date: 2026-10-08 (runner evidence 2026-10-09 UTC).
Consumer project: `heliossamuelhernandezreyes/Godot-juegos-3d.-`, [FISURA visual inventory draft PR #19](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-/pull/19).
Engine: Godot **4.7.2.stable**, Linux headless, `gl_compatibility`.
This is an **external project** observation; no game assets or runtime code are embedded in ARCONT.

## Why this experiment was needed

The main `scenes/reactivo_13.tscn` statically declares one root with a script. The live
mission constructs almost all the level using scripts (`_build_world`, `ArtStage` and
`CinematicStage`). A static TSCN-only audit reports zero local lights, which
would be materially misleading.

## Evidence from real Godot execution

Workflow: [FISURA smoke / ARCONT contract run 37874494036](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-/actions/runs/37874494036).

The Godot runtime exporter emitted a 333,143-byte JSON scene-tree snapshot with
the exact scene-file SHA-256, engine/renderer, native node types and all instantiated nodes.
The `reactivo-13-arcont-native-visual-inventory` Actions artifact stores both the
native snapshot and the independent ARCONT P1 import summary, visual intent validation,
SHA-256 listing and a commit-bound CI receipt. At the time of this field note the full
run was still processing graphical screenshot capture, but its native snapshot import,
P0 intent validation, P1 audit and receipt steps passed.

| Measurement | Source | Result |
|---|---|---|
| Declared static .tscn nodes | ARCONT P1 static source audit | 1 |
| Instantiated runtime nodes | Godot native exporter + ARCONT P1 | 667 |
| Runtime mesh nodes | same | 523 |
| Runtime lights | same | 13 |
| Lights casting shadows | native Light3D.shadow_enabled | 1 |
| Instances incl. MultiMesh | native inventory sum | 858 |
| Material descriptors across meshes | native material observation | 604 |
| Unique normalized material-parameter signatures | analytic observation from native snapshot | 80 |
| Normal-enabled descriptors | same | 194 |
| Emission-enabled descriptors | same | 158 |
| Unique recorded albedo texture paths | same | 10 |
| Nodes with source-labeled Poly Haven lineage | native node path string match (includes descendants) | 22 |

**Interpretation:** near all render geometry is procedurally constructed or dynamically
instanced; many materials share the same parameters across many meshes. Light totals alone
do not establish adequate coverage, shadow contrast or cinematic quality. 
The source-labeled Poly Haven node count includes children and must NOT be treated as
22 independent production props.

## Strong evidence and limitations

- Native Godot executed; output includes scene SHA and checked-out GITHUB_SHA.
- The separate Python CI receipt checks native light roles, procedural materials,
  PBR normal/emission flags, MultiMesh, source-labelled prop geometry and ARCONT
  imported counts. ARCONT still labels the external JSON **unverified** in isolation;
  the GitHub Actions provenance is required to contextualize it.
- These are **counts**, not visible draw calls, shaded pixels, GPU memory, memory pressure,
  camera coverage, image fidelity, smoothness or third-party licensing adjudication.
- Headless Linux scene observation is **not** Android profiling and not a human art pass.
- The 80 signatures are unique values of the exported material descriptors, not
  80 distinct authored source files or 80 unique texture sets. All numbers are
  scoped to this exact observed instantiation.

## Reusable engineering rule

A visual-environment audit must distinguish static source, native runtime traversal
and independently bound CI receipts. For script-generated Godot scenes, runtime
observation is indispensable before drawing conclusions about asset density,
lighting budgets or material variation.

## Next improvement candidates

1. Teach ARCONT P1 to aggregate `material_descriptors`, color profiles, normal
   and emission flags, and roles of shadowed lights without scoring "beauty".
2. Identify predominant primitive families (source `mesh.get_class()`) and
   physically meaningful objective/camera coverage.
3. Comparable 1280×720 camera-locked before/after screenshots and an independent
   Android performance trace, with `needs_measurement` if absent.
4. Audit asset rights via existing provenance records before automatically proposing
   replacements; do not use inferred model names as a license receipt.

**Maturity:** observed under one Linux Godot 4.7.2 CI context, not yet reproduced
across hardware; no ARCONT 1.2 release claim.

## P1 follow-up: spatial light and Map Forge collision reconciliation

Follow-up FISURA run: [workflow 37876895542](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-/actions/runs/37876895542), with external ARCONT `visual.scene.diagnose` and native `world_position` / box collider size observations.

- Five linked mission anchors sampled at radii 9 / 9 / 9 / 11 / 9 m, with mesh-center counts `20 / 25 / 24 / 52 / 28`.
- Lights whose range contains the anchor center: insertion **3**, Node A **2**, Node B **2**, reactor **4**, extraction **3**. Insertion and extraction exceed their declared **2 local lights** per-zone planning budgets. The result is a **warning to review**, not a measured lighting failure.
- The earlier stage-path heuristic detected **18 physical nodes** inside industrial art. Source review of `scripts/art_stage.gd` proved these are actually **9 valid gameplay-owned StaticBody3D and CollisionShape3D pairs** generated from `maps/reactivo_13.json` `authoring.world_props`.
- Corrected P1 reconciles all 18 nodes with the map IDs, body positions, collider centers and exact BoxShape3D dimensions. **0 unmapped art-stage collider nodes**, **0 shape/position mismatches** and **0 missing size observations**. This false-positive correction is a primary reason to join visual audit data against game-owned semantics rather than trusting scene-tree folder names.
- Geometry resource instances: **451 BoxMesh**, **384 ArrayMesh**, **19 CylinderMesh**, **3 TorusMesh**, **1 SphereMesh**. The ArrayMesh category includes 336 instanced floor tiles, so the ratios cannot be read directly as distinct hero assets.
- Material descriptors **604**, distinct parameter signatures **80**, unique albedo texture paths **10**; repeated parameter values are not automatically an aesthetic defect.
- The untrusted JSON supplied by the game is still marked external/unverified by Arcont in isolation; the Actions commit-bound receipt and hashed artifact are retained alongside the report.

**Engineering outcome:** first cross-linked diagnosis is real and catches two possible light-range/budget excesses while clearing false physics warnings through Map Forge authority. It is not an Android frame rate test, screen-space illumination measurement or image-quality acceptance.
