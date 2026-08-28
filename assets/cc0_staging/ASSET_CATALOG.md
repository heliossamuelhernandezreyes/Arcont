# Reusable CC0 Asset Catalog

This catalog sits above `vendor/` and classifies the permanent warehouse without forcing assets into any one game. The staging directory remains ignored by Godot; production projects copy only audited runtime derivatives.

## Status vocabulary
- **WAREHOUSE** — preserved, licensed source asset; not automatically used by Arcont.
- **ARCONT-CANDIDATE** — visually/technically relevant to Arcont and awaiting metric/rig/mobile audit.
- **PROMOTED** — selected derivative already copied into an Arcont runtime path.
- **REFERENCE** — useful benchmark, LOD target or research asset; not necessarily suitable for direct runtime use.
- **SOURCE-POOL** — approved provider/catalog from which assets are curated on demand.

| ID | Category | Provider / pack | License | Rig / animation | Warehouse status | Arcont role |
|---|---|---|---|---|---|---|
| quaternius-ultimate-guns | weapons | Quaternius Ultimate Guns | CC0 | n/a | WAREHOUSE + PROMOTED subset | current provisional firearms; reusable |
| quaternius-ual2 | animations | Universal Animation Library 2 | CC0 | humanoid animations | WAREHOUSE | retargeting/animation library |
| quaternius-zombie-apocalypse | characters/infected | Zombie Apocalypse Kit | CC0 | animated character assets | WAREHOUSE + PROMOTED subset | current provisional infected; reusable |
| quaternius-ubc-reference | characters/humans | Universal Base Characters reference | CC0 | humanoid | ARCONT-CANDIDATE | human-scale player/NPC compatibility test |
| rikindle-city-zombie | characters/infected | Male City Zombie | CC0 | rigged + multiple clips | ARCONT-CANDIDATE | realistic infected comparison/replacement candidate |
| lucian-mobile-zombie | characters/infected | Mobile Ready Zombie | CC0 | non-rigged | REFERENCE | 1,938-triangle mobile/LOD benchmark |
| kenney-city-roads | environment | Kenney City Kit Roads | CC0 | n/a | WAREHOUSE + PROMOTED subset | roads/infrastructure, especially prototypes/future games |
| kenney-city-industrial | environment | Kenney City Kit Industrial | CC0 | n/a | WAREHOUSE + PROMOTED subset | industrial blockout/secondary scenes |
| kenney-factory | environment/props | Kenney Factory Kit | CC0 | n/a | WAREHOUSE + PROMOTED subset | factory and urban props |
| yethiel-trashcan | props | Trashcan | CC0 | n/a | WAREHOUSE | urban clutter |
| loafbrr-street-clutter | props | Lamp Post Bench TrashCan | CC0 | n/a | WAREHOUSE + PROMOTED subset | street dressing |
| wortmann-paper | props | 3D Dungeon Debris: Paper | CC0 | n/a | WAREHOUSE | litter/debris |
| polyhaven-realistic | PBR/environment | Poly Haven | CC0 assets | n/a | SOURCE-POOL | human/semi-realistic Arcont materials and hero props |

## Current human/semi-realistic shortlist

For Arcont's newer human-scale art direction, prioritize technical evaluation in this order:
1. `rikindle-city-zombie`: inspect geometry, skeleton, animation names, materials and Android cost.
2. `quaternius-ubc-reference`: test human proportions, retargeting and player-camera readability. This staging item is a single audited derivative/reference, not the complete official pack.
3. `lucian-mobile-zombie`: use as a low-poly baseline against generated ~2k infected and future LODs.
4. Poly Haven candidate IDs `asphalt_02`, `concrete_floor_damaged_01`, `rubble`, `trashbag`, `metal_trash_can`: ingest only game-sized derivatives when a scene actually needs them.

## Non-destructive warehouse rule

Changing Arcont's visual direction is never a reason to delete a correctly licensed asset from this branch. Stylized and low-poly packs remain valuable for prototypes and other games. A source file is removed only for a licensing/provenance problem, corruption, exact duplication with no archival value, or explicit repository-storage maintenance decision.