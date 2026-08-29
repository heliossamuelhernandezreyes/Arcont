# Knowledge Gaps and Watchlist

This file is a living queue, not a statement that a topic is unimportant.

## Priority A — directly affects current vertical slice
- Real-device Android profiling: CPU/GPU/frame pacing/RAM/thermal/battery.
- TPS camera feel, collision, shoulder swap and ADS transitions.
- Touch ergonomics, gyro, aim assistance and configurable HUD.
- Locomotion blending, upper/lower-body layers, aim offsets and action transitions.
- Gunfeel: recoil, impacts, hit reactions, sound layering and latency.
- Navigation/path query budgeting for crowds and tactical AI.
- Mobile urban visibility, occlusion, LOD/HLOD and shadow budgets.
- Audio architecture and spatial gunshot/impact/footstep system.
- Data-driven weapons/enemies/materials/encounters using Resources.
- Forest prop acquisition: find/license/validate a true fallen-trunk or deadwood asset and a small ground-stone family suitable for repeated scatter. Current promoted candidates `campfire_logs.fbx` and `cliff_blockCave_rock.fbx` are semantically/scale-inappropriate for those roles; do not substitute them merely to eliminate procedural placeholders.
  - Candidate A, preferred for audit: Kenney Nature Kit (`https://kenney.nl/assets/nature-kit`). Official Kenney page currently lists 330 3D files under CC0. Cross-project provenance records identify Nature Kit 2.1, source archive `kenney_nature-kit.zip`, SHA-256 `fa7974a0d342bfe63c38664ba9f8ec1a4aab8ea25f099bdc56870e33588c4d9d`, and GLB members including `log.glb`, `rock_smallA.glb`, `rock_smallB.glb`, `rock_smallC.glb`, `rock_largeA.glb`, `rock_largeB.glb` and `stone_tallA.glb`. Treat those inventory/hash records as corroboration, not a substitute for inspecting Arcont's own downloaded archive. Before integration, verify the downloaded ZIP hash and included `License.txt`, then measure/normalize only the selected models and record exact promoted paths.
  - Candidate B, secondary: Fertile Soil Productions Nature Props (`https://fertile-soil-productions.itch.io/nature-props`), creator page states CC0 and lists 14 logs/branches/roots plus 13 rocks/stepping stones. Audit visual fit, download provenance and exact model filenames before use.
  - Status: CONCRETE CANDIDATE FILES IDENTIFIED, NOT YET PROMOTED. Existing procedural small stones/fallen logs remain safer than semantically wrong substitutions until the source archive itself passes the asset pipeline.
- Android presentation debt: configure an Arcont project/app icon before release-facing builds. Current debug export succeeds without it, but Godot emits an explicit missing-icon warning.
- Headless test cleanup: investigate the recurring single `ObjectDB` leak warning before declaring repeated scene load/unload behavior production-clean.

## Priority B — near-term production
- Root motion policy for vaults, mantles, melee and executions.
- IK: weapon hands, feet, cover contact and look/aim constraints.
- Anatomical damage + visual dismemberment pipeline.
- Tactical AI memory, uncertainty, squad communication and suppression.
- Companion command UX and R-3 autonomy boundaries.
- Encounter pacing and director architecture.
- Destructible cover cost model.
- Asset budgets per character, weapon, prop and environment module.
- Shader/material mobile budget.
- Save/versioning architecture.
- Accessibility and remapping.

## Priority C — future-facing / adjacent
- Procedural animation and motion matching.
- GPU-driven crowds / MultiMesh tradeoffs.
- Large-world streaming and chunked navigation.
- Deterministic simulation and replay systems.
- Networking/rollback/authority models even if Arcont remains single-player.
- Modding/data-pack architecture.
- Localization pipeline.
- Automated visual regression.
- Build reproducibility and dependency pinning.
- Console/desktop portability.
- Haptics and adaptive controller feedback.
- HDR/display calibration.
- Photo mode/camera tooling.
- Telemetry/privacy-aware playtest analytics.
- User-generated accessibility presets.

## Long-horizon research
- ECS/data-oriented design: when it helps and when it adds needless complexity in Godot.
- GOAP, utility AI, behavior trees, hierarchical state machines and hybrid AI.
- Reinforcement learning as offline design/testing tooling, not runtime magic.
- Destruction/fracture, soft bodies and procedural wounds.
- Acoustic propagation and geometry-aware sound.
- Learned animation, neural upscaling and future mobile GPU techniques.
- Procedural generation with authored constraints.
- Game economy and progression psychology.
- Narrative systems, systemic storytelling and companion bonding.
- Cognitive load/readability under dense combat.
- Color science, contrast and accessibility in dark environments.
- Anti-cheat/security only if online features ever justify it.
