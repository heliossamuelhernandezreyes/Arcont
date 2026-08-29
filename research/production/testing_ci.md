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

## Dependency discipline
Pin important engine/tool versions, record upgrade rationale, and re-audit Reference Lab findings when engine behavior changes.
