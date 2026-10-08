# ARCONT observation: additive aiming and Android CI export (FISURA 0.6)

**Date:** 2026-10-08 UTC  
**Evidence:** [FISURA game source](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-) · [Godot rig/touch regression](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-/actions/runs/37732213764) · [successful debug APK export](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-/actions/runs/37732162049)

## Tested engineering question

Can a Godot 4.7.2 game augment an existing 24-clip/62-bone Quaternius character with bounded aiming and recoil **after** authored animation, unify camera targeting with hitscan, accept two independent touch inputs, and create a source-verified ARM64 Android debug package in CI without putting runtime code in ARCONT?

## Observation

1. **ANIM-002 post-animation modification:** `SkeletonModifier3D` executes after `AnimationMixer`. A subclass can apply bounded pitch/yaw/recoil to the actual `Torso` and `Chest` bones without replacing imported animation tracks. Existing Run/Run_Shoot/Roll/Hit/Death tests still pass. This is an *additive modifier*, **not full IK**. It neither solves foot placement nor computes a two-hand grip.
2. **Bone identity cannot be inferred from generic names:** the skeleton used `Wrist.R`, not `Hand.R`; a first pass did not attach the rifle. Diagnostic bone-name enumeration revealed the mismatch. A subsequent regression test asserts both the wrist mount and separate Torso/Chest source-bone indices. Names are asset-specific; avoid hard-coding guesses as general ARCONT facts.
3. **Ballistic coherence:** before v0.6 the camera projected a cursor into a world plane but the gun hitscan always used a horizontal ray. Using the same camera-projected target for both visual reticle and muzzle ray direction resolves the architectural mismatch. Collision with nearby cover still requires real visual QA.
4. **Multi-touch simulation:** two distinct screen touch IDs and right-side drag event were verified in Godot's scripted test. This proves input routing, not touch latency or comfort on a phone.
5. **Android export is independently testable from Android gameplay.** The CI flow acquired official *matching* Godot 4.7.2 editor and templates, configured OpenJDK 17 and Android SDK, enabled the required ETC2/ASTC texture import flag, signed a debug-only ARM64 package with a disposable key, and uploaded the package with SHA-256. Initial failures came from an obsolete `tools` Android SDK package in the v3 setup action, a missing `sdkmanager` in PATH when the action was removed, and a required ETC2/ASTC project setting. Using `android-actions/setup-android@v4` fixed setup; the Godot import toggle fixed export.

## Evidence classes and limits

| Evidence | Established | Not established |
|---|---|---|
| Godot import and scripted gameplay checks | 62-bone rig, state continuity, additive recoil, aim/multitouch event routing | animation naturalness, body/weapon collision, competitive aiming latency |
| Real software-rendered screenshot | Linux screenshot of current scene | physical screen presentation or quality level AAA |
| Debug APK exported in GitHub Actions | one ARM64 debug package exists and can be downloaded | APK installed/started successfully on actual hardware |
| SHA-256 generated from resulting APK | repeatable verification of byte integrity | performance, thermal endurance, input timing, or release-signing stability |

## Reusable ARCONT recommendations

- Couple `camera target -> muzzle trajectory -> raycast -> visual reticle` with a scripted regression so weapon impact direction does not drift silently during camera refactors.
- Preserve named bone manifests and import-time assertions before attaching rifles or applying animation modifiers. Source-native clips, additive post-mixer work and full IK are different stages and must be evaluated separately.
- Require `ANIM-002` regressions to assert both proper modifier placement and native state compatibility, then capture rendered frames and profile animation LOD/CPU cost independently.
- Validate Android export as a distinct CI gate (Java, SDK, matching templates, texture compression, debug keystore, checksum), followed by on-device validation (cold/warm p50/p95/p99, thermal state, controller/touch response) before Android support claims.
- The next actionable experiment is **two-bone hand/foot IK with source skeleton mapping**, measured vs additive modifier baseline, not claiming IK coverage from the current implementation.

**Separation rule:** all FISURA game code, APKs and 3D assets live in the dedicated game repository. ARCONT contains only reusable, source-grounded experimental findings. The `production_game_code_allowed=false` and `embedded_godot_project_allowed=false` constraints are unchanged.
