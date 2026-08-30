# Character Art Guide

## Production goals
Characters must remain readable in third-person on a small display, animate cleanly, support anatomical gameplay and fit a constrained mobile skinning budget.

## Pipeline
Concept/reference -> blockout -> silhouette approval -> production mesh/retopo -> UV/material IDs -> textures -> skeleton/skin -> gameplay sockets/hit regions -> animation tests -> damage segmentation -> LODs -> Godot import -> calibration scene -> mobile validation.

## Silhouette
- Primary silhouette carries faction/role.
- Secondary shapes communicate equipment and protection.
- Tertiary details should not be required for identification.
- Test at typical gameplay distance and reduced resolution.

## Topology
- Spend deformation loops at shoulders, elbows, hips, knees, neck and hands.
- Keep gore/dismemberment boundaries deliberate rather than arbitrary mesh cuts.
- Avoid tiny geometry that becomes subpixel noise.
- Preserve predictable normals/tangents and manifold surfaces where practical.

## Rigging
- Standardize humanoid naming/mapping and retarget through Godot SkeletonProfileHumanoid where suitable.
- Validate bone rests, hierarchy and scale before animation sharing.
- Establish weapon, muzzle, hand, head, spine and gameplay attachment sockets.
- Test extreme ADS, crouch, dodge, vault and melee poses for clipping.

## Materials
Prefer a small reusable material set: skin/flesh, cloth, polymer, painted metal, bare metal, armor, glass/visor, alien material. Use masks/atlases where they reduce draw calls without destroying iteration speed.

## Damage-ready construction
Separate gameplay anatomy from visual gore implementation. A limb can have:
- hit region
- health/functional state
- visual mesh group
- sever boundary/cap
- blood/VFX socket
- alternate animation state

## LOD strategy
LOD0: close gameplay and executions.
LOD1: ordinary combat distance.
LOD2: distant actors with simplified silhouette/material features.
Potential impostor/culling only if large crowds justify it.

## Arcont Survivor
The procedural Survivor base is a workbench, not final art. It should graduate only after production retopo/UV/material/rig/animation and mobile tests. Keep its modular anatomy because it aligns with Arcont's functional damage identity.
