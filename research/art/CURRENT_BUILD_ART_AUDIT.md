# Current Build Art Audit — mobile-playtest-2

Audited production head: `fix/mobile-playtest-2` at `1e5e2b26166d18ac6edfc732f17fd6de354071b9`.
Evidence: repository scene/code inspection plus the 2026-08-28 Android screenshots. This audit does not promote anything to MOBILE-VALIDATED until the corrected build is inspected on the target phone.

## Executive finding
The current build is technically usable as a gameplay proxy after the metric/animation repair, but it is not an art pass. The dominant visual failure is incoherence: Kenney character art, KayKit urban models, procedural BoxMesh architecture/road/checkpoint, primitive weapon geometry and generic lighting are all visible together without a unifying material, silhouette or composition pass.

Overall status: **PROXY**.

## Player character — PROXY
What works:
- Real rigged FBX exists and is now metrically normalized.
- Runtime animation is validated by CI rather than allowed to remain in bind/T-pose.
- Character has enough silhouette to test TPS framing and locomotion.

Why it is not ART-PASS-1:
- Kenney Survivor is explicitly provisional and does not establish Arcont faction/technology language.
- No authored Arcont armor/material breakup, damage states, LOD set or production gore segmentation.
- Current 0.01 import compensation is technically controlled but should not become the production authoring convention.

Decision: keep only as a rig/locomotion mannequin until the Arcont Survivor GLB passes the production pipeline.

## Weapon visual — PROXY / highest-priority replacement
The visible gun is a `BoxMesh` (0.16 × 0.11 × 0.62 m). It communicates only muzzle direction. It has no weapon silhouette, sights, receiver/barrel/stock language, authored materials or faction identity.

Decision: do not polish this primitive. Replace it with the first authored weapon proxy/ART-PASS-1 asset while retaining the existing WeaponMount and muzzle contract.

## Urban environment — PROXY
Current district: 170 × 220 m, 14 m road, 18 repeated building placements, six vehicles and sparse props. Buildings/cars/props are real imported FBX assets and now receive runtime metric normalization, which fixes the catastrophic scale mismatch.

Art problems:
- Four building models are repeated along a long straight corridor, producing obvious kit repetition.
- Road, sidewalks, lane marks and checkpoint remain BoxMesh geometry.
- Collision volumes are generic boxes independent of visible imported geometry.
- Materials for generated geometry are flat StandardMaterial colors with roughness only; no authored material family or surface breakup.
- Sparse prop placement produces neither believable urban density nor strong gameplay composition.
- Current city is generated as a technical test district, not an authored encounter space.
- No explicit hero/midground/background hierarchy.

Decision: preserve the normalized FBX assets as kit candidates, but replace the current 170 × 220 showcase with a compact authored vertical-slice block before investing in detail.

## Materials — PROXY
Generated asphalt/concrete/building/military/boundary materials are flat albedo + roughness. They are useful calibration materials but fail the Art Bible material-identity target. Imported pack materials may read internally but are not harmonized with the generated geometry.

Needed for ART-PASS-1:
- shared Arcont material palette;
- coherent roughness ranges by surface class;
- controlled concrete/asphalt/paint/metal families;
- consistent texel density where textures are used;
- limited, purposeful wear and grime rather than random noise.

## Lighting — PROXY
Current scene uses one shadowed directional light (cool), one warm omni emergency light, ambient energy 1.35, tonemap mode 2 and no fog.

Problems:
- lighting is global rather than composed around traversal/encounter beats;
- no atmospheric depth/fog hierarchy;
- one emergency light cannot establish visual rhythm across a 220 m district;
- bright ambient fill reduces shape/material contrast;
- the current setup is useful for visibility testing but not a finished mood.

Direction for next pass: establish readable dusk/night baseline, directional key for form, restrained ambient fill, warm emergency/practical pools at gameplay landmarks, and cheap atmosphere/depth separation compatible with Forward Mobile.

## Composition / level readability — PROXY
The long straight road makes navigation simple but visually monotonous. Repeated buildings parallel to the road create a tunnel without authored reveals, focal landmarks, compression/release or meaningful silhouette changes. Enemy and cover markers are gameplay-functional but not yet supported by environmental composition.

Next vertical-slice composition should contain:
1. arrival/readable establishing view;
2. compressed approach;
3. generator landmark;
4. defensible combat pocket with multiple readable lanes;
5. Xeno/brute reveal space;
6. extraction/conclusion sightline.

## VFX — PROXY
The current visible muzzle effect is an OmniLight. Combat systems can be tested, but muzzle flash, impact families, blood/gore, sparks/dust and environmental response have not reached ART-PASS-1. VFX should be authored around cause/readability first and capped for mobile overlap.

## HUD — PROXY
HUD communicates objective, wave, hostiles, health, weapon/ammo and throwable state, while mobile controls expose the action set. It is functional but visually generic and crowded. Art work should wait until camera/control ergonomics are stable; then establish typography, spacing, hierarchy, safe areas and icon language.

## Asset disposition
### Keep and develop
- Kenney Survivor: temporary rig/animation calibration mannequin only.
- KayKit buildings/cars/props: provisional modular kit candidates; keep while building the first authored block.
- metric normalizer/calibration scene: permanent production tooling.
- WeaponMount/muzzle contract: permanent gameplay interface independent of final mesh.

### Replace rather than polish
- BoxMesh gun.
- procedural checkpoint boxes as final art.
- endless straight-road presentation.
- flat generic generated materials as final materials.

### Build next
- Arcont Survivor ART-PASS-1.
- one signature Arcont weapon ART-PASS-1.
- compact authored street/defense block.
- coherent material palette.
- lighting benchmark scene and final-block lighting pass.
- small reusable VFX impact/muzzle library.

## Promotion gates
### Scene → ART-PASS-1
- coherent silhouettes/material family;
- authored composition and landmarks;
- no accidental primitive visible as intended final art;
- all asset scales metric and validated;
- player/enemy readability survives gameplay distance.

### Scene → ART-PASS-2
- wear/detail hierarchy;
- lighting/material response coherent;
- VFX integrated;
- background/midground/hero hierarchy established;
- repetition disguised through modular composition, not noise.

### Scene → MOBILE-VALIDATED
- target-phone screenshots/playtest;
- frame pacing/GPU/CPU/thermal evidence;
- real screen-size readability;
- acceptable LOD/visibility transitions and worst-case VFX overlap.

## Immediate production order
P0: verify corrected APK on phone and preserve camera/scale/animation baseline.
P1: replace primitive weapon and establish Arcont Survivor silhouette.
P2: build one compact authored encounter block from normalized existing kit.
P3: material palette + lighting benchmark.
P4: VFX/readability pass.
P5: profile on target phone, tune budgets, then promote only proven elements.

## Audit conclusion
Do not spend time making the current procedural avenue prettier. Its value is systems testing. The fastest path to a visually credible Arcont is to use the repaired metric/import pipeline as infrastructure, then author one small representative slice to ART-PASS-1/2 quality and use that as the template for future content.