# Arcont Realistic Asset Warehouse

Status: research warehouse only. Nothing in this catalog is runtime-approved merely because it is listed here.

## Goal
Build a very broad, license-auditable reservoir of realistic source material for Arcont. Storage breadth is preferred here; runtime promotion remains selective and mobile-budgeted.

## Trust tiers

### Tier A — preferred, CC0/public domain
- Poly Haven — photoreal 3D models, PBR textures, HDRIs; CC0.
- ambientCG — large CC0 PBR material/HDRI/3D library.
- Existing verified CC0 packs already staged in Arcont.

### Tier B — useful but per-asset/license review required
- Sketchfab downloadable assets filtered to CC0 only.
- OpenGameArt resources only when the individual asset license is compatible and provenance is retained.
- Other repositories only after explicit license/provenance review.

Do not ingest an asset with unknown, editorial-only, non-commercial, or ambiguous redistribution rights.

## Warehouse taxonomy

### Natural world
- terrain: forest floor, mud, dirt, gravel, sand, clay, snow, wet ground, paths, tire tracks
- rock: boulders, cliff faces, rubble, pebbles, mossy/wet variants
- vegetation: deciduous/conifer trees, saplings, dead trees, logs, roots, bushes, ferns, grasses, weeds, ivy, moss, leaf litter, mushrooms
- water/wetlands: puddles, river stones, reeds, banks, mud transitions

### Rural / settlement architecture
- brick, stone, concrete, plaster, stucco, timber, roofing, corrugated metal
- modular walls, corners, doors, windows, shutters, frames, stairs, railings, gutters
- barns, sheds, cabins, workshops, garages, fences, gates, retaining walls
- interior shells, floors, ceilings, beams, trim

### Urban / industrial
- asphalt, sidewalks, curbs, drains, manholes, road markings
- barriers, bollards, signs, poles, cables, utility boxes
- warehouses, factory pieces, pipes, valves, ducts, tanks, pallets, crates
- damaged/burned/rusted/abandoned variants

### Props / set dressing
- furniture, appliances, tools, containers, trash, debris, papers, books
- workshop/farm equipment, barrels, sacks, rope, tarps
- street furniture, bins, benches, lamps
- food/kitchen/general household clutter

### Vehicles / machinery reference reservoir
- civilian cars, vans, trucks, trailers, tractors, construction/farm machinery
- wheels/tires, wreckage and vehicle debris
- assets require especially careful source/license and mobile geometry review

### Characters / creatures support
- realistic clothing/material references, footwear, gloves, bags, tactical accessories
- human scan/reference assets only when licensing clearly permits game use and redistribution strategy is compatible
- animation/reference libraries remain separate from final character identity

### PBR material families
- ground, rock, bark, leaves, wood, metal, rust, concrete, brick, plaster, roofing
- fabric, leather, rubber, plastic, glass, ceramic, painted surfaces
- blood/grime/mud/wetness/decal source materials where licensing permits

### Lighting / skies
- overcast forest, sunrise/sunset, cloudy, clear, night, industrial/interior HDRIs
- neutral calibration HDRIs for material validation

### VFX source reservoir
- smoke/fire/embers/dust/fog/rain/snow/water splash references and permissively licensed textures/flipbooks
- decals: cracks, leaks, stains, moss, dirt, bullet/impact surface references

### Audio reservoir (separate from visual promotion)
- ambience: forest, wind, rain, interiors, village, industrial
- Foley/material impacts and footsteps
- mechanical/vehicle/environment layers
- only ingest with explicit compatible license metadata

## Required metadata per acquired item
Every acquisition record should retain:
- source provider
- canonical source URL / asset ID
- author/creator when applicable
- exact license and license URL/text snapshot
- acquisition date
- original filename and format
- source resolution / texture maps
- dimensions / scale when known
- polygon/vertex count when known
- tags and intended Arcont use
- SHA-256 after download
- runtime status: warehouse / candidate / approved / rejected

## Resolution policy
Warehouse may retain source/master quality. Runtime derivatives should normally be generated separately (for example 1K/2K textures and optimized meshes for Android), preserving the source master and provenance.

## Promotion rule
Warehouse != game. Assets reach runtime only after visual fit, metric scale, material correctness, collision/LOD strategy, license/provenance, memory and Android performance checks.
