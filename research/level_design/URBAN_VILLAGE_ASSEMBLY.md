# Arcont — Urban Village Assembly Grammar

Status: CANDIDATE / reference-lab
Date: 2026-08-29

## Purpose
Build a believable village as an assembled place, not as isolated house meshes. The map should read as something that could have existed before the disaster while remaining legible for third-person combat and scalable on Android.

## Evidence distilled
- NACTO treats streets as systems of travel lanes, sidewalks, furniture/curb zones, buffers, intersections and stormwater elements rather than a single road slab. Residential pedestrian through-zones are commonly described in the 5–7 ft range; commercial/downtown through-zones are wider. Use this as a realism reference, not a mandatory game dimension.
- WBDG describes residential enclosure as layered construction: foundation/slab, walls/floors, cladding, barriers, roof and windows. For game art, this supports modular assembly where believable joints and thicknesses matter more than simulating structural engineering.
- Godot GridMap/MeshLibrary can carry mesh, collision and navigation for repeated metric modules, but should not be forced onto irregular hero compositions. Navigation remains a deliberate representation.
- Godot visibility ranges/HLOD can replace groups of near individual houses with grouped proxies at distance; this is relevant to a village where architecture is modular but should not explode draw calls.

## Village hierarchy
The village is authored in nested scales:
1. district massing: forest enclosure, terrain ridges, main road, stream, village center;
2. blocks / parcels: buildable lots, setbacks, yards, service alleys, drainage and edge vegetation;
3. building footprints: house/shop/civic/service archetypes;
4. envelope modules: slab/plinth, wall bays, corners, openings, roof family, porch/balcony;
5. street edge: curb, sidewalk, ditch, tree/furniture zone, driveway cuts, fences;
6. story layer: vehicles, barricades, trash, damaged utilities, abandoned possessions;
7. micro layer: cracks, leaves, glass, papers, stains, cables and small vegetation.

## Map grammar for the current forest-village slice
The existing north-south route remains the primary movement spine. The village should gain:
- a recognizable central civic/commercial node around the square/tower;
- residential parcels on both sides rather than houses floating independently in terrain;
- short local access/driveway connectors from homes to the road;
- pedestrian edge bands/sidewalk fragments where the settlement is denser;
- drainage/ditch logic at the rural edges and near the stream;
- service/back-yard gaps that double as flanks;
- fences/hedges/walls that define ownership and create tactical partial cover;
- one or two cross-links rather than a perfect grid;
- a gradual transition from maintained village edge to forest invasion.

## Spatial rules
These are authoring candidates, not legal building-code claims.
- Main road: preserve existing gameplay width until device/playtest proves a change is needed.
- Residential pedestrian clear band: target roughly 1.5–2.1 m where a real sidewalk exists; rural houses may instead use verge/ditch/driveway logic.
- Commercial/civic pedestrian band: target roughly 2.4–3.6 m around the square and storefronts when composition allows.
- Setback variation: houses should not share one front line. Use shallow commercial frontage, medium residential setbacks and occasional deep yards.
- Driveways: typically one per parcel, narrower than the main road, visually connected to a door/garage/service area.
- Corners: reserve visibility and turning space; avoid placing dense clutter directly at every corner.
- Negative space: deliberate empty yards/clearings are required for combat readability and make dense story pockets feel richer.

## Parcel archetypes
Use a small reusable catalog with variation rather than unique whole-house assets:
- cottage parcel: small detached house + porch + side yard + low fence;
- family house parcel: larger footprint + rear yard + shed/utility strip;
- shop-house parcel: shallow setback + storefront/awning + rear service yard;
- civic parcel: tower/well/square + broader pedestrian apron;
- corner house: rotated or L-shaped relation to two routes;
- edge homestead: larger setback + ditch + vegetation invasion;
- service parcel: workshop/shed/garage + hardstand + crates/vehicle;
- damaged/abandoned parcel: same believable base grammar, then destruction layered on top.

## Architecture assembly policy
A house is not one block. Assemble from reusable pieces:
- foundation/plinth/slab;
- floor platform;
- wall bays and corners;
- structural-looking lintels/headers around openings;
- doors/windows with recess, sill and trim;
- roof planes/ridge/eaves/gutters/chimney;
- porch/deck/posts/stairs;
- balcony/canopy/awning where archetype calls for it;
- utility meter/downspout/vent/pipe;
- cladding/material variation;
- optional damage modules.

The result only needs to be structurally plausible to the eye. Do not simulate load calculations unless gameplay ever requires structural destruction.

## Technical representation
- Keep terrain as the single macro ground/collision owner.
- Urban surface overlays should sample terrain and remain visual unless they require distinct gameplay collision.
- Parcel markers and zoning data should be deterministic and separate from final visual modules.
- Repeated curb/fence/post/vegetation families should be chunkable into MultiMesh groups later.
- Hero buildings may remain composed Node3D hierarchies nearby; create HLOD/grouped proxies for distance only after visual approval and Android profiling.
- Navigation should be baked/maintained from gameplay geometry, not inferred from visible decoration.

## Visual acceptance rule
No map-system block is accepted by compile/test alone. Every mounted visual block must produce reproducible gameplay screenshots and be reviewed for scale, silhouette, street coherence, parcel logic, route readability, intersections, terrain contact and Arcont art direction.

CI screenshots are observational evidence, not proof of Android renderer quality or device performance. Real-device profiling remains required for budgets.

## Near-term implementation order
1. deterministic parcel/urban-plan data layer;
2. visualize lot boundaries only as debug/non-production aids;
3. sidewalks/curbs/verges/driveway connectors following terrain;
4. mount modular houses to parcel anchors rather than free coordinates;
5. fences/yard/service boundaries;
6. civic/commercial center composition;
7. forest-invasion transition masks;
8. story/damage pass;
9. nav/occlusion/HLOD validation;
10. repeated screenshot review and Android profile.

## Sources checked
- NACTO Urban Street Design Guide: street types, sidewalks, curb/furniture zones, intersections and stormwater design principles.
- WBDG Residential Building Enclosure: foundation, walls/floors, cladding, roof and windows as layered enclosure systems.
- Godot 4 documentation: GridMap/MeshLibrary, NavigationRegion3D and visibility ranges/HLOD.
