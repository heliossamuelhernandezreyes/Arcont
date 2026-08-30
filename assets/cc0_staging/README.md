# ARCONT CC0 Staging Library

Branch: `assets/cc0-staging`

Purpose: isolated intake area for freely licensed provisional art. Nothing in this directory is production-approved merely because it is downloaded.

## Structure
- `vendor/weapons/` — firearm candidates.
- `vendor/animations/` — humanoid/zombie animation libraries.
- `vendor/characters_zombies/` — zombie/survivor character candidates.
- `vendor/environment_roads/` — roads, signs, barriers, traffic infrastructure.
- `vendor/environment_industrial/` — warehouses and industrial city modules.
- `vendor/environment_factory/` — factory/interior/industrial props.
- `vendor/props_trashcan/` — dirty urban trash container.
- `vendor/props_street_clutter/` — lamp posts, bench, trash can, cans.
- `vendor/props_paper/` — loose paper/debris pieces.

## Licensing policy
Only packs independently verified as CC0 are admitted to this automated intake. Source pages and authors are recorded in `SOURCES_AND_LICENSES.md`.

CC0 does not remove unrelated trademark/privacy/personality rights. Avoid recognizable real-world brands/logos unless separately audited.

## Intake policy
1. Download on this branch only.
2. Preserve source/author/license record.
3. Prefer GLB/glTF for runtime; fall back to FBX where necessary.
4. Remove duplicate heavy authoring formats when an equivalent runtime interchange format exists.
5. Never assume authoring scale; measure and normalize through Arcont's metric pipeline.
6. Assets begin as `UNREVIEWED-CC0`.
7. Audit topology/materials/rig/animation/performance before promotion to `PROXY` or `ART-PASS-1`.
8. Production branches should receive selected normalized assets, not the whole staging library.

## Status vocabulary
- `UNREVIEWED-CC0`: license/source verified, technical/art suitability unknown.
- `REJECTED`: unsuitable; record why before removal if lesson is useful.
- `PROXY`: safe/useful for gameplay blockout.
- `ART-PASS-1-CANDIDATE`: strong enough to adapt to Arcont's visual language.
- `PROMOTED`: copied intentionally to a production asset path after audit.

## Why a separate branch
Asset discovery creates binary churn and can rapidly bloat production history. This branch acts as quarantine/catalog. Only useful, validated assets should later cross into `fix/mobile-playtest-2` or its successor.