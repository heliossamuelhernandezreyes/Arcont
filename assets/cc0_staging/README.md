# ARCONT Reusable CC0 Staging Library

Branch: `assets/cc0-staging`

Purpose: permanent isolated intake/catalog for freely licensed art that can serve Arcont **or other games**. Nothing in this directory is production-approved merely because it is downloaded.

Godot ignores this warehouse through `.gdignore`. Production branches receive only intentionally selected, normalized runtime derivatives.

## Structure
- `vendor/weapons/` — firearm candidates.
- `vendor/animations/` — humanoid/zombie animation libraries.
- `vendor/characters_zombies/` — existing stylized/provisional zombie assets.
- `vendor/human_scale_characters/` — human-proportion character candidates and audited references.
- `vendor/realistic_infected/` — human/semi-realistic infected candidates.
- `vendor/mobile_infected_reference/` — very low-cost mobile/LOD infected references.
- `vendor/environment_roads/` — roads, signs, barriers and traffic infrastructure.
- `vendor/environment_industrial/` — warehouses and industrial city modules.
- `vendor/environment_factory/` — factory/interior/industrial props.
- `vendor/realistic_environment_manifest/` — approved realistic CC0 source pools/candidates without bulk high-resolution mirroring.
- `vendor/props_trashcan/` — urban trash containers.
- `vendor/props_street_clutter/` — lamp posts, benches, cans and related dressing.
- `vendor/props_paper/` — loose paper/debris pieces.

See `ASSET_CATALOG.md` for cross-project classification and `SOURCES_AND_LICENSES.md` for provenance/license records. `INGEST_INVENTORY.md` is generated automatically from the physical warehouse.

## Non-destructive warehouse policy
A change in Arcont's art direction is **not** a reason to delete a correctly licensed asset. Low-poly/stylized packs remain useful for prototypes and future games. Remove source material only for a licensing/provenance problem, corruption, exact duplication with no archival value, or an explicit repository-storage maintenance decision.

The automated ingest follows the same rule: it is additive/idempotent and must never globally delete `vendor/` before rebuilding it.

## Licensing policy
Only packs independently verified as CC0 are admitted to automated intake. Source pages, authors and provenance are recorded in `SOURCES_AND_LICENSES.md`.

CC0 does not remove unrelated trademark/privacy/personality rights. Avoid recognizable real-world brands/logos unless separately audited.

## Intake and promotion policy
1. Download/source on this staging branch first.
2. Preserve source, author, license and redistribution provenance.
3. Prefer GLB/glTF for runtime; fall back to FBX where necessary.
4. Keep useful source material in the warehouse; optimize/copy only what a production project needs.
5. Never assume authoring scale; measure and normalize through the target game's metric pipeline.
6. Assets begin as warehouse/reference/candidate material, not final art.
7. Audit topology, materials, rig, animation, performance and mobile cost before promotion.
8. Production branches receive selected normalized assets, never the whole staging library.
9. A derivative/reference must be labeled as such and must never be represented as the complete upstream pack.

## Status vocabulary
- `WAREHOUSE`: preserved licensed source asset; project-neutral.
- `ARCONT-CANDIDATE`: potentially suitable for Arcont; awaiting technical/art audit.
- `REFERENCE`: benchmark/LOD/research material; not necessarily intended for direct runtime use.
- `SOURCE-POOL`: approved CC0 provider/catalog curated on demand.
- `PROXY`: technically safe/useful for gameplay blockout.
- `ART-PASS-1-CANDIDATE`: strong enough to adapt to Arcont's visual language.
- `PROMOTED`: intentionally copied into a runtime path after audit.
- `REJECTED`: unsuitable for a given production use; record why, but do not automatically delete the reusable source.

## Why a separate branch
Asset discovery creates binary churn and can rapidly bloat production history. This branch is the reusable quarantine/catalog. Arcont currently promotes selected files to `assets/provisional/cc0_runtime/`; future games can select completely different subsets without rebuilding the library from zero.