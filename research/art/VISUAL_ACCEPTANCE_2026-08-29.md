# Arcont — Visual Acceptance Audit 2026-08-29

Status: ACTIVE / evidence-based visual gate

## Evidence inspected
CI #444 in-mission captures from branch `feat/cc0-provisional-art-pass`, commit `612a4df5186aeb36aa49c433bd0ebe70c56b63a9`:
- gameplay-start.png
- gameplay-village-approach.png
- gameplay-village-center.png
- gameplay-north-lookback.png

## Critical finding: architecture pass was not actually mounted
The screenshots were generated successfully, but `scenes/main.tscn` at the same commit does not reference or instantiate `scripts/modular_village_architecture_pass.gd`.

Therefore CI success and successful screenshot capture did **not** prove the new modular architecture was integrated into the playable scene. The captures still represent the previous village visual state.

This is exactly why visual acceptance must happen after structural/CI validation.

## Visual acceptance rule
No visual block may be labeled complete merely because:
- the project parses;
- tests pass;
- Android exports;
- the asset/script exists in the branch;
- metrics/metadata report expected values.

A visual block is accepted only after:
1. the runtime scene actually instantiates the intended system;
2. representative in-game captures are generated after the change;
3. the captures are visually inspected;
4. obvious composition, scale, grounding, silhouette, material or integration defects are corrected;
5. CI remains green after the correction.

## Current screenshot findings
The current village remains a provisional blockout visually:
- architecture reads as simple colored building masses;
- forest identity is weak from gameplay viewpoints;
- road/path segmentation is visually obvious;
- environment/material response is very flat under CI software rendering;
- cyan/bright foliage silhouettes are not representative of the intended Arcont quality;
- several broad surfaces dominate the frame without enough architectural hierarchy or material breakup.

These observations are CI/Xvfb software-render evidence, not Android renderer quality measurements. They are valid for composition/silhouette/integration checks but not final exposure, material fidelity or performance budgets.

## Next gate
Mount `ModularVillageArchitecturePass` in the playable scene, add a runtime contract that proves it built eight modular houses and superseded legacy house visuals, capture the same four viewpoints, and inspect those images before any claim that ART-PASS-9 improved the village.
