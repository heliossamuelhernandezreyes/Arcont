# Animation Quality Guide

## Goal
Animation must preserve responsiveness while giving actions weight, intent and readable contact.

## Principles
- Strong key poses and silhouettes before polishing curves.
- Anticipation only where it does not damage responsive control.
- Follow-through and secondary motion should reinforce force direction.
- Feet, hands and weapon contacts matter more than ornamental motion.
- Transition quality is part of animation quality; great clips with bad blending still look broken.

## Locomotion
- BlendSpace2D or equivalent directional locomotion as the set grows.
- Match stride speed to gameplay velocity to avoid foot sliding.
- Add turn-in-place/pivots when camera-relative movement makes them visible.
- Keep ordinary locomotion responsive; root motion is a candidate mainly for committed actions.

## Combat
- ADS uses upper-body layering/filters so legs keep locomotion.
- Recoil has weapon motion + body reaction + recovery; avoid purely camera-only recoil.
- Reloads need readable mechanical milestones for active-reload timing.
- Hit reactions should communicate direction/force without constantly stealing control.
- Melee needs anticipation, active/contact window, recovery and clear parry/execution grammar.

## Traversal
Vault/mantle/dodge should align animation displacement with collision/movement. Evaluate root motion or motion-warp-style placement for actions where contact points must be exact.

## Retargeting
Use consistent humanoid bone mapping and rest-pose policy. Godot SkeletonProfileHumanoid can auto-map common bone names, but mappings/rest poses must be inspected; incorrect parent relationships or rest orientation can break shared animation.

## Mobile
Animation update rates and skinning detail can scale with distance/importance. Distant enemies do not need the same update cadence as the player or nearby melee threats.

## Quality review
Test idle -> start -> locomotion -> stop -> pivot -> ADS locomotion -> fire -> reload -> crouch -> dodge -> vault/mantle -> damage -> melee -> execution as connected chains, not only isolated clips.
