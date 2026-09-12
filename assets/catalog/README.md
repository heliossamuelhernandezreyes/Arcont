# ARCONT Asset Vault Catalog

This directory contains normalized metadata records named `*.asset.json`.

Provider subdirectories are allowed. Large binary assets do not belong here by default.

Canonical workflow:

1. ingest through a provider adapter or verified manifest;
2. validate exact license metadata;
3. deduplicate by ARCONT ID, provider/external identity, and binary SHA-256 when mirrored;
4. build the searchable index with `python tools/asset_vault_indexer.py build`;
5. keep binaries upstream unless redistribution is explicitly allowed and mirroring has a technical reason.

The first live provider adapter is Poly Haven. Other sources use verified manifests until a stable, license-preserving API adapter exists.
