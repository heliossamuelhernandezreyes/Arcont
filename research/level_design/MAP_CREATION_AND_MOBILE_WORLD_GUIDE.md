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

## Spatial chunking policy
Never make one world-sized MultiMesh. MultiMesh instances share culling and LOD behavior, so split repeated scenery into spatial cells.

Candidate baseline for testing:
- dense urban clutter: 16–24 m cells;
- grass/leaf/stone scatter: 24–40 m cells;
- trees: 32–64 m cells depending on canopy and sightlines;
- distant impostors: larger HLOD cells.

Each cell owns its repeated visual instances and can be hidden/cull-ranged as a unit. Keep collision/gameplay objects separate from decorative MultiMesh instances. A decorative rock may be instanced visually while only selected cover rocks receive authored collision.

## LOD / HLOD ladder
Use screen importance, not a universal distance. Initial policy to benchmark:
- Hero/interactive: full mesh and gameplay representation.
- Near: LOD0, important normals, selected shadows.
- Mid: automatic/manual LOD, cheaper material, shadow disabled on low-value props.
- Far: HLOD group or Sprite3D/impostor.
- Very far: skyline/horizon card, sky/HDRI, or nothing.

Godot visibility ranges work on MeshInstance3D, MultiMeshInstance3D, particles and Sprite3D, so a tree can explicitly transition from 3D geometry to an impostor. Prefer dither/alpha-scissor style transitions over large alpha-blended fades when possible on mobile.

Important MultiMesh caveat: automatic mesh LOD is evaluated for the MultiMesh node as a whole. Widely separated instances should therefore live in separate spatial MultiMeshes; otherwise a near instance can keep a distant group at an unnecessarily expensive LOD.

## Occlusion as level design
Occlusion is not only an engine setting. Design maps so geometry naturally limits expensive sightlines.

Urban tools:
- corners and street bends;
- buses/trucks/wrecks as visual blockers;
- building masses;
- tunnels, alleys, courtyards and gates;
- interior room segmentation.

Forest tools:
- terrain ridges;
- dense tree masses outside combat lanes;
- rock walls;
- fog and canopy silhouette;
- curved trails rather than unlimited straight sightlines.

Occlusion culling has CPU cost. Use it where meaningful blockers exist. Open terrain with little obstruction should lean harder on mesh LOD, HLOD and visibility ranges. Mobile renderer can benefit strongly from good occlusion because it does not rely on the same depth-prepass behavior as Forward+.

## Mobile visual budget principles
- Minimize materials and draw calls before obsessing over raw polygon count.
- Avoid alpha-blended vegetation layers where alpha-scissor/opaque geometry can work; overdraw is dangerous on tile-based mobile GPUs.
- Do not spend dense geometry on tiny distant screen-space objects.
- Limit shadow casters by importance and distance.
- Prefer 1K/2K atlases and shared materials for common environment families; reserve larger textures for rare hero assets only after device measurement.
- Micro-clutter should have aggressive visibility ranges.
- Atlas decals/VFX where practical to reduce material churn.
- Reuse material families: concrete, painted metal, rusted metal, asphalt, soil, bark, foliage, glass, blood/grime overlays.

## Fire architecture
Fire is a layered illusion, not a fluid simulation.

Near hero fire:
1. low-poly source mesh or crossed quads;
2. animated flipbook flame atlas;
3. emissive material;
4. small sparks/embers GPUParticles3D;
5. low-count large smoke sprites;
6. optional short-range unshadowed light with subtle flicker;
7. optional heat distortion only on high tier after measurement.

Medium fire:
- fewer/larger flame cards;
- smoke count reduced;
- no dynamic light unless it materially affects composition.

Far fire:
- AnimatedSprite3D/impostor or emissive card;
- no particle simulation;
- no light.

Use visibility ranges on VFX. GPUParticles3D is a GeometryInstance3D and can be distance culled. Set/generate a sensible visibility AABB so effects do not disappear incorrectly and do not use giant always-visible bounds.

## Smoke, dust and weather
Smoke:
- prefer a handful of large soft sprites over hundreds of tiny transparent particles;
- randomize rotation, scale, lifetime and atlas frame;
- fade/dissolve softly but control overdraw;
- disable distant emitters.

Dust:
- localized impact puffs;
- low ground haze cards in selected areas;
- tiny particle counts for windblown debris.

Rain candidate:
- camera/local-volume rain rather than particles across the entire map;
- cheap splash decals/particles near player only;
- wetness via material parameter rather than unique wet meshes.

Wind candidate:
- shader-driven vegetation sway shared by foliage materials;
- occasional leaf particles near player;
- do not animate every tree through scripts.

## Sky, clouds and horizon
Baseline Android sky stack:
- WorldEnvironment + ProceduralSky or reduced HDRI/pure-sky panorama;
- one DirectionalLight3D as primary sun/moon;
- fog for depth separation;
- optional scrolling cloud layer/card;
- distant mountain/tree/city silhouettes as horizon impostors.

Do not model distant cloud volumes by default. A sky panorama or shader provides effectively infinite visual distance at negligible geometry cost. Dynamic weather can blend sky/material parameters rather than swapping a complete world.

Poly Haven CC0 HDRIs are useful masters, but runtime derivatives should be deliberately reduced. Keep source-quality masters in staging/reference and export only the resolution actually justified by Android testing.

