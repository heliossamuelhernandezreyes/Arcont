# Arcont — Poly Haven Ingest & Provenance 2026

Status: REFERENCE / reference-lab
Date: 2026-08-31

## Current source status
Poly Haven states that its HDRIs, textures and 3D models are licensed CC0 and may be used for commercial work. Poly Haven also provides a public API for asset metadata and lists; its July 2026 API announcement states the API is free for everyone, including commercial use.

## Policy
Treat Poly Haven as a high-quality source warehouse, not a runtime dependency.

For every promoted asset record:
- Poly Haven asset slug/name;
- source page URL;
- asset type;
- license = CC0;
- retrieval date;
- source resolution/mesh statistics when known;
- selected runtime derivative;
- optimization operations performed;
- runtime texture resolution;
- LOD/HLOD/impostor class;
- material family;
- intended map role.

Do not copy Poly Haven webpage text, logos or showcase imagery into Arcont as if those were CC0 assets. Poly Haven's license page distinguishes the CC0 assets themselves from site content such as branding/text.

## Forest import priorities
### Terrain/material masters
- forest floor / leaf litter;
- mud / wet soil;
- moss;
- bark;
- cliff/rock;
- gravel/streambed;
- roots/deadwood.

Prefer 2K or lower runtime derivatives unless close-up testing justifies more. Keep high-resolution masters in staging/reference, not default runtime.

### Model masters
- rocks/boulders;
- logs/stumps/deadwood;
- selected hero trees;
- small natural props where scan quality materially improves realism.

Source scan geometry may be far too dense for mobile. Build or select optimized derivatives before runtime promotion.

### HDRI / sky masters
Use HDRIs primarily for:
- lighting reference;
- sky/background candidates;
- material calibration.

Runtime versions should be deliberately reduced to the lowest resolution that preserves the intended sky/lighting role on target devices.

## API use
Poly Haven maintains a public API at `https://api.polyhaven.com` with endpoints for assets, categories and metadata. Use the API to build deterministic source manifests rather than scraping website pages. Respect the API terms and send an identifying User-Agent where required by the API documentation/tooling.

## Runtime promotion gate
An asset cannot move from source/staging to Arcont runtime until:
- source/license recorded;
- scale/pivot checked;
- material channels verified;
- texture budget set;
- collision role decided;
- LOD/HLOD strategy assigned;
- visual comparison captured;
- Android performance impact measured if it will be repeated at scale.

## Primary references
- Poly Haven license: https://polyhaven.com/license
- Poly Haven site/library: https://polyhaven.com/
- Poly Haven API announcement (2026-07-18): https://polyhaven.com/our-api
- Poly Haven public API specification repository: https://github.com/Poly-Haven/Public-API

## Arcont decision
Poly Haven remains approved as a CC0 source. High source fidelity is preserved in staging/reference; runtime receives optimized derivatives only.