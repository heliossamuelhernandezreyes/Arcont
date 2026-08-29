# Realistic Forest Settlement & Construction Guide

## Status
REFERENCE / TESTING. This document guides Arcont environment production; numeric performance ceilings remain unvalidated until Android profiling.

## Goal
Build a believable forest settlement that reads as a place people could actually have built and inhabited, while simultaneously serving third-person combat, navigation, occlusion and mobile rendering constraints.

## Core rule: construct before decorating
A convincing game settlement should have a plausible reason for every large form. Work in this order:
1. terrain and drainage;
2. access roads and pedestrian circulation;
3. parcels / yards / setbacks;
4. building foundations and structural volumes;
5. roofs, openings and utilities;
6. vegetation shaped by human use;
7. gameplay cover and encounter routes;
8. weathering, abandonment and story detail.
Micro-props must not compensate for implausible macro layout.

## Terrain and settlement logic
- Put roads and buildings where grades make sense; avoid arbitrary houses balanced on steep slopes.
- Keep a drainage logic: water follows low ground, roads crown or drain to edges, bridges cross actual depressions, and foundations meet terrain deliberately.
- Preserve the existing Arcont single physical ground-owner contract: ForestTerrainRelief remains the source of terrain height/collision.
- Use terrain, retaining walls, houses and dense vegetation as sightline breakers.
- Establish a hierarchy: primary approach, village street, service tracks, yards, footpaths and wilderness.

## Streets and pedestrian scale
Use real infrastructure dimensions as calibration references, then adapt for gameplay rather than copying regulations blindly.
- FHWA pedestrian guidance uses roughly 5 ft / 1.52 m clear sidewalk width as a baseline allowing two adults to walk side-by-side, with wider sidewalks in higher-use contexts.
- Vehicle lanes, shoulders, drainage and sidewalks should form a coherent street section rather than isolated floating slabs.
- Curbs, driveways, crossings, hydrants, poles, drainage and building entrances must agree spatially.
- Tactical widening is allowed, but disguise it through shoulders, parking, verges, porches, setbacks or damaged edges so combat space still looks architecturally plausible.

## Houses: believable construction anatomy
Do not model a house as a decorated box. Treat it as a simplified building assembly:
- foundation / slab / piers;
- floor system;
- load-bearing or framed walls;
- headers/openings for doors and windows;
- floor/ceiling structure where relevant;
- roof structure and overhang;
- exterior weather layer/cladding;
- interior partitions;
- utility/service clues.

For North-American-style light-frame references, the American Wood Council WFCM covers wall, floor, roof and connection systems, and WoodWorks provides light-frame construction details. Arcont does not need structural-engineering simulation, but visible geometry should respect how those systems produce real proportions and joints.

### Modular building kit
Author metric modules rather than one-off fake buildings:
- wall straight / corner / damaged variants;
- foundation and terrain transition pieces;
- doors and frames;
- windows and frames;
- floor/ceiling modules;
- roof edge, ridge, valley and gable modules;
- porch/step/railing modules;
- gutters/downspouts where appropriate;
- interior wall/door modules for enterable structures.
Keep dimensions consistent across the kit and validate against a human reference.

### Existing Arcont anchors
Retain the current calibration anchors unless a later audited pass changes them:
- human roughly 1.75–1.85 m;
- common door roughly 2.1 m high;
- cover around 1 m;
- passenger vehicle around 4.5 m long.

## Settlement authenticity
Before placing a prop, ask why it exists there.
- Houses need approaches and entrances.
- Garages/sheds need usable access.
- Fences should delimit something.
- Utility poles/cables should form a network, not isolated decoration.
- Trash and storage cluster near human activity, not uniformly across the map.
- Vegetation should react to mowing, roads, foundations, shade, water and abandonment.
- Damage should propagate logically from an event: impact, fire, collapse, infestation, evacuation or neglect.

## Forest composition
The forest must surround, penetrate and visually dominate the settlement without destroying tactical readability.
Use layers:
1. hero trees near playable routes;
2. midground tree clusters;
3. understory shrubs/saplings;
4. ground cover and leaf litter;
5. fallen logs, rocks and deadwood;
6. distant canopy / HLOD silhouettes.
Avoid uniform random scatter. Create ecological clusters, clearings, edges and succession around abandoned human spaces.

## Realistic tree asset policy
The current stylized/low-poly CC0 trees are technical placeholders, not Arcont's visual target.
Preferred source class: photogrammetry / realistic PBR assets with explicit commercial-compatible licensing and provenance.

