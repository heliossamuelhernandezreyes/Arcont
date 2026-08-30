# Production — 3D Asset Pipeline

## General pipeline
Reference/concept -> model/generation -> cleanup/retopology -> UV -> materials/textures -> rig -> animation -> LOD -> collision -> export -> Godot import -> validation -> performance test.

AI/generated geometry is one possible input, not a substitute for the production pipeline.

## World-scale contract
**1 Godot unit = 1 meter.**

Never trust FBX/OBJ/GLB authoring units blindly. At the integration boundary:
1. instantiate/import the asset;
2. measure visual bounds;
3. compare against a gameplay reference dimension;
4. apply one uniform normalization factor;
5. validate collision against visual dimensions;
6. record the source, target dimensions and scale factor;
7. make CI reject absurd scale regressions.

Reference dimensions are contracts, not aesthetic guesses: human ~1.7–1.9 m; common door ~2.0–2.2 m; passenger vehicle ~4–5 m; waist cover ~0.8–1.1 m.

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
- Verify AnimationTree is actually playing a state; existence of clips/tree alone does not prove deformation at runtime.

## Environment checklist
- Modular dimensions/grid.
- Collision complexity.
- Occluder value.
- LOD/visibility ranges.
- Material reuse.
- Lightmap/runtime-light strategy if used.
- Navigation implications.
- Destruction states.
- Per-category metric scale profile for external packs.

## Weapon checklist
- First/third-person readability decision.
- Muzzle/ejection/hand sockets.
- Magazine/bolt/slide moving pieces.
- Animation pivots.
- LOD/material budget.
- Validate world scale after BoneAttachment/reparenting; imported skeleton transforms can make local scale intuition misleading.

## Arcont lessons from Android playtest 2026-08-28
A green structural CI allowed a visually invalid TPS build because the rig and clips existed while the imported human scale/camera relationship was wrong. A subsequent scale contract exposed a second error: compensating the WeaponMount by `100x` produced a global scale near 100. The lesson is to test **global observed dimensions/transforms**, not just local properties or node existence.

The playtest also exposed a runtime T/bind pose while the test reported an AnimationTree and valid clips. Tests must verify the state machine is actually running, not merely constructed.

KayKit/Kenney remain useful provisional sources, but all external packs must pass metric normalization before gameplay judgement.

## Existing Arcont tooling
The repository already contains a 3D pipeline/preflight and generation experiments. Preserve those as experimental acquisition tools while building a conventional validation/cleanup path around them.

The modular Arcont Survivor generator produces a meter-scale T-pose OBJ workbench source. It is not a runtime character until it completes cleanup, rigging, animation, LOD, collision/hit-region and Godot validation.

## Future research
Blender automation, glTF import metadata, automatic LOD generation, mesh optimization, texture atlasing, retargeting, animation compression, reproducible asset validation and automated visual-bound/collision mismatch reports.