## Terrain and forest composition
Forest should not be random noise. Build in ecological/compositional layers:
- canopy anchors: large trees;
- secondary trunks/saplings;
- shrubs;
- ground cover;
- rocks/logs/stumps;
- micro scatter: leaves, twigs, mushrooms, debris.

Use density zones. Keep combat lanes and enemy silhouettes readable. Cluster vegetation naturally instead of uniform random distribution. Clearings are gameplay rooms; trails are corridors; ridges/rock formations are walls; landmark trees/structures are navigation anchors.

Scatter masks should support:
- include/exclude polygons/volumes;
- road/path exclusion;
- slope limit;
- minimum spacing;
- density and cluster noise;
- random yaw;
- bounded scale variation;
- deterministic seed;
- asset weighted sets;
- distance/LOD class;
- collision/nav exclusion metadata.

## Urban composition
Use modular kits for repetition but deliberately break repetition with hero corners and story pockets.

Street recipe:
- macro building masses first;
- sidewalk/road/curb rhythm;
- major blockers and cover;
- landmark/signage;
- utility layer: poles, cables, fences, pipes;
- damage layer: rubble, broken barriers, cracks;
- story layer: vehicles, luggage, barricades, trash;
- micro layer: paper, casings, blood, glass;
- atmosphere/VFX last.

Never distribute every prop evenly. Empty negative space makes dense areas look richer and improves combat readability.

## Decal strategy
Reusable atlas categories:
- bullet holes by surface family;
- blood splashes/pools;
- cracks;
- leaks/grime;
- tire/skid marks;
- warning paint/signage;
- scorch marks;
- dampness/puddles.

Decals need distance fading and a population budget. Persistent combat decals should use pooling/ring-buffer cleanup instead of growing forever.

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
- Kenney Particle Pack — CC0, particle/light/shader sprites; useful for fire, sparks, smoke and generic VFX.
- Kenney Smoke Particles — CC0 smoke/explosion sprite source.
- OpenGameArt Fire Smoke Animations (Reactorcore) — CC0 PNG sheets/individual frames; evaluate style fit before promotion.
- OpenGameArt Smoke Vapor Particles — CC0 soft smoke textures.
- Poly Haven Cloud Layers HDRI — CC0, sky/lighting source; use mobile-resolution derivative in runtime, keep master in staging/reference.
- Poly Haven Wasteland Clouds Pure Sky — CC0, useful for apocalyptic/late-day atmosphere; use reduced runtime copy.
- Poly Haven forest/rock HDRIs and materials — CC0 candidates for lighting reference, ground/bark/rock material families; ingest selectively rather than bulk-shipping masters.

## Required tooling: EnvironmentScatter
Target: deterministic authoring tool that turns art rules into optimized world chunks.

Inputs:
- placement volume/polygon;
- seed;
- weighted asset set;
- density/cluster noise;
- slope/height limits;
- road/gameplay exclusion masks;
- min/max spacing and scale;
- LOD class and visibility range;
- collision mode.

Outputs:
- chunked MultiMeshInstance3D groups by asset/material/LOD class;
- optional selected collision proxies;
- metadata report: instance counts, estimated triangles, material families, shadow casters and cell bounds.

The tool must be deterministic: same seed + same rules = same placement. Designers can therefore regenerate maps safely.

## Required tooling: MapValidator
Automated warnings/failures for:
- oversized textures;
- excessive unique materials;
- micro props with unlimited visibility;
- too many shadow-casting lights/props;
- world-sized MultiMeshes;
- transparent foliage/VFX density;
- missing collision on gameplay cover;
- missing/invalid nav coverage;
- extreme longest sightline;
- excessive persistent decals;
- high-cost VFX without distance tiers.

## Performance test matrix
Every serious map must have reproducible captures:
- empty exploration;
- normal exploration;
- worst long sightline;
- dense forest;
- urban intersection;
- 10 enemies;
- 20 enemies;
- 30 enemies;
- grenade/explosion VFX stress;
- multiple fires/smoke;
- worst combined combat case.

Record FPS, frame ms, PerformanceBudget tier and enemy count on real Android hardware. CI validates structure; device measurements decide visual budgets.

## Research conclusions
1. Rich maps should be produced by composition + reuse + LOD/HLOD + atmosphere, not brute-force unique geometry.
2. MultiMesh is foundational for Arcont Mobile, but must be spatially chunked because instances are not independently culled.
3. Visibility ranges can bridge real mesh -> cheap mesh/group -> Sprite3D impostor -> disappearance.
4. Mobile renderer requires deliberate instancing; do not rely on Forward+-only automatic instancing behavior.
5. Fire, smoke, weather and distant scenery should use layered illusions with quality tiers.
6. Level layout itself is a performance tool: occlusion-friendly routes can reduce rendering work dramatically.
7. A reusable scatter + validator pipeline is higher leverage than manually placing thousands of props.

## Source notes
Primary implementation references researched: official Godot 4 documentation for GridMap, Navigation, Visibility Ranges/HLOD, mesh LOD, MultiMesh, occlusion culling, GPUParticles3D and 3D/GPU optimization. Asset candidates use CC0 sources from Kenney, OpenGameArt and Poly Haven. Re-check source/license at ingest time and record it in SOURCES_AND_LICENSES.