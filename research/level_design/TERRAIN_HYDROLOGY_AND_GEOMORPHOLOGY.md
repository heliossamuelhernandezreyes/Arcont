# Arcont — Terrain, Hydrology & Geomorphology

Status: REFERENCE / reference-lab
Date: 2026-08-31

## Purpose
Define how hills, ridges, valleys, streams, erosion, rocks and traversable landforms should relate so the map reads as a coherent landscape instead of arbitrary sculpting.

## Core rule
Water and gravity organize terrain. A believable forest map should have a drainage hierarchy and landforms that explain where water, sediment, exposed rock and vegetation occur.

## Terrain hierarchy
Author terrain in this order:
1. watershed-scale fall direction and major ridges;
2. primary valley / drainage;
3. secondary gullies and tributary depressions;
4. hills, shoulders, saddles and local ridges;
5. stream channel and flood/riparian zone;
6. erosion cuts, talus, rock outcrops and microrelief.

Do not sculpt isolated hills and then draw a river across them. Drainage should emerge from or agree with the heightfield.

## Derived terrain fields
From the heightfield compute or approximate:
- elevation;
- slope magnitude;
- aspect;
- local curvature/convexity;
- flow direction;
- flow accumulation;
- wetness/moisture proxy;
- distance to channel;
- ridge/valley classification.

These fields should drive both visuals and scatter rules.

## Rivers and streams
A stream should generally occupy connected low ground. Channel width, rockiness and bank form should increase with accumulated flow rather than remain constant.

Practical game hierarchy:
- seep / wet depression: vegetation/material change, little or no visible water;
- ephemeral gully: shallow incision and debris concentration;
- small stream: narrow continuous water with banks and stones;
- primary creek/river: wider channel, stronger bank definition, crossings and floodplain cues.

Use spline tools only after deriving or validating the drainage path against terrain. The spline should conform to the drainage logic, not override it blindly.

## Erosion and deposition logic
- Convex ridges/shoulders: thinner soil, more exposed roots/rock, drier material family.
- Steep slopes: less loose fine ground cover, more exposed rock and erosion scars.
- Concave hollows/toeslopes: deeper-looking soil, more litter, moisture and deposition.
- Stream inside bends / low-energy pockets: finer sediment and vegetation.
- High-energy channel segments: coarser stones, exposed bed material, fewer fragile plants.
- Talus/scree: accumulate below cliffs or outcrops, not randomly on flats.

## Rock distribution
Rocks should come from a geological story:
- bedrock outcrop tied to steepness, ridges or erosional exposure;
- detached boulders concentrated below outcrops, steep slopes or channels;
- rounded stream stones aligned with active or historical drainage;
- buried/embedded stones should match ground contact and slope.

Random rotation and scale are allowed only after choosing a geologically plausible placement zone.

## Traversal and level design
Topography is also gameplay architecture.
- Ridges create occlusion walls and orientation silhouettes.
- Saddles create natural passes.
- Valleys create route channels.
- Stream crossings become encounter gates.
- Steep slopes can block movement without invisible walls.
- Terraces/benches create combat platforms.
- Curved drainage and ridges prevent infinite sightlines.

Keep traversal grades readable. When gameplay requires a climbable slope that would otherwise look artificial, support it with erosion, vegetation breaks, switchbacks, exposed roots or rock steps.

## Water-adjacent ecology
Distance-to-water should influence:
- soil darkness/wetness;
- moss probability;
- fern/shrub density;
- deadwood moisture treatment;
- tree-family weighting;
- fog/haze pockets where artistically justified.

Do not use a hard circular river buffer. Blend with flow accumulation, elevation and local slope.

## Heightfield generation guidance
Procedural terrain should combine low-frequency structure and controlled high-frequency erosion detail. Avoid stacking noise octaves without landform intent.

Recommended conceptual stack:
- macro ridge/valley field;
- directed drainage/valley carve;
- secondary erosion field;
- local rock/soil microrelief;
- authored gameplay corrections with smooth masks.

Any gameplay edit that changes terrain should trigger a drainage sanity check.

## Validation rules
Fail the map if:
- streams climb uphill;
- tributaries disconnect without explanation;
- river width ignores drainage scale;
- boulders float or appear uniformly random;
- talus exists without a source slope/outcrop;
- wetland/riparian vegetation ignores low ground;
- steep slopes carry the same soil/ground cover as flats;
- terrain contains repeated noise bumps with no larger landform structure.

## Source basis
- US Forest Service Integrated Moisture Index work combines slope-aspect shading, cumulative flow, curvature and soil water-holding capacity to describe landscape moisture: https://research.fs.usda.gov/treesearch/11583
- US Forest Service studies on topographic position, exposure, moisture and vegetation support using ridge/cove/aspect/moisture differences rather than uniform biome scatter: https://research.fs.usda.gov/treesearch/56080 and https://research.fs.usda.gov/treesearch/54881
- General watershed/geomorphology practice from USGS/NRCS should be used when a specific real-world biome/location is chosen; this guide intentionally stores transferable rules rather than pretending one channel geometry fits every climate.

## Arcont decision
Terrain generation owns drainage. Rivers, rocks, materials and vegetation must consume derived terrain fields so that all environmental systems agree spatially.