# ARCONT Reference Lab

This branch is Arcont's isolated, persistent research/audit workspace and technical memory. Nothing here is a production dependency unless separately reviewed, tested and intentionally integrated.

## Start here
- [AUDIT_PROTOCOL.md](AUDIT_PROTOCOL.md) — how the lab is maintained and consulted.
- [DECISIONS.md](DECISIONS.md) — implemented, candidate, rejected and superseded technical decisions.
- [KNOWLEDGE_GAPS.md](KNOWLEDGE_GAPS.md) — living gaps/watchlist.

## Godot engineering
- [godot/camera_tps.md](godot/camera_tps.md)
- [godot/input_mobile.md](godot/input_mobile.md)
- [godot/animation.md](godot/animation.md)
- [godot/navigation.md](godot/navigation.md)
- [godot/rendering_mobile.md](godot/rendering_mobile.md)
- [godot/performance.md](godot/performance.md)
- [godot/resources_architecture.md](godot/resources_architecture.md)
- [godot/audio.md](godot/audio.md)

## Visual art and production quality
Start with [art/ART_BIBLE.md](art/ART_BIBLE.md) and use [art/ART_AUDIT_CHECKLIST.md](art/ART_AUDIT_CHECKLIST.md) for reviews.
- [art/ART_BIBLE.md](art/ART_BIBLE.md) — visual pillars, hierarchy and quality states.
- [art/CHARACTERS.md](art/CHARACTERS.md) — silhouette, topology, rigging, materials, anatomy and LOD.
- [art/ENVIRONMENT_ART.md](art/ENVIRONMENT_ART.md) — modular urban art, composition, tactical readability and destruction.
- [art/MATERIALS_PBR.md](art/MATERIALS_PBR.md) — PBR authoring and mobile material policy.
- [art/LIGHTING.md](art/LIGHTING.md) — lighting hierarchy, mobile constraints, tonemapping and calibration.
- [art/VFX.md](art/VFX.md) — weapon, gore and gameplay VFX with mobile limits.
- [art/ANIMATION_QUALITY.md](art/ANIMATION_QUALITY.md) — locomotion, combat, traversal and retargeting quality.
- [art/MOBILE_VISUAL_BUDGETS.md](art/MOBILE_VISUAL_BUDGETS.md) — visual budget framework and benchmark scenes.
- [art/AI_ASSET_PIPELINE.md](art/AI_ASSET_PIPELINE.md) — generative 3D to production asset pipeline.
- [art/ART_AUDIT_CHECKLIST.md](art/ART_AUDIT_CHECKLIST.md) — reusable visual/technical review gate.
- [art/CURRENT_BUILD_ART_AUDIT.md](art/CURRENT_BUILD_ART_AUDIT.md) — audited disposition and production order for the current mobile-playtest-2 visuals.
- [art/OFFICIAL_SOURCES.md](art/OFFICIAL_SOURCES.md) — primary Godot documentation catalog.

## Gameplay
- [gameplay/game_feel.md](gameplay/game_feel.md)
- [gameplay/damage_anatomy_gore.md](gameplay/damage_anatomy_gore.md)

## AI
- [ai/architecture.md](ai/architecture.md)

## Production
- [production/asset_pipeline.md](production/asset_pipeline.md)
- [production/testing_ci.md](production/testing_ci.md)
- [production/level_design.md](production/level_design.md)

## References and adjacent knowledge
- [references/repos.md](references/repos.md) — repository catalog.
- [references/beyond_games.md](references/beyond_games.md) — human factors, perception, robotics, mathematics, film, urbanism and other cross-disciplinary knowledge.
- [references/research_backlog.md](references/research_backlog.md) — deliberately broad future research queue.

## Core rules
- Preserve source URL, license and purpose for external references.
- Prefer official documentation and permissive sources.
- Unknown license means reference-only until audited.
- Do not merge this branch wholesale into production.
- Audit patterns and architecture before copying code.
- Production remains mobile-first and Godot 4.7 compatible until deliberately changed.
- Preserve failed/rejected approaches and why they failed.
- Real-device evidence outranks assumptions.
- Store useful adjacent knowledge even when it does not solve today's task.

## Current reference seeds
### TPS / locomotion
- https://github.com/gdquest-demos/godot-4-3d-third-person-controller
- https://github.com/selgesel/godot4-third-person-controller
- https://github.com/Jeh3no/Godot-Third-Person-Controller
- https://github.com/fdemir/real-controller
- https://github.com/etherealxx/Godot-Third-Person-Controller-Mobile
- https://github.com/catprisbrey/Third-Person-Controller--SoulsLIke-Godot4

### Tactical shooter / AI
- https://github.com/AetherRadar/operation-steel-tide

### Official Godot seeds
- https://docs.godotengine.org/en/4.7/tutorials/3d/spring_arm.html
- https://docs.godotengine.org/en/stable/classes/class_boneattachment3d.html
- https://docs.godotengine.org/en/stable/tutorials/animation/animation_tree.html
- https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html

## Important findings already reflected in Arcont
- SpringArm3D should own TPS camera collision.
- Mobile touch needs explicit finger ownership and separation from emulated mouse input.
- Equipment should follow the rig/world-space mount rather than a camera-attached FPS hierarchy.
- AnimationTree/state-machine blending becomes preferable as locomotion/action complexity grows.
- Urban mobile levels need explicit visibility/LOD/occlusion strategy.
- AI navigation, perception and decision work should be budgeted rather than uniformly updated every frame.
- Anatomical damage is more valuable when it changes gameplay capability rather than acting as cosmetic gore alone.
- Visual quality must be evaluated through metric scale, silhouette, material response, lighting and mobile performance rather than asset-source prestige or raw polygon count.

## Maintenance contract
For normal Arcont work, consult the relevant topic files first. Perform focused external research only when the lab is missing or has stale evidence, then add the useful result here. Full research sweeps are reserved for major engine/platform changes and explicit audits.
