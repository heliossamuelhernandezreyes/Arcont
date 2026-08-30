# Realistic Asset Warehouse tooling

This directory defines acquisition tooling for research/reference storage. It must not silently promote downloaded content into the playable runtime.

## Preferred providers
1. Poly Haven (CC0): models, textures, HDRIs.
2. ambientCG (CC0): PBR materials, HDRIs and selected 3D assets.
3. Existing verified Arcont CC0 sources.

## Planned acquisition flow
`discover -> license gate -> metadata -> download master -> SHA256 -> inspect -> catalog -> candidate -> optimize -> runtime promotion`

## Safety / repository hygiene
Large binary masters should not be blindly committed into ordinary Git history. Prefer an external/LFS/release-backed warehouse when bulk acquisition becomes large. The research branch should keep manifests, provenance, acquisition recipes, previews where appropriate, and selected masters that are intentionally versioned.

## Selection profile for Arcont
Prioritize photorealistic forest/rural/industrial assets: ground, rocks, vegetation, wood, brick, concrete, plaster, roofing, damaged architecture, fences, utility props, clutter, debris, HDRIs, and material calibration assets.

Keep multiple variants in the warehouse. Runtime promotion is where duplication and mobile budgets are enforced.
