# Arcont — Map Creation & Mobile World Guide

Status: CANDIDATE / reference-lab
Date: 2026-08-28

## Goal
Build visually rich tactical maps on Android without paying for richness with uncontrolled draw calls, overdraw, shadows, physics, or AI cost.

## Level-design workflow
1. Mission and combat beats first: objective, approach, escalation, defense, exit.
2. Greybox with metric modules and navigation before decoration.
3. Establish primary/secondary routes, flanks, cover rhythm, sightline lengths, enemy approach lanes and safe breathing spaces.
4. Establish landmarks and a visual hierarchy so the player can orient without minimap dependence.
5. Art pass by layers: macro silhouette -> architecture/terrain -> gameplay props -> story clutter -> decals/damage -> VFX -> lighting/atmosphere.
6. Optimize by measured bottleneck, then Android validation.

## Godot implementation patterns
- GridMap/MeshLibrary: useful for repeated metric architectural modules. MeshLibrary items can include collision and navigation. Do not force irregular hero composition into a grid.
- MultiMeshInstance3D: preferred for large counts of repeated nearby static meshes: grass, repeated stones, leaf clusters, debris families, fence posts. Keep spatial groups/chunks because a MultiMesh is culled as a unit.
- Automatic instancing cannot be assumed on the Mobile renderer; explicitly use MultiMesh where repeated-object draw calls matter.
- Automatic mesh LOD + Visibility Range/HLOD can coexist.
- HLOD: close = individual meshes; medium = reduced/grouped meshes; far = grouped proxy or billboard/Sprite3D impostor; irrelevant micro-detail disappears.
- Occlusion: use large opaque occluders/architecture intelligently. Do not expect tiny props to solve visibility cost.
- NavigationRegion3D/NavMesh: navigation is its own representation; visuals and physics are not automatically pathfinding constraints. Bake/design nav data deliberately for agent dimensions.
- Static/baked lighting should carry most environment lighting on mobile. Reserve realtime shadowed lights for high-value dynamic events.

## Mobile visual budget principles
- Minimize materials and draw calls before obsessing over raw polygon count.
- Avoid alpha-blended vegetation layers where alpha-scissor/opaque geometry can work; overdraw is dangerous on tile-based mobile GPUs.
- Do not spend dense geometry on tiny distant screen-space objects.
- Limit shadow casters by importance and distance.
- Prefer 1K/2K atlases and shared materials for common environment families; reserve larger textures for rare hero assets only after device measurement.
- Micro-clutter should have aggressive visibility ranges.

## Fire, smoke and atmospheric cheats
Fire does not need volumetric simulation. Mobile default:
- one or a few crossed/billboard flame sprites or flipbook/atlas frames;
- additive/emissive or alpha-scissor material where visually acceptable;
- a small GPUParticles3D emitter for sparks/embers;
- separate cheap smoke particles;
- optional short-range unshadowed OmniLight3D for important nearby fires only;
- distant fire becomes Sprite3D/AnimatedSprite3D and eventually disappears.

Smoke:
- use a small library of soft CC0 smoke sprites, randomized scale/rotation/lifetime;
- keep particle count low and particles large rather than hundreds of tiny transparent particles;
- distance-cull emitters.

Clouds/sky:
- cheapest: PanoramaSkyMaterial/HDRI or procedural sky, no actual cloud geometry;
- dynamic option: one/few large scrolling cloud layers or low-cost sky shader;
- distant horizon cloud cards can add depth;
- avoid expensive volumetric cloud simulation for the Android baseline.

Fog:
- depth/height fog is useful for atmosphere and hiding distant LOD transitions;
- use it as art direction, not as a bandage for bad geometry/layout.

## Art direction for Arcont maps
Every area needs: one dominant landmark, one secondary landmark, a controlled palette/material family, a readable route hierarchy, and environmental storytelling.

Composition scale:
- Macro: skyline, terrain silhouette, street/forest massing, landmark.
- Meso: buildings, clearings, checkpoints, wrecks, cover clusters.
- Micro: trash, paper, shell casings, blood, broken glass, vegetation scatter.

Do not distribute detail uniformly. Create dense story pockets separated by calmer visual areas. Combat spaces must remain readable.

Urban: strong hard silhouettes, concrete/asphalt/metal hierarchy, controlled emergency accents, blocked routes that explain themselves.
Forest: canopy/vertical trunks create rhythm; clearings create arenas; rocks/logs shape cover; vegetation density must not destroy enemy silhouette readability.
Hybrid: use material and vegetation transition zones rather than an abrupt city-to-forest seam.

## Asset gaps worth filling
Priority reusable CC0 library candidates:
- flame flipbooks / fire sprites;
- smoke, dust, sparks, embers;
- sky HDRIs / pure skies / cloud layers;
- decals: cracks, grime, leaks, blood, bullet marks, signage;
- forest ground: leaves, twigs, branches, mushrooms, roots, dead trees;
- rocks/cliffs/boulders with mobile LODs;
- industrial cables/pipes/fences/barriers;
- destroyed architecture modules and rubble;
- water/puddle materials and simple water planes;
- distant skyline/mountain/tree impostors;
- ambient audio loops and one-shots in a separate audio pass.

## Current researched CC0 candidates
- Kenney Particle Pack — CC0, 80 particle/light/shader sprites; useful for fire, sparks, smoke and generic VFX.
- Kenney Smoke Particles — CC0, ~70 smoke/explosion sprites.
- OpenGameArt Fire Smoke Animations (Reactorcore) — CC0 PNG sheets/individual frames; evaluate style fit before promotion.
- OpenGameArt Smoke Vapor Particles — CC0 soft smoke textures.
- Poly Haven Cloud Layers HDRI — CC0, sky/lighting source; use mobile-resolution derivative in runtime, keep master in staging/reference.
- Poly Haven Wasteland Clouds Pure Sky — CC0, useful for apocalyptic/late-day atmosphere; use reduced runtime copy.

## Required future tooling
- Environment scatter tool: deterministic seed, density masks, slope/road exclusion, clustering, random scale/yaw, MultiMesh output.
- Map validator: missing collision/nav, excessive material counts, shadow-caster counts, micro-props without visibility range, oversized textures, dense transparent overlap.
- LOD/HLOD policy component and distance bands.
- VFX prefab library with mobile/high tiers.
- Performance capture scenarios: empty map, exploration, 10/20/30 enemies, VFX stress, worst sightline.

## Source notes
Primary implementation references researched: official Godot 4 documentation for GridMap, Navigation, Visibility Ranges/HLOD, 3D/GPU optimization and Environment/Fog. Asset candidates use CC0 sources from Kenney, OpenGameArt and Poly Haven. Re-check source/license at ingest time and record it in SOURCES_AND_LICENSES.
