# Arcont — Visual validation 2026-08-29

Status: EVIDENCE / reference-lab

## Source history
- CI #447: first mounted modular-village evidence.
- CI #485/#487: forest-density iterations; #487 achieved a recognizable forest but exploded to ~11k nodes and produced giant foreground understory masses.
- CI #488, head `8669a318705813da478b161de45599546fd32bc9`: first spatial MultiMesh forest-strata implementation reviewed from `gameplay-village-center.png` and `gameplay-north-lookback.png`.

## What CI #488 proves
- The spatial MultiMesh conversion materially reduced runtime scene complexity versus the node-heavy forest pass: the capture overlay shows roughly 3.4k nodes instead of ~11.4k in CI #487. This is a structural improvement, not a real-device performance result.
- Forest enclosure remains dominant after batching; the village is still framed by continuous canopy/trunk masses rather than returning to an exposed settlement.
- The tactical route remains readable as a clearing through the forest.
- The visual block is still not accepted. Canopy crowns read as oversized rounded opaque blobs, especially near the top/foreground, and eye-level understory contains large boulder-like masses.
- The scene is too dark for architecture/vegetation material read in CI captures. Silhouettes are legible, but house edges, undergrowth and ground transitions collapse into near-black areas.
- The bright cyan/white central provisional prop remains visually dominant and requires a separate material/layer fix if it persists after the next capture.
- The current procedural crown meshes and `tree_blocks.fbx` remain placeholders, not final tree art.

## Performance interpretation
Godot documentation recommends MultiMesh for large repeated geometry counts, while visibility ranges/HLOD can be applied to MultiMeshInstance3D. On mobile/Compatibility renderers, automatic instancing is not available as it is in Forward+, so explicit MultiMesh remains relevant. MultiMesh should be spatially partitioned so node-level visibility/culling remains useful. Real Android profiling is still required before final budgets.

## Acceptance rule
A visual pass is not accepted because CI is green or because metrics are correct. Acceptance requires screenshot/device inspection of:
1. silhouette and proportion;
2. grounding/intersections;
3. material read;
4. composition and landmark hierarchy;
5. route/cover readability;
6. forest/urban transition;
7. mobile performance on real Android before final budgets.

## Immediate corrections after CI #488
1. Keep spatial MultiMesh batching and forest enclosure.
2. Narrow/taper canopy crowns and reduce their foreground scale so they read as tree crowns rather than opaque balls.
3. Reduce street-edge bush size/count and replace giant ground blobs with smaller irregular invasion patches.
4. Raise dusk ambient readability slightly while preserving nocturnal mood and contrast.
5. Re-capture representative views and reject/regress if forest enclosure is lost.
6. If the cyan/white central prop remains, trace its effective art layer/material and neutralize it without altering gameplay collision.

## Decision
ART-PASS-19 is **TECHNICALLY IMPROVED / VISUALLY ITERATE**. MultiMesh is the correct representation direction, but the forest block remains pending visual acceptance. ART-PASS-20 should retain the performance architecture while correcting crown silhouette, foreground clutter and dusk readability.
