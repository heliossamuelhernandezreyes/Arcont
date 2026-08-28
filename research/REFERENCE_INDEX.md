# ARCONT Reference Lab

This branch is an isolated research/audit workspace. Nothing here is a production dependency unless it is separately reviewed, reimplemented or intentionally integrated into the playable branch.

## Rules
- Preserve source URL, license and purpose for every external reference.
- Prefer MIT/CC0/permissive material.
- Do not merge this branch wholesale into production.
- Audit patterns and architecture before copying code.
- Production remains mobile-first and Godot 4.7 compatible.

## Initial reference set

### Third-person controllers / camera / locomotion
- https://github.com/gdquest-demos/godot-4-3d-third-person-controller — TPS/shooter architecture reference.
- https://github.com/selgesel/godot4-third-person-controller — MIT; touchscreen TPS, gestures, zoom.
- https://github.com/Jeh3no/Godot-Third-Person-Controller — MIT; Godot 4.4–4.7, FSM, free/aim shoulder cameras, model orientation.
- https://github.com/fdemir/real-controller — MIT; Godot 4.6, AnimationTree and 8-direction locomotion.
- https://github.com/etherealxx/Godot-Third-Person-Controller-Mobile — MIT; Android/virtual joystick TPS reference.
- https://github.com/catprisbrey/Third-Person-Controller--SoulsLIke-Godot4 — MIT; AnimationTree/state-machine melee reference (older; patterns only).

### Tactical shooter / AI / combat-space reference
- https://github.com/AetherRadar/operation-steel-tide — Godot tactical/extraction shooter reference; squad AI, cover, stance, anatomical hit regions, larger combat spaces. Audit license before any code reuse.

### Official Godot engineering references
- https://docs.godotengine.org/en/4.7/tutorials/3d/spring_arm.html
- https://docs.godotengine.org/en/stable/classes/class_boneattachment3d.html
- https://docs.godotengine.org/en/stable/tutorials/animation/animation_tree.html
- https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html
- https://github.com/godotengine/godot-docs/blob/master/tutorials/performance/optimizing_3d_performance.rst

## Audit topics
1. Touch ownership and GUI/gameplay event isolation.
2. Camera orbit, shoulder swap, ADS and collision.
3. Character facing independent from camera orbit.
4. AnimationTree/state-machine locomotion and action blending.
5. Skeleton/BoneAttachment weapon mounting and eventual hand IK.
6. Tactical AI: cover scoring, suppression, flanking and orders.
7. Hit regions and damage architecture.
8. Mobile renderer constraints, visibility ranges, mesh LOD and occlusion.
9. Large-map streaming/visibility strategy.
10. Android performance budgets and scalable quality tiers.

## Important findings so far
- SpringArm3D should own camera collision rather than a hand-written single ray.
- Mobile touch needs explicit finger ownership and strict separation from emulated mouse input.
- Weapon equipment should follow the rig through BoneAttachment3D instead of a static torso transform.
- As locomotion complexity grows, AnimationTree/state-machine blending is preferable to manually switching isolated clips.
- Urban levels need occlusion/LOD strategy; rendering an entire city behind foreground buildings wastes mobile GPU/CPU work.
