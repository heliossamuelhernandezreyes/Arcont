# ARCONT production observation — FISURA 0.3 (Godot)

**Record:** ARC-GODOT-OBS-FISURA-0001  
**Date:** 2026-10-07 (America/Monterrey)  
**Engine:** Godot `4.7.2-stable`, expected upstream commit `ed1daf0bf001b61586d9930840f2f1394092c079`  
**Production repository:** [FISURA](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-)  
**Game evidence report:** [ARCONT_FIELD_REPORT_V03.md](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-/blob/main/docs/ARCONT_FIELD_REPORT_V03.md) (once integrated)  
**Evidence class:** CI source/integration validation + software-rendered screen captures. No Android runtime measurements.  
**Maturity:** L2–L3 for isolated executable integration checks, L1 for proposed gameplay/visual quality extrapolation.

## Question

Can a consumer game use ARCONT as a technical bank, asset provenance index and executable semantic validator to develop a visual 3D vertical slice without embedding game code into ARCONT?

## Experiment design and observations

FISURA's independent repository contains the Godot project, its art and scripts. The CI retrieves an **immutable ARCONT revision** of `tools/map_forge_contract.py`, checks the canonical level JSON, imports Godot and executes a scripted extraction. The scene consumes semantic anchors and world obstacles directly from that JSON. This tests integration, not the ability of ARCONT to write or render a game autonomously.

As a new observation in version 0.3, the canonical map declares **11 physical world props and 2 cover guides**. `scripts/tactical_grid.gd` uses the same colliders to rasterize a coarse 1 m AStarGrid2D and `tests/tactical_validation.gd` asserts both reactor and cover detours and objective connectivity. Enemy steering uses cached requests plus direct line-of-sight tests. This is **not** a Recast/Detour navmesh, does not bake scene geometry, and is not crowd avoidance parity.

Art production uses source-traced CC0 records in the ARCONT Asset Vault to select 1K Poly Haven photogrammetric material sets `concrete_wall_007`, `concrete_floor_worn_02`, and `green_metal_rust`, and two previously imported glTF props. The production repo independently vendors official file bytes with `PROVENANCE.json` and SHA-256. **The ARCONT catalog contained metadata, not mirrored asset binaries**; Godot importing an asset cannot be assumed merely from catalog compatibility flags.

## Negative findings worth reusing

1. **Strict GDScript type inference:** Godot 4.7.2 import failed on `var x := side_x * 19.2` and `var z := side_z * 19.2` in a loop with Variant iterables. Explicit `float(side_x)` and annotated `var x: float` resolved it. A code-generation workflow must run a real import/parse check rather than rely on source heuristics.
2. **Functional CI ≠ visual pass:** Import, 120-frame smoke and extraction tests were green while a 3D screenshot showed the tall south wall obscuring most of the scene. A follow-up camera clamp prevented being placed beyond the enclosure but produced overly top-down framing. Rendering captures plus human review were needed to refine framing; camera-bounds tests alone are insufficient for image quality.
3. **Arcont asset registries ≠ drop-in assets:** Source-confirmed CC0 did not imply ready-to-load binaries, resolved glTF texture URLs or Godot-compatible import. Every external resource needed official origin, hash and an actual Godot import gate.
4. **Material quality ≠ AAA result:** Even with triplanar packed ARM, normal maps, authored prop meshes and a procedural industrial shell, complete AAA-level visual credibility is unproven and requires high-quality authored models, lighting, animation, production audio, effects and art direction.

## Reusable workflow pattern

`ARCONT source/standards → game-owned semantic contract → asset license vetting → game-owned runtime/geometry → Godot import + scripted tests → actual screenshot artifact → human visual audit → revised game → ARCONT observation`.

Do **not** copy production gameplay into ARCONT. The project must retain its `production_game_code_allowed=false` and `embedded_godot_project_allowed=false` invariants. Reusable future additions: a declarative AI-ready environment specification with gameplay geometry and visual projection kept separate, viewport screenshot regression criteria, asset provenance validation, and grid/navmesh side-by-side experiments.

## Evidence boundaries

Passing a Linux software-rendered Godot workflow verifies successful import, running code and an actual viewport capture **in that environment only**. It does not verify animation quality, tactile response, Android thermals, GPU draw calls, 60/120 FPS sustainability, or claim commercial AAA quality.

Exact latest CI and PR identifiers remain in the FISURA repository's [Actions page](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-/actions) and its [FISURA v0.3 source branch](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-/tree/feat/fisura-v03-industrial-combat).