Poly Haven is a strong CC0 source: its library states that models/textures/HDRIs are CC0 and includes hyperreal models. However, source tree meshes can be extremely heavy: examples currently list millions of triangles (Tree Small 02 ~5M tris, Fir Tree 01 ~8M tris), while smaller assets can still be hundreds of thousands. Therefore source quality is an authoring input, not a runtime budget.

Pipeline for realistic foliage:
1. preserve original source + license/provenance outside runtime selection;
2. inspect dimensions, pivots, materials and alpha usage;
3. create/choose a mobile LOD0 rather than shipping scan geometry directly;
4. generate progressively cheaper LODs / HLOD or impostor solution where useful;
5. constrain texture resolution on import;
6. prefer alpha scissor/alpha-tested foliage over alpha blending when visually acceptable;
7. split forest MultiMeshes into spatial cells so all-or-nothing MultiMesh visibility does not keep a whole forest alive;
8. benchmark shadows, overdraw and material complexity, not triangles alone;
9. validate on Android before promoting a numeric budget to canon.

Godot automatically generates mesh LODs for imported 3D scenes such as glTF/FBX and supports LOD on MultiMeshInstance3D. Manual visibility ranges/HLOD can coexist with automatic mesh LOD. For distant LODs, simpler materials can reduce per-pixel cost.

## Mobile rendering architecture
- Keep MultiMesh for repeated foliage, but spatially partition cells because individual MultiMesh instances are not independently culled.
- Use automatic mesh LOD for imported scenes as a baseline and authored HLOD where silhouette/material control matters.
- Buildings, walls and terrain should provide occlusion opportunities. Godot notes occlusion culling can be especially beneficial on the Mobile renderer, which lacks Forward+'s depth prepass.
- MultiMesh geometry is not automatically included when baking occluders; create simple manual occluders for major forest/structure masses where measurement justifies it.
- Prefer opaque geometry; for leaf cards prefer alpha scissor where acceptable. Alpha blending and overlapping transparent foliage are expensive.
- Consider LightmapGI for static settlement lighting: Godot documents it as high-quality indirect lighting with strong runtime performance suitable for mobile, while dynamic objects can receive indirect light through probes.
- Avoid assuming desktop/Xvfb screenshot performance represents Android.

## Level-design workflow
### Phase A — reference and intent
Define location, climate, settlement age, construction culture, abandonment/event history, mission flow and visual landmarks.

### Phase B — metric greybox
Build terrain, roads, house footprints, entrances, combat lanes, cover and verticality with metric anchors. Test movement/camera before detail.

### Phase C — structural pass
Replace boxes with believable modular building anatomy and coherent roads/drainage. Make enterable spaces structurally readable.

### Phase D — ecological pass
Place hero trees and forest masses deliberately, then understory and ground cover. Preserve combat silhouettes and navigation.

### Phase E — material/light pass
Use coherent PBR material families, weathering logic, baked/static lighting where appropriate, selective dynamic lights and atmospheric depth.

### Phase F — story/destruction pass
Add event-specific damage, abandonment, utilities, debris and environmental storytelling.

### Phase G — optimization
Profile representative Android scenes; tune LOD, HLOD, MultiMesh cell size, visibility, shadows, texture sizes, materials, occluders and lightmaps from measurements.

## Sources audited
- Godot stable/4.x documentation: Mesh LOD, Visibility ranges (HLOD), MultiMesh, Occlusion Culling, GPU optimization, Standard/ORM Material transparency, LightmapGI and renderer feature matrix.
- Epic Games Unreal Engine documentation: Building Virtual Worlds / Level Editor, used as cross-engine environment-production reference.
- American Wood Council: 2024 Wood Frame Construction Manual overview; wall/floor/roof/connection systems.
- WoodWorks: light-frame construction resources and construction/detail guidance.
- FHWA Pedestrian Facilities Users Guide: pedestrian/sidewalk dimensional references.
- Poly Haven: CC0 license/library and realistic model metadata.

## Arcont decisions from this audit
- Current tree_blocks foliage remains placeholder-only.
- New forest target is realistic PBR source quality followed by an explicit mobile optimization/LOD pipeline.
- Do not set a universal tree triangle ceiling yet.
- Build houses from believable structural assemblies and a metric modular kit, not decorated boxes.
- Rework settlement macro layout and forest composition before microdetail.
- Treat roads, foundations, drainage, entrances, utilities and vegetation as one spatial system.
- Add real-device benchmark evidence before declaring foliage/map budgets production-ready.
