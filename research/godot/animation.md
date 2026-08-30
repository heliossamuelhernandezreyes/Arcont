# Godot — Character Animation

## Production direction
Use AnimationTree as the coordination layer as complexity grows. Separate locomotion from upper-body aiming/actions where possible.

## Topics
- AnimationNodeStateMachine for discrete states.
- BlendSpace1D/2D for locomotion direction/speed.
- Layered/additive recoil and hit reactions.
- Upper/lower body filters for ADS while moving.
- Turn-in-place and pivots.
- OneShot nodes for discrete actions.
- Root motion for authored contact-heavy actions.
- BoneAttachment3D for equipment anchors.
- Hand IK for weapon contact.
- Foot IK for uneven terrain.
- Look/aim constraints and procedural spine rotation.
- Animation LOD/update-rate budgeting for distant enemies.
- Retargeting and skeleton consistency in asset pipeline.

## Root-motion candidate policy
Ordinary locomotion should remain highly responsive and code-driven unless testing proves otherwise. Evaluate root motion for vault, mantle, execution and selected melee actions where authored spatial contact matters.

## References
- AnimationTree: https://docs.godotengine.org/en/stable/tutorials/animation/animation_tree.html
- AnimationNodeStateMachine: https://docs.godotengine.org/en/stable/classes/class_animationnodestatemachine.html
- BoneAttachment3D: https://docs.godotengine.org/en/stable/classes/class_boneattachment3d.html
- Root motion overview via AnimationTree documentation.
- fdemir real-controller (MIT): https://github.com/fdemir/real-controller
- catprisbrey Soulslike controller (MIT, patterns/reference): https://github.com/catprisbrey/Third-Person-Controller--SoulsLIke-Godot4

## Future research
Motion matching, inertialization, learned locomotion and procedural animation are WATCH topics; do not add complexity until the authored baseline is excellent.
