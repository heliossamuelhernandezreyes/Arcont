# ARCONT — Current Build Art Audit — 2026-08-28

Status vocabulary: BLOCKED / PROXY / ART-PASS-1 / ART-PASS-2 / MOBILE-VALIDATED / FINAL-CANDIDATE.

This audit records the current visual state after the metric-scale rescue, CC0 runtime art integration and hero-street composition pass. It is not a claim of final visual quality.

## 1. Player character

**Status: PROXY**

Current runtime player remains the Kenney survivor rig because it is technically reliable, metrically corrected and compatible with the current animation pipeline. Keep it for gameplay validation. Replace it for the final visual identity with the Arcont Survivor production asset after retopo, UV/material, rig, socket, LOD and mobile validation.

**Decision: KEEP TEMPORARILY / REPLACE FOR FINAL.**

## 2. Player materials

**Status: PROXY**

Current character material identity comes from the source asset and does not yet express the Arcont art bible: worn functional survival gear, controlled material roughness hierarchy, authored damage and stronger silhouette landmarks.

**Decision: TRANSFORM.**

## 3. Weapons

**Status: ART-PASS-1**

Five gameplay slots now use imported CC0 weapon meshes with explicit metric targets and CI validation instead of the former BoxMesh presentation. They are sufficient for a visual prototype and weapon silhouette recognition, but material cohesion, authored sockets, hands alignment and final weapon identity still require work.

**Decision: KEEP AS ART-PASS-1 / TRANSFORM FOR FINAL.**

## 4. Infected

**Status: ART-PASS-1 hybrid**

Intact infected use complete CC0 rigged zombie shells at a metric target of roughly 1.90 m. Runtime validates animation availability and combat animation mapping. When an anatomical state changes through limb loss or crawling, the visual system switches to the existing segmented anatomy fallback so gameplay behavior is preserved.

This removes the normal T-pose/primitive presentation while retaining dismemberment mechanics, but the segmented fallback remains visually primitive.

**Decision: KEEP HYBRID NOW / REPLACE SEGMENTED FALLBACK WITH PRODUCTION LIMB MESHES.**

## 5. Ranged enemies / Xenos

**Status: PROXY**

Gameplay systems exist, but their visual identity is not yet at the same maturity as the new weapon/infected pass.

**Decision: REPLACE/TRANSFORM AFTER CORE HERO STREET VALIDATION.**

## 6. Environment buildings and vehicles

**Status: ART-PASS-1 blockout**

KayKit/Kenney buildings and vehicles are metrically normalized through AssetScaleNormalizer and protected by CI. They remain useful modular blockout assets, but their style and material response are not yet sufficient for final Arcont presentation.

**Decision: KEEP SELECTIVELY / TRANSFORM COMPOSITION AND MATERIALS / REPLACE HERO ASSETS LATER.**

## 7. Street composition

**Status: ART-PASS-1**

The earlier street was technically functional but visually regular: repeated building rhythm, nearly periodic benches/boxes, uniform asphalt and weak focal hierarchy. The hero-street pass introduces:

- frontage slabs connecting sidewalk and building line;
- irregular prop rotations/placements;
- repaired asphalt patches;
- skid marks;
- blood marks;
- rubble clusters;
- paper litter using opaque thin geometry instead of transparency;
- broken metal fragments;
- asymmetric containment barriers;
- warning bands around the checkpoint focal zone;
- additional tactical cover markers tied to the new composition.

Detail geometry uses visibility ranges and the existing PerformanceBudget prop scaling, avoiding unlimited distant clutter.

**Decision: KEEP FOUNDATION / MOBILE-VALIDATE ON REAL DEVICE.**

## 8. Lighting

**Status: ART-PASS-1**

The previous scene was relatively flat because ambient energy and cool key intensity were both high. The hero-street pass establishes a clearer hierarchy:

- darker blue background;
- reduced ambient energy;
- cool directional moon key with the primary shadow;
- warm emergency accent near the objective without shadows;
- secondary cool emergency accent without shadows.

The lighting deliberately avoids adding many shadowed local lights. Fog remains disabled pending mobile profiling and art-direction need.

**Decision: KEEP DIRECTION / MOBILE-VALIDATE EXPOSURE AND BLACK LEVELS.**

## 9. Surface/material cohesion

**Status: ART-PASS-1 procedural foundation**

Procedural asphalt, concrete, military paint, grime, blood, warning, rubble, paper and dark-metal materials now provide a controlled palette and roughness hierarchy for blockout geometry. Imported packs still retain their source material styles and therefore visual cohesion is incomplete.

**Decision: TRANSFORM IMPORTED MATERIAL FAMILIES IN A LATER PASS.**

## 10. VFX / gore presentation

**Status: PROXY**

Functional gore and feedback systems exist, but geometry for severed parts remains placeholder-like and broader combat VFX still lacks the authored Arcont look.

**Decision: TRANSFORM AFTER INFECTED SEGMENTATION AND HERO STREET DEVICE TEST.**

## 11. Animation visual quality

**Status: PROXY to ART-PASS-1 depending actor**

Player runtime animation playback is technically fixed and CI-protected but limited in breadth. Intact infected now map Idle, Walk, Punch, RecieveHit and fall/defeat-related clips with action locking so locomotion does not overwrite combat reactions.

**Decision: KEEP TECHNICAL FOUNDATION / EXPAND PLAYER AND ENEMY GRAMMAR.**

## 12. Mobile visual performance

**Status: TESTING**

The build already has dynamic tiers for visibility, props, enemy detail, gore and animation update. Hero-street micro-detail is deliberately opaque, low geometry, unshadowed and distance-limited. Numeric ceilings are not final until representative Poco/Android profiling is captured.

**Decision: MOBILE-VALIDATE BEFORE RAISING DENSITY.**

## Current art priority after hero-street pass

1. Real-device screenshot/video validation of exposure, contrast, scale and clutter density.
2. Production-quality segmented infected limbs so dismemberment no longer reveals primitive fallback geometry.
3. Player Survivor art pass with final-ish silhouette/material family and better animation breadth.
4. Ranged/Xeno visual pass.
5. Imported environment material unification and one or two hero architecture assets.
6. Minimum authored combat VFX: muzzle, impact, blood, debris, explosions and readable Xeno effects.
7. Audio pass should follow closely because perceived production value will otherwise remain capped even if geometry improves.

## Principle confirmed

Arcont gains more visible quality from **composition + scale + silhouette + material hierarchy + lighting + controlled detail** than from indiscriminately increasing polygon count or importing more asset packs. The hero-street pass should be judged on a real Android device before increasing scene complexity.