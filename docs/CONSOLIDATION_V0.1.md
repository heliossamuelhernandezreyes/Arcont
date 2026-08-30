# Arcont v0.1 — Consolidation Manifest

Status: INTEGRATION / NOT YET CANONICAL
Branch: `integration/arcont-v0.1`

## Purpose

This branch is the single candidate line for consolidating the current playable game before anything is promoted to `main`.

It was created from `feat/cc0-provisional-art-pass` because that branch already contains the complete history of `fix/mobile-playtest-2`, which itself contains `fix/mobile-camera-foundation`. This preserves the current TPS/mobile/gameplay work without replaying or duplicating those branches.

No legacy branch is to be deleted until its unique commits and assets are explicitly classified.

## Branch disposition

- `main`: stable historical base. Do not add new feature work directly during consolidation.
- `integration/arcont-v0.1`: canonical integration candidate. All consolidation fixes land here first.
- `feat/cc0-provisional-art-pass`: source snapshot for the current playable/art build. Treat as frozen input once integration advances.
- `fix/mobile-playtest-2`: already contained by the art-pass ancestry; retain temporarily for traceability.
- `fix/mobile-camera-foundation`: already contained by mobile-playtest-2/art-pass; PR #1 is superseded by this integration line.
- `research/reference-lab`: evidence/reference source. Import documentation selectively; do not merge its divergent runtime files wholesale.
- `assets/cc0-staging`: source-ingest/staging archive. Do not merge wholesale into runtime. Promote only audited, licensed, semantically appropriate assets.

## Consolidation invariants

1. Never trade a known working gameplay system for visual cleanup without a regression test.
2. Structural CI means `STRUCTURALLY_VALIDATED`, not `VISUALLY_ACCEPTED`.
3. Android/device evidence is required for acceptance-critical rendering, animation, controls and performance.
4. Keep gameplay logic independent from provisional render meshes and art assets.
5. Preserve asset provenance and licenses for every promoted external asset.
6. Do not add another corrective world/art pass unless ownership cannot be expressed in an existing stable subsystem.
7. Accepted temporary art passes must graduate into clear data/system ownership or be removed.
8. Do not call a build `Final`, `Polished` or equivalent while visual/device acceptance is pending.

## P0 acceptance gates before merge to main

### TPS rendered contract
- Player body is visibly present in hip-fire third-person composition.
- ADS has a visibly distinct and correct framing.
- SpringArm collision does not make the operator disappear in representative walls/doors/open-terrain cases.
- Locomotion is visibly animated on Android; node existence alone is not sufficient.

### Infected animation contract
- Intact infected never remain in bind/T-pose during idle, chase or attack.
- Runtime state chooses a semantically correct clip, not an arbitrary first animation fallback.
- Skeleton/track compatibility is proven by visible deformation in representative captures/device play.

### World visual contract
- Forest uses real audited vegetation archetypes while retaining MultiMesh/spatial batching where useful.
- Shared semantic occupancy/exclusion rules keep vegetation out of building footprints, doors, primary routes, mission objects and camera-critical spaces.
- Houses read as constructed/abandoned architecture rather than greybox blocks.
- Road/ground transitions do not present obvious procedural plates or patch boundaries.
- Dusk lighting preserves enemy/navigation readability on Android.

### Performance/device contract
- Benchmark scenes are repeatable and identified by build/settings/device.
- Record frame pacing and 1% lows, not only instantaneous FPS.
- Record CPU/GPU frame behavior, memory and thermal trend where device tooling allows it.
- Include at minimum: close enemy, 12+ infected, firefight/VFX, village vista, gore/explosion overlap and mixed worst case.

## Test/CI policy

The integration line should retain the stronger art-pass CI suite: project import/parse, character generator, rig/animation, TPS screen-space diagnostic, metric scale, runtime candidate audit, weapon contract, infected animation/visual diagnostics, forest art contract, performance telemetry, lifecycle diagnostics, smoke test, representative captures and Android APK export.

Tests must assert semantic output where possible. Proxies such as `node exists`, `animation list is non-empty`, `density is high`, or `surface follows heightmap` cannot by themselves close a player-facing acceptance gate.

## Asset policy

`assets/cc0-staging` remains an ingest source, not runtime truth. Promotion requires:

- verified source and license;
- exact selected model/texture paths;
- scale/orientation audit;
- semantic role fit;
- mobile visual/performance trial;
- runtime destination documented.

Do not copy entire vendor packs into runtime merely because they are CC0.

## Immediate work order

1. Establish this integration branch and make it the only candidate for `main`.
2. Preserve and selectively import Reference Lab documentation without its divergent runtime changes.
3. Classify the 14 staging-only commits/assets; promote only missing value.
4. Fix TPS rendered visibility and add a semantic regression gate.
5. Fix infected animation/T-pose and add a semantic regression gate.
6. Consolidate additive art-pass ownership and introduce shared occupancy masks.
7. Replace primitive forest archetypes while retaining the batching architecture.
8. Rebalance architecture/surfaces/lighting against Android captures.
9. Run the repeatable Android benchmark suite.
10. Merge to `main` only after P0 gates are satisfied.

## Promotion rule

`integration/arcont-v0.1` becomes `main` only through its consolidation pull request after all P0 items above have evidence. Until then, `main` remains unchanged and the integration PR remains draft.
