# ARCONT Asset Vault — Automatic Indexer

The Asset Vault is catalog-first. ARCONT stores structured metadata, provenance, license state, search indexes and verified hashes; large binaries are mirrored only when redistribution is explicitly permitted and useful.

## Pipeline

`SOURCE -> ADAPTER/MANIFEST -> NORMALIZED RECORD -> VALIDATION -> DEDUPLICATION -> INDEX -> QUERY`

The canonical CLI is `tools/asset_vault_indexer.py` and uses only the Python standard library.

## Commands

```bash
python tools/asset_vault_indexer.py validate
python tools/asset_vault_indexer.py build
python tools/asset_vault_indexer.py query "forest low poly" --commercial --no-attribution --android
python tools/asset_vault_indexer.py polyhaven-sync
python tools/asset_vault_indexer.py ingest-manifest path/to/provider.json --provider Kenney
```

`build` scans `assets/catalog/**/*.asset.json`, validates records, rejects duplicate ARCONT IDs, rejects duplicate provider/external identities, detects duplicate mirrored binaries by SHA-256, and writes `assets/index.json`.

## Provider strategy

### Poly Haven

Poly Haven is the first live adapter because it exposes a public API intended for programmatic asset access. The adapter uses the API rather than scraping the website, sends an ARCONT-specific User-Agent, and imports metadata only. Assets remain upstream unless later mirroring is deliberately requested.

The asset license and API-service terms are separate concepts: Poly Haven assets are CC0, while live API usage has its own attribution/User-Agent conditions. ARCONT records that distinction explicitly.

### Kenney

Catalog ingestion should use official downloadable manifests or a curated manifest generated from verified asset pages. Do not introduce an undocumented scraper simply to increase record count.

### Quaternius

Metadata may be indexed, but current redistribution restrictions mean binaries are not mirrored by default. Exact governing license must be recorded per acquisition.

### OpenGameArt / Freesound

These are mixed-license ecosystems. Automatic ingestion is allowed only when an adapter can preserve the exact asset-level license and attribution obligations. Unknown license data blocks publication into the canonical catalog.

### Sonniss

Catalog references may be indexed. Audio packs are not mirrored into ARCONT because the bundle license restricts redistribution as an asset library.

## Canonical record

Formal validation contract: `schemas/asset-record.schema.json`.

Human-readable model: `docs/assets/ASSET_SCHEMA.yaml`.

Unknown values remain `null`; they are never inferred merely from provider identity. Asset-level evidence overrides provider-level defaults.

## Deduplication

Three identities are checked:

1. ARCONT record ID.
2. `(provider, external_id)` or `(provider, asset_url)` when no external ID exists.
3. SHA-256 for binaries that are actually mirrored.

A visually similar asset is not considered a duplicate unless identity or binary evidence supports that conclusion.

## Safety and legal rules

- No silent license upgrades.
- Commercial use and redistribution are separate fields.
- `mirrored_in_arcont=true` is invalid unless `redistribution_allowed=true`.
- Attribution requirements remain machine-readable.
- Provider pages, preview renders and logos are not assumed to share an asset's license.
- Scraping is never the default when a public API or manifest exists.
- A provider adapter failing to verify license metadata should stop or emit a non-canonical staging record, not guess.

## Scale model

The Git repository is the control plane, not necessarily the binary warehouse. It can index hundreds of thousands of remote assets while keeping the canonical repository relatively small. Large legal mirrors, if created later, should use a dedicated storage layer with hashes referenced by ARCONT.

## Future adapters

Priority order:

1. Poly Haven public API — implemented.
2. Kenney verified manifest ingestion.
3. Google Fonts repository/OFL metadata.
4. CC0-only filtered audio manifests.
5. OpenGameArt and Freesound only after exact per-item license extraction is reliable.
6. Additional open repositories with stable APIs and explicit redistribution terms.
