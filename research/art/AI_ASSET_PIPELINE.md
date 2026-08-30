# AI / Generative 3D Asset Pipeline

## Rule
Generative output is source material. It becomes an Arcont asset only after passing the same production requirements as handmade geometry.

## Pipeline
1. Reference sheet / multiview concept.
2. Generate candidate mesh(es).
3. Select based on silhouette and structural usefulness, not screenshot beauty.
4. Metric normalize and orient.
5. Cleanup nonmanifold/duplicate/internal geometry.
6. Retopology appropriate to deformation/gameplay.
7. Define modular/gore boundaries where needed.
8. UV unwrap and texel-density policy.
9. Re-author/clean PBR materials and textures.
10. Rig/skin or validate rigid pivots.
11. LOD generation/manual cleanup.
12. Collision/gameplay sockets.
13. Export GLB.
14. Godot import validation.
15. Calibration scene + target-phone performance/art review.

## Reject conditions
- Impossible topology that would cost more to repair than rebuild.
- Inconsistent anatomical/mechanical structure.
- Baked lighting/artifacts embedded in albedo.
- Unmanageable UV/material fragmentation.
- Silhouette that conflicts with Arcont art direction.
- Unknown/unacceptable source/license provenance.

## Hunyuan/Tripo/etc.
Treat model brands/backends as replaceable acquisition stages. Preserve backend, prompt/reference, version/settings and license/provenance in metadata so results are reproducible and auditable.

## Characters
AI character generation does not bypass retopology, rigging, rest-pose validation, deformation tests, anatomical hit regions or gore segmentation.

## Environments/props
Generated props can be useful for blockout or unique hero objects, but modular environment kits benefit strongly from authored dimensions, pivots and repeatable topology.

## Quality principle
The goal is not to make AI output less obvious by adding random detail. The goal is to pass it through coherent art direction, physical material logic and a reproducible technical pipeline until its origin no longer determines its quality.
