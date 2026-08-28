# Mobile Visual Budgets

## Principle
Budgets are targets to measure and tune, not universal commandments. Record device/build/scene/settings with every measurement.

## Budget dimensions
- Visible characters and skinned meshes.
- Draw calls/material switches.
- Visible triangles and sub-pixel geometry concentration.
- Shadowed lights and overlapping light volumes.
- Transparency/overdraw.
- Particle count and lifetime.
- Decals per mesh/scene.
- Texture memory/resolution.
- Shader complexity/samplers.
- Animation update frequency.
- LOD/visibility distance.

## Arcont quality tiers
### Player / hero
Highest animation/material detail; close-range silhouette must hold.

### Near combat enemy
Full gameplay animation, readable material/damage state, reduced unnecessary microdetail.

### Mid/distant enemy
LOD mesh/material, reduced animation update cadence, cheaper VFX.

### Hero environment
Landmarks and encounter-critical geometry get detail.

### Repeated/background environment
Aggressive material reuse, LOD/HLOD, visibility ranges and instancing.

## Mobile renderer constraints to remember
- Tile-based GPUs are sensitive to fill/overdraw and concentrated tiny geometry.
- Skinning and morphs increase vertex work.
- Transparency stacks are expensive.
- Forward Mobile is designed for mobile and uses limited per-mesh local lights.
- Decals are finite; Mobile allows only a limited number per mesh.
- Large source textures should be constrained on import; mobile hardware commonly caps maximum texture dimensions at 4096.

## Required benchmark scenes
1. Player + 1 enemy close combat.
2. 12+ infected crowd.
3. Tactical firefight with cover and VFX.
4. Urban vista with vehicles/props.
5. Worst-case gore/explosion overlap.
6. Xeno ability stress.
7. Mixed vertical-slice worst case.

## Metrics
Frame CPU/GPU, 1% lows/frame pacing, draw calls, primitives, objects, memory, thermal trend and battery. Do not declare an art budget validated from average FPS alone.

## Current status
Framework established; numeric production ceilings remain TESTING until representative Android profiling exists.
