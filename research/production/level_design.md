# Production — Level and Encounter Design

## Vertical-slice principle
A procedural test district is useful for systems validation; a commercial slice needs authored combat spaces with intentional sightlines, cover rhythm, traversal choices, pacing and landmarks.

## TPS combat-space questions
- What can the player see before committing?
- Where can ranged enemies create crossfire?
- Are flanks readable and counterable?
- Does cover create choices rather than a single safe lane?
- Can melee/infected pressure dislodge static play?
- Are traversal actions useful but not mandatory gimmicks?
- Does R-3 have meaningful command space?
- Can encounters scale without spawning enemies behind the player unfairly?

## Mobile considerations
- Readability on a small display.
- Avoid visually dense clutter around targets.
- Strong silhouettes and landmarks.
- Controlled sight distance for both performance and cognition.
- Use architecture as occlusion/HLOD opportunity.

## Continuous-relief ownership and grounding
Status: IMPLEMENTED / EVOLVING for the forest-village slice.

A continuous heightmap should have one physical ground owner. Do not leave a full-map flat collider hidden underneath it merely because an older blockout used one; competing ground surfaces create false contact, hovering, buried props and hard-to-diagnose movement behavior.

For Arcont's current forest slice:
- `ForestTerrainRelief` owns macro rendering/collision through the shared height field and `HeightMapShape3D`.
- Decorative roads/tracks sample the terrain during scene construction. They do not need their own gameplay collision when the heightmap already owns walkable ground.
- Long road overlays should follow relief in bounded pieces or a purpose-built sampled mesh rather than one long flat slab.
- Buildings, wells, cover and authored landmarks sample a stable base elevation but remain upright; do not normal-align architecture to local terrain noise.
- Water can remain level when the terrain itself authors the drainage cut.
- Enemy/spawn markers and gameplay collision associated with structures must use the same terrain-height contract as their visuals.

Arcont evidence (2026-08-29): ART-PASS-8 replaced the old flat `ForestGroundCollision`, grounded the village and routes to `ForestTerrainRelief`, and produced 20 terrain-following route groups / 169 sampled segments / 224 grounded nodes. Godot CI #432 passed import, art contract, structural smoke, main boot and Android export.

Performance note: 169 separate route segments are a correctness-first representation, not a final mobile draw-call target. Profile or consolidate them into fewer sampled meshes before declaring the route rendering budget production-ready. Do not blindly optimize without measurements, but keep representation scalable.

## Encounter grammar
Exploration -> warning/contact -> positioning -> pressure -> escalation/role introduction -> release/reward -> transition.
Break this grammar deliberately when surprise serves the experience.

## Metrics worth recording
Time to first contact, encounter duration, deaths/damage, ammo pressure, cover usage, flank frequency, player path, ability/R-3 use, performance worst points.

## Reference-study topics
Gears cover arenas, F.E.A.R. combat spaces, Left 4 Dead pacing/director, Resident Evil encounter staging, immersive-sim systemic spaces, survival-horror resource pressure. Extract principles rather than layouts.
