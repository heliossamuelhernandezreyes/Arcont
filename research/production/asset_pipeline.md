# Production — 3D Asset Pipeline

## General pipeline
Reference/concept -> model/generation -> cleanup/retopology -> UV -> materials/textures -> rig -> animation -> LOD -> collision -> export -> Godot import -> validation -> performance test.

AI/generated geometry is one possible input, not a substitute for the production pipeline.

## Character checklist
- Consistent scale/orientation.
- Production topology suitable for deformation.
- Skeleton naming/retargeting policy.
- Material count budget.
- Texture resolution budget.
- LODs.
- Hit regions and gameplay sockets.
- Weapon/hand attachment points.
- Dismemberment segmentation if required.
- Mobile skinning cost.

## Environment checklist
- Modular dimensions/grid.
- Collision complexity.
- Occluder value.
- LOD/visibility ranges.
- Material reuse.
- Lightmap/runtime-light strategy if used.
- Navigation implications.
- Destruction states.

## Weapon checklist
- First/third-person readability decision.
- Muzzle/ejection/hand sockets.
- Magazine/bolt/slide moving pieces.
- Animation pivots.
- LOD/material budget.

## Existing Arcont tooling
The repository already contains a 3D pipeline/preflight and generation experiments. Preserve those as experimental acquisition tools while building a conventional validation/cleanup path around them.

## Future research
Blender automation, glTF import metadata, automatic LOD generation, mesh optimization, texture atlasing, retargeting, animation compression and reproducible asset validation.
