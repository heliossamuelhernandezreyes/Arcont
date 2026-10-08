# ARCONT ANIM-004 / Mobile research — FISURA 0.6

**Scope:** External Godot game integration (no game project embedded in ARCONT)  
**Date:** 2026-10-08 UTC  
**Reference game:** [FISURA](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-), branch `feat/fisura-v06-aim-mobile-qa`  
**Engine:** Godot 4.7.2-stable (Linux CI); Android physical test NOT performed.

## Hypothesis and sources

After Quaternius Spacesuit's 62-bone rig and 24 native animations were validated, a bounded post-animation torso correction may reduce purely authored recoil mismatch without retargeting or changing physics. This follows `PROCEDURAL_ANIMATION.md` layered animation research. Godot documents `SkeletonModifier3D` as a post-AnimationMixer stage with influence that must not be applied twice by the modifier.

## Reproducible experiment

The separate FISURA project defines `scripts/vanguard_aim_modifier.gd` inheriting `SkeletonModifier3D`. It resolves `spine`/`chest` bones by source names (no hardcoded bone index), modifies pose local rotations with bounded small recoil and aim correction after the imported clip plays. It does **not** solve IK for hands, feet or terrain contact. The character's `CharacterBody3D` remains independently authoritative for collision and damage.

`tests/vanguard_aim_mobile.gd` instantiates the genuine game scene, validates the modifier belongs to the skeleton and finds one torso bone, sends distinct screen-touch IDs into move and aim zones, invokes a rifle shot and confirms active modifier processing. The observed test run on the prototype branch reported:

- `ARCONT ADDITIVE AIM READY torso_bones=1`
- `VANGUARD AIM PASS torso_bones=1 processed=14 independent_touch=true recoil=true`

This proves post-animation modification was **executed in Linux Godot**, not that the motion is visually natural or performant in Android. The experiment also uncovered the difference between synthetic multitouch event handling and physical touchscreen latency, which must be tested separately.

## Camera observation

A follow-camera needs the same look target at initialization and during updates, ray-based occlusion handling, and frame-consistent interpolation. The existing test checks bounds and proximity, not visual silhouette stability or collider flicker in every camera position. Screenshots should remain part of the gate.

## Android QA protocol

An automated debug APK export uses matching Godot 4.7.2 editor + export template, Android SDK, Java and temporary debug signing. Passing export **only** establishes a package file was generated and archive checks passed. It cannot validate that an Android GPU/driver loads the scene, controls feel correct, or target FPS can be sustained.

Follow `MOBILE_PERFORMANCE_FOUNDATIONS.md`: record p50/p95/p99 frame intervals, cold/warm sessions, display refresh, resolution, CPU/GPU load where supported, heat and touch latency. A 15-minute test is preferable to a short static screenshot benchmark.

## ARCONT reusable improvements

1. Add `ANIM-004` tests proving a SkeletonModifier3D executes after imported clips and has bounded rotations; separate this from real two-bone IK.
2. Require `ANIM-005` comparisons of effector cost and animation-LOD update rates, if actual IK is introduced later.
3. Require stable manifest descriptors of device model, Godot renderer, actual FPS distribution and thermal context for Android claims.
4. Keep game-specific script, export preset, and binary APK in the **game repository**.
5. Explicitly reject conflating APK package success with install/launch/presentation success.

**Evidence level:** automated runtime behavior for the torso correction; Android export packaging is a separate gate and may remain pending/failed until a workflow proves otherwise. No AAA claim.


## Android export failures observed in GitHub Actions

During the first Android packaging experiments, CI found three separate environment/configuration problems, **not gameplay defects**:

1. An Android setup action tried to install the obsolete SDK `tools` package; bypassed by using the runner's existing `cmdline-tools/*/bin/sdkmanager`.
2. `sdkmanager` was installed but not on the default shell PATH; resolved by discovering its absolute path from `ANDROID_HOME`.
3. Godot 4.7.2 refused Android export with the explicit error: `ETC2/ASTC texture compression is required`. The corresponding game project flag is `rendering/textures/vram_compression/import_etc2_astc=true` (under `[rendering]` in `project.godot`).

These examples show why ARCONT should use **real exporter invocation**, verify the specific target-platform texture-import path, and collect tool logs. Source-only project validation and Linux runtime smoke would not detect these Android packaging prerequisites.

No inference about physical-device performance follows from these fixes.
