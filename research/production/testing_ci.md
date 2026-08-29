# Production — Testing, CI and Regression Control

## Existing strength
Arcont already validates project import, rig/animation assets, structural contracts, main-scene boot and Android export. Preserve this discipline.

## Test layers
1. Static/structural contracts.
2. Unit-like deterministic logic tests where practical.
3. Scene integration tests.
4. Main boot/smoke.
5. Export/build validation.
6. Performance benchmark/regression.
7. Real-device playtest.
8. Visual/audio subjective review.

## Future candidates
- Ballistics/material deterministic cases.
- Damage/anatomy state-transition tests.
- Weapon Resource schema validation.
- Save migration tests.
- Navigation stress benchmark.
- AI update-budget benchmark.
- Spawn/pool leak tests.
- Repeated scene load/unload memory checks.
- Benchmark scenes with recorded thresholds.
- Screenshot/visual regression for stable deterministic scenes.

## CI philosophy
CI proves reproducibility and catches regressions; it cannot prove touch ergonomics, camera feel, thermal behavior, artistic quality or fun.

## Structural contract synchronization
Status: IMPLEMENTED.

When an intentional architecture or art-pipeline change removes a method, supersedes a status marker, or changes another structural contract, update the corresponding structural/smoke assertion in the same coherent change. A stale assertion is not useful regression protection: it can turn an intentional migration into a false CI failure and prevent later boot/export stages from running.

Arcont evidence (2026-08-29): production commit `20c449b` deliberately removed the old terrain `_add_mounds` path and superseded `ART-PASS-4-HEIGHTMAP` with the PBR terrain contract. Godot CI #423 failed because `tests/smoke_test.gd` still required the obsolete method/status. Production commit `b4b94a6` synchronized those assertions; Godot CI #424 then completed successfully.

Operational rule: before committing an intentional contract deletion/rename, search structural tests for the old symbol/status and migrate the assertion alongside the production change. Keep this separate from weakening tests merely to make CI green: the new assertion must verify the replacement contract.

Re-audit: structural test framework changes, major scene architecture rewrite, or CI pipeline redesign.

## Consolidated-instance regression contracts
Status: IMPLEMENTED / EVOLVING.

When repeated scene nodes are migrated into `MultiMeshInstance3D`, node count is no longer a valid proxy for content density or art coverage. Validate the replacement architecture using explicit metadata and aggregate instance counts: source asset, semantic kind, accepted instance count, metric source extent, target metric range, and whether the real runtime asset or a fallback is active.

Arcont evidence (2026-08-29): the CC0 forest migration consolidated repeated grass, shrubs and trees. CI #425/#428 exposed stale tests that still counted individual forest nodes. The replacement contracts now validate 96 grass + 64 shrub + 96 tree instances (256 total) and require the CC0 tree cells rather than restoring duplicate nodes. CI #429 completed through Android export after those contracts were migrated.

Operational rule: when optimizing representation, preserve the gameplay/art invariant but change the observable used by the test. Never reintroduce expensive duplicate nodes merely to satisfy an assertion written for the old representation.

## Lifecycle leak diagnostic evidence
Status: TESTING.

A Godot shutdown warning is not enough evidence to assign ownership to a gameplay system, imported asset, scene, Resource, or test harness. Diagnostic runs must preserve the complete verbose process output, preserve the original Godot exit code, expose numbered leak/ObjectDB/orphan/RID/resource matches with surrounding context, and retain the complete log as a CI artifact when ownership is still ambiguous.

Arcont evidence (2026-08-29): production commit `b1917bc` added a first verbose `forest_village_art_test.gd` lifecycle diagnostic. Godot CI #437 completed successfully on Godot 4.7.2, proving the warning is non-blocking, but the first diagnostic representation does not provide durable, independently inspectable ownership evidence sufficient to justify a production fix. Therefore no subsystem is considered the confirmed leak owner yet.

Operational rule: never patch a suspected owner merely because its resources appear near engine shutdown output. First make the diagnostic artifact durable and distinguish test-harness lifetime from scene/runtime ownership. Only promote the warning to a failing contract after a reproducible clean-lifecycle expectation exists.

## Current non-blocking CI warnings
Observed on the validated terrain-grounding run #432 and still under lifecycle investigation on #437 (2026-08-29):
- Android export reports that no project icon is configured. The debug APK is still created, signed, verified and uploaded; treat this as release/presentation debt, not a gameplay blocker.
- Some headless tests report one leaked `ObjectDB` instance at exit. CI #437 itself completed successfully; exact ownership remains unconfirmed and must not be guessed.
- Hosted CI has no ADB daemon, so `cannot connect to daemon at tcp:5037` can appear during headless Android tooling. This is not evidence of a device-runtime failure.

Do not silence these warnings blindly. Track whether they persist, identify ownership, and turn them into failing contracts only when the expected clean behavior is defined and reproducible.

## Dependency discipline
Pin important engine/tool versions, record upgrade rationale, and re-audit Reference Lab findings when engine behavior changes.
