# Materials and PBR Guide

## Principle
A believable material is defined more by correct energy response and roughness structure than by noisy albedo detail.

## Core maps
- Albedo/Base Color: surface color without painted-in lighting.
- Roughness: controls reflection spread; primary carrier of wear/material differentiation.
- Metallic: binary-ish physical classification; dielectrics normally 0, exposed metals normally 1, with transitions only where masks represent mixed/painted surfaces.
- Normal: micro/meso surface orientation detail.
- AO: restrained cavity support; do not multiply strong fake shadows into albedo.
- Emission: reserved for actual light-emitting surfaces and gameplay/faction language.

## Authoring rules
- Establish material at broad scale before scratches.
- Use roughness variation with causal logic: fingerprints, abrasion, wetness, polishing, dust.
- Painted metal is paint until coating is removed; exposed chip can reveal metallic substrate.
- Cloth needs broad fiber response without expensive microscopic geometry.
- Concrete/stone needs scale cues; avoid texture tiling that makes buildings look miniature.
- Skin/flesh should not be treated as generic glossy plastic.

## Mobile constraints
- Normal maps add tangent/vertex and sampling cost; keep where they materially improve screen-space result.
- Limit sampler count and shader branches.
- Prefer shared material families and masks/atlases where appropriate.
- Use texture import size limits for source textures that exceed useful target resolution.
- Mobile GPUs are commonly limited to 4096×4096 textures; production should generally need far less for most assets.
- Distant LOD materials may drop normal/detail features when measured gains justify the extra material variants.

## Texel-density policy
Define category ranges rather than one universal number. Hero characters/weapons receive more density than background architecture and distant props. Preserve consistency among adjacent objects so one asset does not look unnaturally sharp or blurry.

## Validation
Review materials under:
1. neutral calibration light;
2. Arcont daylight/overcast target;
3. dark combat lighting;
4. phone display at gameplay distance.

## Godot sources
- StandardMaterial3D/BaseMaterial3D documentation.
- 3D rendering limitations: mobile texture constraints and precision.
- GPU optimization and visibility-range documentation for material cost.
