# Arcont — Visual Gate Evidence: CI #450

Status: OBSERVED / ACTIONABLE
Date: 2026-08-29
Source build: `feat/cc0-provisional-art-pass` @ `547237d8597da80202c885163b7d907fc7bc0dd7`

## Acceptance rule
A visual pass is not accepted because it parses, passes structural tests, exports Android, or satisfies metric contracts. It is accepted only after representative in-mission captures show the intended composition without obvious geometric/art-direction defects. CI and metrics remain necessary technical gates, not substitutes for visual review.

## Observed blockers in CI #450 captures
1. Gable roofs read as an inverted valley/open V. The generated left/right roof plane rotations are visually reversed.
2. The four-box hip approximation overlaps into a broken/crossed silhouette and must not ship as an accepted roof.
3. Correctness-first terrain route BoxMesh segments remain visibly legible as plates/terraces. Terrain adherence alone is therefore insufficient; the final route visual should be a thin sampled surface or purpose-built continuous mesh while `ForestTerrainRelief` remains collision owner.
4. Current forest prototype material reads bright cyan/teal in the CI renderer, overwhelming village composition. A temporary muted material override is acceptable as an interim art-direction fix, but the low-poly `tree_blocks.fbx` geometry remains non-final.
5. The village still lacks sufficient lot/street/forest transition and atmospheric hierarchy; subsequent passes should add these only after roof/route legibility is corrected so capture comparisons remain attributable.

## Immediate implementation trace
- Correct roof slope direction and suppress broken hip side plates until proper geometry exists.
- Convert existing terrain-following route groups to visual-only sampled top surfaces; hide source slab segments, retain terrain collision ownership.
- Apply a muted forest material override to current scatter cells, explicitly marked placeholder/non-final.
- Re-run the same four gameplay capture viewpoints and compare before mounting additional urban-detail passes.

## Non-conclusions
- CI/Xvfb FPS is not Android performance evidence.
- A color override does not make the current tree geometry production-quality.
- A green CI after these changes does not constitute artistic acceptance without reviewing the new screenshots.
