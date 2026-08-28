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

## Dependency discipline
Pin important engine/tool versions, record upgrade rationale, and re-audit Reference Lab findings when engine behavior changes.
