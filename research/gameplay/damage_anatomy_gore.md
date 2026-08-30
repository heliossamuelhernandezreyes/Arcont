# Gameplay — Anatomical Damage and Gore

## Identity opportunity
Arcont's limb damage is mechanically meaningful. Preserve that distinction: anatomy changes capability, not only visuals.

## System layers
1. Hit localization.
2. Damage type/energy/material interaction.
3. Local tissue/armor/limb state.
4. Functional consequence.
5. Animation/locomotion consequence.
6. Visual representation.
7. Audio/VFX response.
8. Persistence/performance policy.

## Functional examples
- Leg damage -> movement instability/reduced speed/crawl thresholds.
- Arm damage -> recoil/spread/reload/melee consequences.
- Head/critical anatomy -> high lethality where archetype permits.
- Dismemberment -> changes attacks/navigation silhouette rather than spawning decoration only.

## Production concerns
- Rig segmentation and seam hiding.
- Bone/mesh detach strategy.
- Collision/hitbox state after limb loss.
- Physics debris lifetime/pooling.
- Blood decals/particles and mobile overdraw.
- LOD: distant gore may use cheaper representation.
- Accessibility/content settings where appropriate.
- Animation coverage for altered anatomy.

## Research targets
Dead Space is a design reference for functional dismemberment; study systemic principles only. Also research medical/anatomical plausibility only to the degree useful for readable fictional combat; gameplay clarity outranks simulation for Arcont.

## Status
Functional provisional anatomy: IMPLEMENTED.
Production visual pipeline: OPEN.
