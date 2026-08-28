# VFX Guide

## Purpose
VFX communicates causality, force and danger. Decorative spectacle is secondary to gameplay readability and mobile performance.

## Effect hierarchy
1. Gameplay-critical telegraph.
2. Impact/confirmation feedback.
3. Environmental atmosphere.
4. Cosmetic flourish.
Critical information always wins when effects overlap.

## Weapon effects
Separate muzzle flash, smoke, mechanical movement, tracer/projectile cue, impact spark/debris, surface response and distant persistence. Do not use one giant particle burst for everything.

## Gore
- Blood direction should follow impact/sever event.
- Use short-lived particles plus restrained persistent evidence.
- Cap decals/particles/debris by importance and distance.
- Functional anatomy state must remain readable after gore settles.

## Mobile constraints
- Transparency/overdraw is expensive, especially stacked particles.
- Keep sprites/meshes tight around visible content.
- Reduce particle amount, lifetime, size and overlapping layers before sacrificing readability.
- Use distance/importance tiers and hard caps.
- GPU particles provide powerful simulation but still incur rendering/fill costs; CPU particles can be fallback/reference for older targets where appropriate.
- Forward Mobile supports decals but has a per-mesh limit; do not assume unlimited bullet/blood decals.

## Stylization
Use shape, timing and value before particle count. A fast clean flash with a strong sound may feel more powerful than a huge translucent cloud.

## Testing
Create isolated VFX test scenes for muzzle, ballistic impact by material, explosion, EMP, blood hit, severing and Xeno abilities. Measure worst-case overlapping effects on target hardware.
