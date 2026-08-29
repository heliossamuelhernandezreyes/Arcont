# Arcont — Modular Architecture Catalog

Status: CANDIDATE / reference-lab
Date: 2026-08-29

## Intent
Arcont buildings should read as places that could have been built, occupied, altered, abandoned and damaged. Do not author a house as one opaque mesh by default. Author a reusable architectural grammar: foundations, slabs/floors, wall bays, corners, openings, headers/lintels, doors, windows, porches, columns, beams, roof planes, eaves, fascia, gutters, chimneys, stairs, railings, exterior cladding, utilities and dressing. Assemble these into coherent silhouettes, then art-direct each lot.

This is visual/game-environment guidance, not structural engineering for real construction.

## Evidence translated into art rules
Whole Building Design Guide residential enclosure guidance decomposes a real house into foundations, walls/floors, exterior surfaces/cladding, weather layers, roofs, insulation/air layers and windows. For game art, invisible membranes/insulation usually collapse into material logic, while the visible structural/enclosure hierarchy remains useful.

Modular-environment production guidance consistently favors reusable snap-compatible walls, windows, doors and related pieces rather than one unique mesh per building. Godot GridMap/MeshLibrary can represent repeated metric modules, but irregular hero buildings may be assembled as ordinary Node3D hierarchies.

Godot imported mesh LOD is automatic for imported 3D scenes and also applies to MultiMeshInstance3D. Widely separated instances must not share giant MultiMeshes because culling/LOD is evaluated at the node/group level.

## Metric grammar
Use 1 Godot unit = 1 meter.

Candidate module grid:
- horizontal planning module: 0.5 m;
- common facade bay: 2.5–3.5 m;
- residential floor-to-floor: 2.7–3.2 m;
- exterior door clear visual height: ~2.0–2.2 m;
- common door width: ~0.85–1.05 m;
- common residential window bay: ~0.8–1.8 m wide;
- exterior wall visual thickness: 0.18–0.35 m depending on construction language;
- slab/floor thickness visible at edges: 0.15–0.30 m;
- eave projection: ~0.3–0.8 m;
- porch depth: ~1.5–2.5 m;
- steps: use believable rise/run proportions and avoid giant gameplay stairs unless deliberately stylized.

These are art-authoring anchors, not code requirements. Gameplay can widen openings/routes, but compensate architecturally so the result still looks intentional.

## Reusable module families
### Structure / massing
- slab rectangular variants;
- foundation/plinth segments;
- full wall bay;
- half wall bay;
- inside/outside corner;
- floor/ceiling panel;
- beam/header;
- column/post;
- stair straight/landing;
- retaining wall.

### Openings
- door bay centered/offset;
- single window bay;
- double window bay;
- storefront/glazed bay;
- garage/service opening;
- boarded/broken variants;
- lintel/sill/trim pieces independent of wall.

### Roof kit
- gable plane;
- hip plane;
- shed/lean-to plane;
- flat/parapet roof;
- ridge cap;
- valley/intersection cover;
- eave/fascia/soffit;
- gutter/downspout;
- chimney/vent;
- porch canopy/awning.

### Exterior character
- siding/plaster/brick/stone/concrete material families;
- base course/plinth;
- corner trim;
- shutters;
- balcony/railing;
- porch rail;
- columns/brackets;
- signage/mailbox/address plate;
- utility meter, conduit, cable, AC unit, vent;
- drain/downspout;
- fence/gate/retaining edge.

## House archetype catalog
Do not make eight color swaps of one box. Build a family with related construction language but distinct massing.

