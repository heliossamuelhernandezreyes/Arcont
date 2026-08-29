# Arcont — Model Asset Catalog

Persistent catalog of external 3D model sources and candidate assets for Arcont. A catalog entry is **not** production approval. Promotion still follows `research/production/asset_pipeline.md`: provenance/license -> inspect source files -> metric normalization -> cleanup/materials -> LOD/collision -> Godot import -> visual validation -> representative Android profiling.

## Status vocabulary
- `INDEXED`: source recorded; no production claim.
- `CANDIDATE`: worth a focused visual/technical trial.
- `STAGING`: exact downloaded assets under inspection/normalization.
- `PROMOTED`: intentionally integrated into a production branch after validation.
- `REJECTED`: tested and unsuitable; preserve the reason.

## Forest / vegetation

### Poly Haven — 3D Models
- URL: https://polyhaven.com/models
- License: assets are CC0 according to Poly Haven's official license/FAQ.
- Catalog status: `CANDIDATE — PREFERRED FOR REALISTIC FOREST TEST`.
- Why: high-fidelity scanned/authored models and PBR textures provide a stronger realistic source than Arcont's current primitive forest silhouettes.
- Acquisition/indexing: Poly Haven exposes asset metadata, categories, tags, authors, maximum texture resolution, thumbnails, file hashes and downloadable model variants through its public API. API usage terms are separate from the CC0 asset license and must be re-checked before automating bulk/live integration.
- Arcont policy: do not ship source fidelity blindly. Prefer selected tree/vegetation assets, normalize to meters, constrain texture resolution/material count, and build aggressive LOD/HLOD/visibility behavior for mobile.
- Proposed tree test tiers:
  - Near: recognizable trunk/major branches + controlled foliage silhouette; highest retained geometry/material quality.
  - Mid: aggressively decimated geometry/material simplification.
  - Far: very low geometry or impostor/billboard/HLOD where visually acceptable.
  - Forest mass: spatial MultiMesh/cluster representation and visibility ranges.
- Mobile risks: alpha/foliage overdraw, tiny triangles, texture memory, material switches, shadows and excessive source geometry.
- Acceptance gate: representative Arcont dusk scene screenshot + Android benchmark. No asset is accepted from catalog thumbnails alone.

### Quaternius — Ultimate Stylized Nature Pack
- URL: https://quaternius.com/packs/ultimatestylizednature.html
- License: CC0 stated by creator.
- Catalog status: `INDEXED / SECONDARY FOREST CANDIDATE`.
- Use: fallback/alternative when a lighter coherent stylized tree or vegetation family is useful.
- Caveat: visual fit must be compared against Arcont's realistic abandoned-village direction.

### Quaternius — Ultimate Nature Pack
- URL: https://quaternius.com/packs/ultimatenature.html
- License: CC0 stated by creator.
- Catalog status: `INDEXED / SECONDARY FOREST CANDIDATE`.
- Use: trees, vegetation, rocks and environmental fillers; inspect exact files before promotion.

### Kenney — Nature Kit
- URL: https://kenney.nl/assets/nature-kit
- License: CC0 stated by Kenney.
- Catalog status: `INDEXED / MOBILE-SAFE REFERENCE & FALLBACK`.
- Known research state: previously identified in `KNOWLEDGE_GAPS.md`; exact assets were not promoted as final forest trees.
- Use: inexpensive nature/rock/foliage candidates and metric/performance comparison baseline.
- Caveat: may be too stylized/low-detail for final near-field forest art.

### Fertile Soil Productions — Nature Props
- URL: https://fertile-soil-productions.itch.io/nature-props
- License: creator page previously audited as CC0; re-check exact downloaded package/provenance before promotion.
- Catalog status: `INDEXED / DEADWOOD & GROUND-PROP CANDIDATE`.
- Use: logs, branches, roots, rocks/stepping stones; not assumed to solve the standing-tree requirement.

## Current forest decision — 2026-08-29
Arcont will test **Poly Haven first** for standing trees and realistic vegetation, with an **aggressive mobile LOD strategy** rather than choosing a visibly inferior source solely for low source polygon count. Existing spatial MultiMesh work remains valuable and should be preserved where compatible. The source asset's maximum fidelity is an authoring input, not the runtime budget.

The test must explicitly measure: retained triangles by LOD, material count, texture memory/resolution, alpha/overdraw behavior, shadow cost, draw calls/instances, visual silhouette at near/mid/far ranges, frame CPU/GPU, 1% lows/frame pacing, memory and thermal trend on representative Android hardware. Budgets remain empirical until measured.

## Catalog expansion rule
Whenever a useful model gallery/pack is found, index the source here even if it is not immediately used. Record source URL, license/provenance, category/use, quality/style, mobile risks, status, exact selected assets once known, and rejection/promotion evidence. This file is the model-source memory; exact production files still require the asset pipeline and visual acceptance gates.
