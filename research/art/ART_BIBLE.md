# ARCONT Art Bible

## Purpose
This document defines the visual quality bar and decision language for Arcont. It is not a style prison: it exists so characters, props, environments, VFX, lighting and UI belong to the same world.

## Core visual pillars
1. Tactical readability before decoration.
2. Worn, functional survival technology rather than random visual noise.
3. Strong silhouettes at phone-screen size.
4. Material identity: metal, polymer, cloth, concrete, glass, flesh and alien matter must read differently even before close inspection.
5. Controlled color hierarchy: environment supports targets and interaction cues instead of competing with them.
6. Damage tells history and gameplay state.
7. Mobile-first art: visual richness comes from composition, material response, lighting and reuse, not brute-force geometry.

## Quality test
Every asset should answer:
- What is it?
- What gameplay role does it communicate?
- What material is it made of?
- Does its scale make sense next to the metric calibration scene?
- Does its silhouette survive at gameplay distance?
- Does it still look intentional under Arcont's mobile lighting?
- What is its LOD/material/texture budget?
- Can damage, animation or interaction alter it?

## Style consistency checklist
- Metric scale validated.
- Orientation/pivots consistent.
- Texel density follows category policy.
- Materials use shared naming/conventions.
- Roughness carries most surface storytelling; metallic is physically constrained.
- Normal detail does not replace silhouette where silhouette matters.
- Decals/grime have hierarchy: primary wear, secondary wear, microdetail.
- No random scratches/noise everywhere.
- Color accents are purposeful and repeat across factions/systems.
- Emissives are scarce enough to remain meaningful.

## Production hierarchy
Hero > Gameplay-critical > Midground > Background.
Spend geometry, texture memory, unique materials and shader complexity according to importance and screen occupancy.

## Arcont visual audit statuses
- BLOCKED: scale/rig/import/material is technically wrong.
- PROXY: useful for gameplay only.
- ART-PASS-1: silhouette/material language established.
- ART-PASS-2: wear/detail/lighting response established.
- MOBILE-VALIDATED: measured on target phone.
- FINAL-CANDIDATE: production-ready pending holistic review.

## Forbidden shortcuts
- Do not keep an AI-generated mesh because it looks good in one screenshot if topology, UVs, rigging or scale fail.
- Do not solve every surface with unique 4K textures.
- Do not add transparency where masked/opaque geometry can communicate the same thing.
- Do not use post-processing to hide weak lighting/materials.
- Do not accept asset packs with incompatible scale/style without normalization and art direction.
