# Realistic Asset Warehouse tooling

This directory is Arcont's research/reference acquisition layer. It must never silently promote downloaded content into the playable runtime.

## Current components
- `fetch_polyhaven.py` — live Poly Haven cataloger/downloader using the official public API. It records source metadata, CC0 provenance, canonical URLs, download file keys, MD5 verification supplied by the provider, local SHA-256, and acquisition status.
- `arcont_profile.json` — broad realistic discovery vocabulary and runtime promotion gates.
- `sources.json` — provider registry and automation trust state.
- `.github/workflows/asset-warehouse-sync.yml` — manual catalog/download job that stores the result as a GitHub Actions artifact instead of bloating normal Git history.

## Preferred providers
1. Poly Haven (CC0): models, textures, HDRIs. Automated now.
2. ambientCG (CC0): PBR materials, HDRIs and selected 3D assets. Kept as a preferred source, but automation stays disabled until a current official machine-readable API contract is verified in-repo.
3. Existing verified Arcont CC0 sources such as Kenney and Quaternius packs.
4. Per-asset sources only after explicit license/provenance review; never bulk-ingest ambiguous content.

## Acquisition flow
`discover -> license gate -> metadata -> download master -> checksum -> inspect -> catalog -> candidate -> optimize -> runtime promotion`

## Operational examples
Catalog every Poly Haven asset matching Arcont's broad realism profile:

```bash
python tools/asset_warehouse/fetch_polyhaven.py --out warehouse/polyhaven --limit 0
```

Download representative 4K/master-family files with a 20 GiB run cap:

```bash
python tools/asset_warehouse/fetch_polyhaven.py --out warehouse/polyhaven --download --resolution 4k --file-mode representative --limit 0 --max-total-gb 20
```

For a deliberately huge archival batch, raise `--max-total-gb`; do it in separate Actions runs/artifacts rather than committing binary masters to ordinary Git history.

## Repository hygiene
The warehouse is intentionally broad; runtime is intentionally narrow. Large binary masters belong in ephemeral Actions artifacts, Git LFS, releases, object storage, or another dedicated archive if persistence is required. Research branches should keep acquisition code, manifests, provenance, indexes and selected intentionally-versioned source files.

## Arcont selection profile
Prioritize photorealistic forest/rural/industrial assets: terrain, rocks, vegetation, deadwood, wet surfaces, architecture, interior shells, concrete/brick/plaster/roofing, infrastructure, machinery, utility props, clutter, debris, decals and HDRIs. Keep many variants in the warehouse. Mobile budgets and duplication limits apply only when promoting a derivative into runtime.

## Poly Haven API contract used
The collector uses `GET https://api.polyhaven.com/assets` for asset discovery and `GET https://api.polyhaven.com/files/{id}` for downloadable files. Requests send a unique Arcont User-Agent. Poly Haven assets are treated as CC0; API-service attribution/provenance is retained separately from the asset license.
