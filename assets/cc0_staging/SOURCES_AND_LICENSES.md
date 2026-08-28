# CC0 Source & License Ledger

All entries below were checked as CC0/public-domain-dedicated at intake time. Preserve this ledger even though attribution is not legally required by CC0; provenance matters for audits and future replacement.

## Library policy
- `assets/cc0_staging/vendor/` remains the permanent general-purpose CC0 warehouse. Existing stylized/low-poly assets are NEVER discarded merely because Arcont changes art direction.
- New human-scale/realistic candidates are organized separately from the existing library.
- Godot must continue ignoring the staging warehouse via `.gdignore`; only curated assets are promoted into runtime.
- Arcont runtime promotion is selective. Other future games may promote different assets from the same warehouse.

## Quaternius — Ultimate Guns Pack
- Category: weapons
- Author: Quaternius
- Source: https://quaternius.com/packs/ultimategun.html
- Mirror used by ingestion: https://opengameart.org/content/low-poly-guns-pack
- License: CC0 1.0
- Arcont use: weapon visual proxies; preserve for future projects even if replaced.

## Quaternius — Universal Animation Library 2
- Category: animations
- Author: Quaternius
- Source: https://quaternius.com/packs/universalanimationlibrary2.html
- Mirror used by ingestion: https://opengameart.org/content/universal-animation-library-2
- License: CC0 1.0
- Declared contents: 130+ humanoid animations including melee, armed combat, parkour and zombie locomotion.
- Arcont use: humanoid retargeting candidates after skeleton/rest-pose validation.

## Quaternius — Universal Base Characters
- Category: human-scale characters
- Author: Quaternius
- Official source: https://quaternius.com/packs/universalbasecharacters.html
- Official distribution: https://quaternius.itch.io/universal-base-characters
- License: CC0 1.0 Universal
- Declared contents: 6 game-ready humanoid bases (male/female; Regular, Superhero, Teen), 20 hairstyles, humanoid rig, FBX/glTF; average ~13k triangles.
- Compatibility: designed for Universal Animation Library; Godot-compatible standard/source distributions.
- Automation limitation: the complete free official pack does not currently expose a stable direct archive URL suitable for unattended ingestion. Best-effort official retrieval remains in the workflow but failure is nonfatal.
- Staged fallback/reference: `human_scale_characters/quaternius_universal_base_candidate_mirror/night-striker-reference.glb` is a **single audited redistributed/modified CC0 reference derived from Universal Base Characters**, sourced from the public `Seyamalam/blood-league-kickoff` repository, with its accompanying `LICENSE-BASE-CHARACTERS.txt` retained beside it.
- Mirror provenance: https://github.com/Seyamalam/blood-league-kickoff
- Important: the staged derivative/reference must never be described as the complete Universal Base Characters pack.
- Arcont use: human-scale player/NPC compatibility test and art-direction comparison until the complete official pack can be staged. ARCONT-CANDIDATE only until metric, skeleton, material and Android tests pass.

## Rikindle3D — Male City Zombie
- Category: realistic/human-scale infected
- Author: Rikindle3D
- Source: https://opengameart.org/content/male-city-zombie-ready-for-use-in-game-engines
- License: CC0
- Declared contents: rigged/textured male city zombie; walking x2, attacks x3, death, idle x2, hit reaction, running and screaming animations.
- Arcont use: realistic infected candidate and animation/reference comparison against current Quaternius infected. Must be measured by Godot before runtime promotion.

## Lucian Pavel — Mobile Ready Zombie
- Category: mobile infected / LOD reference
- Author: Lucian Pavel
- Source: https://opengameart.org/content/mobile-ready-zombie
- License: CC0
- Declared contents: 1,938 triangles, 512 diffuse texture, non-rigged; explicitly optimized for mobile.
- Arcont use: low-cost horde/LOD reference and comparison target for generated ~2k-triangle infected. Not automatically a production character.

## Quaternius — Zombie Apocalypse Kit
- Category: characters/zombies/environment/vehicles
- Author: Quaternius
- Source: https://quaternius.com/packs/zombieapocalypsekit.html
- Public distribution folder: https://drive.google.com/drive/folders/1mWP6sCHun7OUMHQeDNZLrXTteXlzWg_t?usp=sharing
- License: CC0 1.0
- Arcont use: current provisional zombie/enemy and prop candidates; preserve in general library.

## Kenney — City Kit (Roads)
- Category: roads/traffic infrastructure
- Author: Kenney
- Source: https://kenney.nl/assets/city-kit-roads
- Mirror used by ingestion: https://opengameart.org/content/city-kit-roads
- License: CC0 1.0

## Kenney — City Kit (Industrial)
- Category: industrial buildings
- Author: Kenney
- Source: https://kenney.nl/assets/city-kit-industrial
- Mirror used by ingestion: https://opengameart.org/content/city-kit-industrial
- License: CC0 1.0

## Kenney — Factory Kit
- Category: factory/warehouse props
- Author: Kenney
- Source: https://kenney.nl/assets/factory-kit
- Mirror used by ingestion: https://opengameart.org/content/factory-kit
- License: CC0 1.0

## yethiel — Trashcan
- Category: urban clutter
- Author: yethiel
- Source: https://opengameart.org/content/trashcan
- License: CC0 1.0

## loafbrr_1 — Lamp Post Bench TrashCan
- Category: street clutter
- Author: loafbrr_1
- Source: https://opengameart.org/content/lamp-post-bench-trashcan
- License: CC0 1.0

## Paul Wortmann — 3D Dungeon debris: paper
- Category: litter/paper
- Author: Paul Wortmann
- Source: https://opengameart.org/content/3d-dungeon-debris-paper
- License: CC0 1.0

## Poly Haven — realistic environment/PBR source pool
- Category: realistic environment, PBR materials, HDRIs, props
- Author/provider: Poly Haven
- Source: https://polyhaven.com/
- License: assets are CC0.
- Intake policy: do NOT blindly mirror the whole catalog. Maintain a curated manifest of Arcont-relevant candidates and download selected assets only after visual/size review. This avoids turning the Git repository into a multi-gigabyte asset dump.
- Current shortlist: `asphalt_02`, `concrete_floor_damaged_01`, `rubble`, `trashbag`, `metal_trash_can`.
- API note: live API terms are distinct from the asset license; provenance must be retained.
- Arcont use: realistic concrete/asphalt/grime/rubble/industrial/street materials and hero props to raise visual fidelity while keeping existing Kenney geometry available.

## Intake notes
- Source pages rechecked in August 2026.
- OpenGameArt mirrors are preferred for deterministic automated downloads when available.
- No asset is final merely because it is CC0.
- Before promotion inspect logos/text/signage for trademarks or third-party imagery.
- Preserve source archives/provenance in staging; runtime should contain only curated game-ready derivatives.
- Generated/derived inventory belongs in `INGEST_INVENTORY.md`; semantic cross-project classification belongs in `ASSET_CATALOG.md`.