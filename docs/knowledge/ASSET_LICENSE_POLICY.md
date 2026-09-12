# ARCONT Asset Vault — License Safety Policy

Status: canonical policy for automatic asset ingestion.

## Goal

ARCONT catalogs game-development resources for reuse across engines and platforms. A license being open does not mean it is frictionless for every commercial distribution target. The vault therefore separates factual license metadata from ARCONT's operational ingestion policy.

## Tiers

### GREEN

Default automatic ingestion is allowed only when the source page itself verifies a license that is portable for ordinary commercial use without attribution, share-alike, source-release, or known DRM obligations.

Current GREEN classes:

- CC0 1.0
- explicitly verified Public Domain

GREEN does not mean the asset binary is mirrored. Metadata-only indexing remains the default.

### CONDITIONAL

The work can be useful, but project-specific obligations exist. It is not automatically promoted into the canonical cross-platform-safe pool.

Current CONDITIONAL classes:

- CC-BY 3.0
- CC-BY 4.0
- OGA-BY 3.0

Typical obligations include attribution and distribution-term review. A future project may opt in only after recording the exact target platform, packaging model, attribution mechanism, and legal/source review.

### RESTRICTED

The license creates share-alike, copyleft, DRM, or other obligations that are inappropriate for blind reuse in a general-purpose commercial asset bank.

Current RESTRICTED classes:

- CC-BY-SA 3.0
- CC-BY-SA 4.0
- GPL 2.0
- GPL 3.0

Restricted does not mean forbidden forever. It means ARCONT will not automatically present the asset as drop-in safe.

## Unknown licenses

Unknown text is never guessed. If an adapter cannot normalize a license, the asset is skipped and the reason is recorded in the sync log.

## Source verification

A discovery list, search result, collection, or external claim is not sufficient evidence. Adapters must fetch the individual official asset page at sync time and classify the license declared there.

If the individual page changes license or stops exposing a resolvable license, automatic ingestion stops.

## Platform portability

`commercial_use=true` is not equivalent to `portable_commercial_default=true`. An asset can permit commercial use while still requiring attribution, share-alike, source release, or terms that interact with DRM/platform distribution.

The Asset Vault preserves those concepts separately.

## Mirroring

License classification alone never implies that ARCONT should download or mirror the binary. `archive.mirrored_in_arcont` remains false unless redistribution rights, storage policy, provenance, and binary integrity are all explicitly satisfied.

## Implementation

- Policy engine: `tools/license_policy.py`
- Record schema: `schemas/asset-record.schema.json`
- OpenGameArt adapter: `tools/opengameart_adapter.py`
- Discovery seeds: `assets/sources/opengameart-seeds.json`
- Tests: `tests/test_license_policy.py`

## Current OpenGameArt rule

OpenGameArt is treated as a mixed-license source. The default adapter only writes GREEN records. CC-BY, CC-BY-SA, OGA-BY, GPL, and unknown licenses are not silently promoted into the safe pool.
