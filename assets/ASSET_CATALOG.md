# Arcont Asset Catalog and Metric Contract

This file is the authoritative inventory for runtime and workbench 3D assets on `fix/mobile-playtest-2`.

## World scale
**1 Godot unit = 1 meter.**

Runtime content must be validated against gameplay dimensions instead of trusting authoring-package units.

Reference ranges:
- Human player: ~1.70–1.90 m tall.
- Standard door: ~2.0–2.2 m tall.
- Waist cover: ~0.8–1.1 m.
- Chest/high cover: ~1.3–1.6 m.
- Passenger car: ~4.0–5.0 m longest extent.
- Urban building module used by the current test district: ~16 m longest extent.

## Runtime assets currently present
### Kenney Survivors — CC0
- `characters/kenney_survivors/Model/characterMedium.fbx`
- `Animations/idle.fbx`
- `Animations/run.fbx`
- `Animations/jump.fbx`
- survivor/zombie skins and source artwork.

Role: temporary rigged human reference and animation carrier.
Current import contract: `OperatorModel.scale = 0.01` in `main.tscn`; CI verifies the resulting TPS/weapon scale.

### KayKit City Builder Bits — CC0 provisional selection
- Buildings: `building_A/B/C/D.fbx`
- Vehicles: hatchback, police, sedan, station wagon.
- Props: bench, box A/B, bush.
- Shared texture: `citybits_texture.png`.

Role: provisional urban blockout with real meshes.
Runtime rule: `UrbanEnvironment` measures visual bounds and applies a uniform metric scale profile. Do not add new FBX assets through raw `Vector3.ONE` assumptions.

Current target longest extents:
- building: 16.0 m
- vehicle: 4.5 m
- bench: 2.0 m
- box: 1.0 m
- bush: 1.5 m

These are gameplay calibration targets, not claims about the source package's authored units.

## Arcont bespoke character workbench
`tools/character_generator/` contains the deterministic modular Survivor generator.

Source configuration:
- target height: 1.78 m
- target budget: ~2,500 quads
- modular head/arms/forearms/thighs/shins for future gore/rigging
- output is a T-pose OBJ intended for cleanup/rigging, not direct production use.

Important: the generated OBJ/GLB is **not yet the runtime player asset**. The production pipeline remains:
`generator/concept -> cleanup/retopo -> UV/materials -> rig -> animation -> LOD -> collision/hit regions -> Godot-ready GLB -> validation`.

## Acceptance checklist for every new asset
1. License and provenance recorded.
2. Orientation and pivot checked.
3. Measured dimensions in meters recorded.
4. Uniform scale normalization applied once at the integration boundary.
5. Collision dimensions compared to visual bounds.
6. Material count and texture budget reviewed.
7. LOD/visibility policy assigned.
8. For characters: skeleton, sockets, hit regions and gore segmentation reviewed.
9. Asset-scale CI passes.
10. Real-device visual check before relying on the asset in gameplay evaluation.

## Known non-assets
Generation tooling, prompts, screenshots and pipeline experiments are not runtime assets simply because they exist in the repository history. A model counts as integrated only when a versioned mesh is intentionally placed under an asset path and passes the runtime validation pipeline.
