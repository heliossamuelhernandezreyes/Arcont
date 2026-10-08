# FISURA 0.8 — Industrial art / cinematic QA field research

**Observation ID:** ARC-OBS-FISURA-VISUAL-008  
**Engine and test harness:** Godot 4.7.2-stable, Linux CI under Xvfb  
**Product:** [FISURA](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-), feature branch `feat/fisura-v08-cinematic-industrial`  
**Date:** 2026-10-08  
**Classification:** screenshot-guided engineering observation; **NOT proof of AAA visuals, motion quality or Android performance**.

## Tested question

Do the existing ARCONT Map Forge, asset licensing catalog and graphics foundations expose enough information to prevent a large but unconvincing procedural arena, guarantee coherent camera frames, and allow an LLM to assemble more credible commercial game art without accidentally embedding game logic in ARCONT?

**Finding:** useful but not sufficient. Existing source-traced model licenses and map contracts supported implementation, yet screenshot analysis detected an unambiguous visual/camera failure that semantic/physics gates did not.

## What the game actually changed

- Reactivo-13 is **84×66**; legacy art-stage decorative architecture was dimensioned around a **44×44** Crisol. Using identical art generation for both maps created empty composition and spatial incoherence. FISURA introduced a dedicated game-owned presentation script for the larger level.
- New render content used three earlier **CC0 Poly Haven 1K PBR** material sets for structural flooring, weathered concrete and metal, plus preexisting Poly Haven glTF barrels/lamps.
- To move beyond procedural cubes alone, FISURA vendored two additional 1K PBR **real model binaries**, `industrial_storage_cart` and `industrial_pastic_container`, from the official Poly Haven API. These were recorded with full file dependency closure and SHA-256 manifests.
- For the third combat role, a high-detail Quaternius `Enemy_Trilobite` rig with **9 source animation clips** was selected instead of a geometrical placeholder Bulwark. The creator's asset is CC0 according to the already-verified source pack. **Import/runtime validation of this role must remain separate from sourcing.**
- Dedicated mission stage contains architecture, machine banks, roof, reactor containment, wayfinding signage, extraction lights and industrial pipes. It also introduces a conservative mobile light budget; package size and thermal cost require measurement on device.

## A real failure that ordinary QA missed

The first four-camera render set showed **almost the entire Node A screenshot replaced by a giant tan machinery surface**. Godot and the mission FSM could still parse and run. The decorative machine used a MeshInstance3D with **no collision**, so the gameplay camera's physics raycast did not report the obstruction. The original placement near the node coincided with the shoulder camera's standing position.

**Fix:** move bulky processing machinery to the outer factory perimeter, leaving the mission terminal sightlines clear. **Regression:** inspect bounding volumes of decorative machine pieces against mission-camera probes in `tests/reactivo_art_qa.gd`. Also capture all **four** actual views (insertion, node A, reactor, extraction) under Xvfb.

**ARCONT knowledge gap:** physics/collider validation `!=` camera/visual occlusion validation. Future source-neutral standards should consider geometry AABB and visual-shot collision, not merely Godot PhysicsServer objects. A visual-only mesh can block nearly every pixel while all navigation contracts remain green.

## QA evidence tiers to add to future tools

| Gate | Check | Can prove | Cannot prove |
|---|---|---|---|
| V0 — source/provenance | License, hashes, complete glTF texture/BIN dependencies | File origins/reproducibility | Godot imported mesh correctly |
| V1 — real scene import | Godot loads source scene, skeleton and materials | Engine can read and instantiate models | Production quality, realistic motion |
| V2 — scene metrics | Bounded object count, instanced tiles, light budgets, camera away from known décor AABBs | Specific static presentation/quantity invariants | GPU memory usage, draw-call count, silhouette credibility |
| V3 — visual pack | Actual captured 1280×720 game frame at named deterministic views | The engine rendered pixels from those camera poses | That the view feels attractive, is legible under motion, or performs on Android |
| V4 — human art review | Composition, silhouette, light separation, spatial legibility, material quality and UI review | Subjective recorded visual issues | Measured thermal performance |
| V5 — mobile device | Real sustained GPU timings, frame pacing, memory and touch latency | Quality for named device/settings/session | All-tier Android/general AAA performance |

## Future ARCONT reusable tooling

1. **Visual-shot manifest:** authored camera node/pose (or objective-relative pose), target, render resolution, phase, shot filename and comparison expectation. Keep generated PNGs in game CI, metadata and standards in ARCONT.
2. **Visual collision audit:** intersect anticipated camera volumes/sightline segments with *both* physical colliders and independent presentation mesh bounds. Require negative examples where a raycast-based gate would pass but visual geometry occludes.
3. **Art complexity accounting:** count reusable materials, mesh instances, and light/shadow settings, explicitly separating those from measured GPU draw calls / triangles / frame time.
4. **Render-human loop:** after each geometry pass, audit four deterministic screenshots, note the largest legibility failure, fix **that** before adding more objects, and preserve previous passing test scenes.
5. **Asset category precision:** some asset-catalog entries had `asset_type="unknown"`, so do not preload a purported 3D model until official supplier data confirms its type and all dependencies. `asset_type=2` in provider metadata identifies a model, but engine compatibility still needs importing.
6. **AAA claim boundary:** real photogrammetry assets and a dense industrial shell alone do not create AAA look. Require authored character quality, motion blending/IK, lighting direction, professional sound and high-cost iteration, along with measurable frame pacing and human user testing.

ARCONT itself remains a **technology laboratory**, not the home of FISURA's gameplay scripts, textures, renderer, Android APK or a separate embedded Godot project.
