# Arcont — Full Game Audit 2026-08-29

Status: EVIDENCE / REFERENCE-LAB / FULL-SWEEP

## Scope
This audit compares the current playable branch `feat/cc0-provisional-art-pass` (Android build from commit `8669a318705813da478b161de45599546fd32bc9`, Godot CI #488) against the current `research/reference-lab` guidance and direct Android screenshots supplied after installing the #488 APK.

This is a repository + integration + visual/device evidence audit. It is not a claim that GPU frame time, thermals, battery, input latency or long-session stability have already been measured; those remain explicit device gaps.

## Executive verdict
The build is technically runnable and its architecture contains substantially more functionality than its current presentation suggests, but it is **not an accepted vertical-slice build**. Several systems that pass structural CI do not satisfy their actual runtime/visual contract on Android.

The most important discovery is that current regressions are not explained by the art branch simply missing the prior camera work. `feat/cc0-provisional-art-pass` is a descendant of both current `main` history and `fix/mobile-camera-foundation`; the TPS scripts and nodes remain present. The failures are therefore runtime integration, representation and validation failures inside the descendant build.

## P0 — player third-person runtime contract is false-positive
Production evidence:
- `scenes/main.tscn` mounts `BodyVisual`, the Kenney operator, `CameraRig/SpringArm3D/Camera3D`, `ThirdPersonADS`, `TacticalMobility`, and the weapon path.
- `scripts/player.gd` remains camera-relative and rotates the visible body toward aim/movement direction.
- `scripts/third_person_ads.gd` owns shoulder offsets, hip/ADS distance, SpringArm collision and near-camera body visibility.
- `tests/rig_asset_test.gd` verifies the TPS node graph, camera offsets, active camera, runtime AnimationPlayer/AnimationTree, filtered ADS tracks and weapon bone attachment.

Android evidence:
- The supplied gameplay screenshots do not show the player's operator in the expected over-the-shoulder composition.

Finding:
The TPS system exists structurally but the current test does not prove the rendered operator is actually visible in the camera image. It verifies scene nodes and state, not screen-space visibility, framing, deformation, clipping or device renderer output. The current green test is therefore insufficient as a TPS acceptance contract.

Required correction:
1. diagnose whether the operator is hidden by `_update_near_camera_visibility`, outside the actual frustum, scale/import orientation, render-layer/visibility behavior or a combination;
2. create an integration capture that explicitly requires the operator silhouette at hip camera distance and verifies a different ADS framing;
3. validate on Android, including open terrain and SpringArm-compressed door/wall cases;
4. do not label TPS accepted until the body is visibly present and correctly framed on device.

## P0 — infected animation contract is false-positive
Production evidence:
- `enemy.tscn` mounts `CC0Visual` plus the legacy segmented anatomical fallback.
- `zombie_cc0_visual.gd` prioritizes `InfectedCityMan.fbx`, finds an AnimationPlayer and searches animation names by loose tokens. If no requested token matches, it falls back to the first non-RESET animation.
- `tests/zombie_visual_test.gd` verifies that the realistic shell loads, is human-scale, exposes a non-empty animation list and falls back correctly after severing.

Android evidence:
- Multiple infected are visibly in bind/T-pose.

Finding:
The current zombie test proves that an animation library exists, **not that the selected clip deforms the active skeleton into a valid locomotion/attack pose**. A non-empty animation list is not a sufficient animation contract. The fallback-to-first-animation behavior can also hide semantic incompatibility between desired state and available clip.

Required correction:
- audit actual animation names, tracks, target paths, skeleton rests and bone mapping for the primary infected;
- require deterministic idle/walk/attack states rather than arbitrary first-animation fallback;
- add runtime pose/deformation validation and a representative rendered capture;
- retain the segmented anatomical fallback only as an explicit gameplay fallback, not as a substitute for validating the intact shell.

## P0 — visual acceptance process regression
`research/art/VISUAL_ACCEPTANCE_2026-08-29.md` already records that CI success, script existence and successful screenshots are insufficient for visual acceptance. The latest Android evidence nevertheless exposes forest, architecture, lighting, surface and character failures after an artifact named `ForestVillage-Polished` was produced.

Finding:
The process lesson existed but was not enforced as a release gate. This is a process defect, not just an art defect.

New operational rule:
- CI may say `STRUCTURALLY_VALIDATED` or `EXPORTABLE`.
- A build/art block may say `VISUALLY_ACCEPTED` only after representative runtime captures and Android inspection pass.
- Artifact names must not contain `Polished`, `Final` or equivalent acceptance language while `visual_acceptance` or `device_validation` remains pending.

## P1 — forest architecture is performant in the right direction but visually rejected
Production `forest_strata_pass.gd` now uses spatial MultiMesh cells for trunks, crowns and understory. This is architecturally preferable to thousands of individual MeshInstance3D nodes and aligns with the Reference Lab mobile guidance.

However, the content is explicitly primitive-generated: CylinderMesh trunks and SphereMesh crowns/bushes, with `final_tree_asset=false`. Android evidence shows the predictable result: repetitive lollipop crowns, rows of thin trunks, oversized dark understory blobs that read as rocks, and trees/canopy dominating or clipping the camera.

Finding:
The **instancing strategy can remain**, but the current tree/bush archetypes are rejected. More primitive density will not solve the visual problem.

Required correction:
- replace procedural cylinder/sphere tree archetypes with audited real tree/bush meshes;
- preserve spatial cells/MultiMesh/HLOD where suitable;
- create occupancy masks for roads, player camera corridors, house footprints, entries, mission objects and tactical sightlines;
- vary age/species/silhouette deliberately rather than by random scale alone;
- keep transparent foliage costs under Android profiling control.

## P1 — architecture exists as a modular generator but still reads as greybox
Production contains `modular_house_builder.gd`, eight placed house specs and a modular architecture pass, so the system is not the old single-mesh placeholder architecture.

The Android result still fails the Reference Lab architecture grammar: buildings present as large light-colored blocks with weak facade bays, openings, roof depth, foundations, trim, material hierarchy and abandonment layers. They do not yet read as believable occupied-then-abandoned village structures.

Finding:
The architecture direction is correct; its current authored output is not production-quality. Do not replace the modular system with monolithic meshes merely to hide the problem. Improve the module grammar and lot composition.

## P1 — runtime art-pass stack has become a maintainability and ownership risk
`modular_village_architecture_pass.gd` dynamically mounts ten separate corrective passes: continuous route, urban structure, map composition, forest tone, atmosphere, readability, prop tone, organic forest proxy, surface cleanup and forest strata.

Finding:
This incremental layering allowed fast experimentation, but it now makes ownership, ordering, overlaps, visibility replacement, occupancy and visual debugging difficult. Several current defects are characteristic of additive correction layers fighting one another: vegetation/building intersections, broad patch surfaces, tone overrides and multiple forest representations.

Required correction:
After the current recovery, consolidate the accepted world representation into clearer authored/data-driven ownership boundaries. Temporary visual passes should either graduate into a stable subsystem or be removed/superseded explicitly.

## P1 — lighting/readability fails its own stated contract on Android
`village_atmosphere_pass.gd` is labeled `READABLE-DUSK`, yet direct device captures show crushed blacks and poor separation between canopy, trunks, ground, buildings and enemies.

Finding:
The numeric lighting settings are not evidence of readability. Android exposure/material response must be the acceptance source. Enemy silhouettes must remain separable from background values, as required by `ENVIRONMENT_ART.md`.

Required correction:
Rebalance ambient/key/fog/material values using device captures; preserve dark atmosphere without collapsing navigable surfaces and combat silhouettes into black masses.

## P1 — road/ground and occupancy are still visually procedural
Android screenshots expose hard polygon boundaries, broad flat-looking road/ground regions and vegetation placed too close to buildings/routes/camera.

Finding:
Terrain ownership and terrain-following routes are structurally improved, but visual surface composition and semantic placement masks remain incomplete. Numeric terrain adherence is not visual acceptance.

## P1 — mobile performance evidence is promising but not validated
Direct screenshots frequently show roughly 50–61 FPS after the MultiMesh refactor and around 3.4k scene nodes, which is materially stronger evidence than CI software-render FPS. This suggests the batching direction is useful.

However, the Reference Lab correctly requires frame CPU/GPU, frame pacing/1% lows, draw calls, primitives, memory, thermal trend and battery under named benchmark scenes. One anomalous capture also showed a pathological very-low-FPS/high-node state, demonstrating why averages and isolated frames are insufficient.

Finding:
Status remains `TESTING`, not validated. Use repeatable Android benchmarks: player + close enemy, 12+ infected, firefight/VFX, village vista, gore/explosion overlap, Xeno stress and mixed worst case.

## P2 — infected AI only partially matches research architecture
`enemy.gd` implements intentionally cheap direct pursuit and local separation, which matches part of the infected budget in `research/ai/architecture.md`. It also reads the player's current node directly and chases current position, with no demonstrated perception/memory/sound-attraction gate in this actor path.

Finding:
For a simple infected baseline this is playable, but it does not yet satisfy the full research architecture principle `perception -> memory -> decision -> movement -> combat`, nor the stated infected sound-attraction behavior. Treat this as AI debt rather than the current visual recovery blocker.

## Research-to-production conformance matrix

| Domain | Reference-Lab target | Current production | Status |
|---|---|---|---|
| Third-person camera | readable TPS on small display, collision-safe shoulder camera | correct nodes/scripts exist; operator absent in Android evidence | REJECTED / runtime regression |
| Player animation | connected locomotion/ADS/action chains, correct retarget/rest | dynamic AnimationTree structurally active; no device visual proof | PARTIAL |
| Infected animation | clean humanoid animation, meaningful transitions | animation list exists; T-pose visible | REJECTED |
| Forest | macro enclosure + readable tactical lanes + mobile instancing | enclosure achieved, primitive archetypes visually poor | PARTIAL / art rejected |
| Architecture | believable modular grammar + lot history + grounding | generator exists, output still box-like | PARTIAL / art rejected |
| Terrain/routes | continuous physical ground owner, coherent overlays | architecture largely aligned; visual patches remain | PARTIAL |
| Lighting | dark but readable combat silhouettes/navigation | device scene too crushed/dark | REJECTED |
| Mobile batching | MultiMesh/reuse/HLOD by profiling | spatial MultiMesh forest cells implemented | IMPLEMENTED architecture / tuning pending |
| Performance | device-scoped CPU/GPU/frame pacing/thermal benchmarks | telemetry + ad-hoc device frames only | TESTING |
| CI | structural, scene, build, perf and device/subjective layers | strong structural/export CI; runtime visual contracts too weak | PARTIAL |
| AI | layered perception/memory/decision/movement/combat | infected direct pursuit + separation | PARTIAL |
| Character art | readable TPS hero, clean deformation, mobile validation | provisional Kenney workbench; not visible as intended | REJECTED as current presentation |

## Root-cause pattern
The recurring issue is **contract substitution**: testing a proxy for the property we actually care about.

Examples:
- `TPS nodes exist` was treated as `player is visibly third-person`.
- `AnimationTree is active` was treated as `player animation looks correct`.
- `animation list non-empty` was treated as `infected is animated rather than T-pose`.
- `CI screenshot exists` was treated as `visual block is acceptable`.
- `route follows heightmap` was previously treated as `route looks natural`.
- `forest instance count/density` was treated as `forest looks like a real forest`.

Future contracts must test the semantic output, not merely the mechanism.

## Recovery order
1. Freeze new visual layering while recovering player TPS visibility and infected animation.
2. Add device/render-facing regression evidence for both character systems.
3. Replace primitive forest archetypes while preserving spatial MultiMesh architecture.
4. Add semantic occupancy/exclusion masks shared by forest, buildings, routes and camera-critical spaces.
5. Rework lighting/readability against Android captures.
6. Bring modular houses to the documented architecture grammar; remove remaining greybox cues.
7. Consolidate temporary art passes after their accepted behavior is known.
8. Run repeatable Android benchmark suite and record device/build/settings plus frame pacing, GPU/CPU and thermal behavior.
9. Revisit infected perception/sound and broader AI architecture after the vertical slice is visually and mechanically coherent.

## Acceptance gate for the next APK
Do not call the next build visually accepted unless all of these are observed in representative Android play:
- player body is visible and framed correctly in hip TPS and ADS;
- player locomotion state changes visibly and without bind/T-pose;
- infected visibly animate in idle/chase/attack and no intact actor remains in T-pose;
- forest reads as natural layered vegetation, not cylinders/spheres/rows;
- vegetation does not invade house footprints, doors, core routes or camera-critical space;
- houses read as constructed architecture rather than large blocks;
- road/ground boundaries do not present obvious procedural plates/patch polygons;
- combat silhouettes remain readable in dusk lighting;
- the tested device maintains acceptable frame pacing in a defined combat benchmark, not just an empty-vista average.

## Confidence
High for repository architecture, test gaps and visual failures directly visible in supplied Android screenshots. Medium for exact root cause of missing player body and infected T-pose until runtime instrumentation/pose inspection isolates the failing visibility/animation path. Performance conclusions are deliberately provisional until repeatable device benchmarks exist.