1. Compact gable cottage — 1 floor, 2–3 facade bays, front porch, dominant gable, chimney optional.
2. L-shaped cottage — intersecting masses, protected side yard, secondary roof.
3. Deep porch farmhouse — long facade, repeated posts, simple gable, rear service addition.
4. Hipped-roof bungalow — low broad silhouette, strong eaves, front veranda.
5. Two-storey narrow house — vertical facade rhythm, compact footprint, stair/landing implied.
6. Corner shop + residence — storefront/awning at ground, residential upper or rear mass.
7. Workshop/garage house — service door/garage bay, side residential volume, yard clutter.
8. Masonry courtyard house — heavier walls, privacy facade, gate/courtyard, flat/parapet or low roof.
9. Split/additive house — original small core plus visibly newer side/rear extension.
10. Civic/chapel/school landmark — repeated bays, stronger symmetry, tower/entry emphasis; rare, not a residential repeat.

## Urban lot grammar
A convincing building belongs to a lot:
road -> curb/drainage -> sidewalk/verge -> gate/driveway -> setback/front yard -> porch/entry -> primary mass -> rear/service zone.

Vary setback, orientation, lot width, fence state and vegetation. Avoid lining every house on the same perfect axis unless the settlement history calls for it.

## Beautiful composition rules
- Start with 1–3 simple masses, not detail.
- Give the silhouette one dominant idea: gable, hip, porch, tower, courtyard wall, storefront or workshop opening.
- Use asymmetry intentionally: offset entry, side addition, chimney, porch return, tree/yard relationship.
- Repeat window proportions within a building; variation should feel like renovation, not random generation.
- Roof logic follows massing. Every major volume needs a plausible drainage direction.
- Ground contact matters: foundation/plinth, steps and grade transition prevent the floating-box look.
- Add depth at facade edges: reveals, trim, sills, eaves, porches and recessed doors create shadows cheaply.
- Utilities go somewhere plausible and create excellent meso-detail.
- Damage follows construction: broken glass at openings, failed cladding at edges, roof damage exposing structure, impact damage localized to conflict zones.

## Settlement catalog / visual neighborhoods
Use controlled families so the map has history.

### Old village core
Small masonry/plaster houses, tighter setbacks, irregular lots, stone bases, mixed gable/hip roofs, narrow lanes, mature vegetation.

### Residential edge
Detached cottages/bungalows, deeper yards, fences, sheds, driveways, additions, utility poles.

### Commercial ribbon
Corner stores, workshops, awnings, service yards, signs, wider openings and harder paved frontage.

### Civic pocket
Bell/chapel/school/clinic/municipal landmark, square or widened street, stronger formal composition.

### Industrial/service edge
Sheds, garages, loading yards, retaining walls, tanks/pipes/fences; stronger occlusion masses and combat cover.

## Arcont-specific aging layers
1. Construction base.
2. Weather/age: runoff, damp base, faded paint, moss where exposure supports it.
3. Occupation: repaired boards, extensions, cables, signs, gardens, furniture.
4. Evacuation/conflict: barricades, abandoned vehicles, broken openings, localized debris.
5. Recent event: blood, fresh impacts, fire/smoke, dragged objects.

Never distribute all five layers uniformly.

## Runtime architecture policy
- Near/hero buildings: modular individual pieces where silhouette/depth matter.
- Repeated facade pieces may share meshes/materials and can be grouped where profiling supports it.
- Medium distance: simplified facade/roof group or HLOD proxy.
- Far distance: silhouette proxy/impostor; remove window recess microgeometry and small utilities.
- Interiors exist only when mission/gameplay requires them. Closed buildings should not secretly pay for full interiors.
- Collision is gameplay representation, not triangle-perfect architectural collision.
- Occlusion-friendly massing is desirable: buildings, courtyard walls and bends should naturally terminate expensive sightlines.

## First implementation target
Replace the current single-mesh residential placeholders in the forest village with an authored modular-house generator that produces multiple archetypes from shared metric pieces. Preserve the existing terrain-grounding contract and house collision envelope while improving silhouette, facade depth, roof logic and lot composition.

## Source notes
Research basis: Whole Building Design Guide residential enclosure/architecture guidance; official Godot 4 mesh LOD and GridMap/MeshLibrary documentation; reusable modular-environment production patterns including Roblox Creator modular environment guidance. Commercial marketplace kits were used only as taxonomy/reference evidence for useful module categories, not as source assets or geometry.