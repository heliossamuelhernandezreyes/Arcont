# Public Asset Discovery + Provenance v1

ARCONT Public Asset Discovery gives an external AI agent a bounded way to find
and stage public assets without accepting arbitrary URLs.

V1 supports one provider adapter:

- **Poly Haven** via its official public API.

Poly Haven assets are CC0. Its live API also requires a distinct User-Agent and
clear provider credit when the API is integrated into a product or service.
ARCONT records that distinction explicitly:

- asset license: CC0;
- asset attribution required: false;
- API attribution required: true;
- provider credit: `Poly Haven`.

Provider metadata:

```text
site:        https://polyhaven.com
api:         https://api.polyhaven.com
api terms:   https://polyhaven.com/our-api
license:     https://polyhaven.com/license
```

## Project policy gate

Network discovery is unavailable unless `project.intent.json` says:

```json
{
  "asset_policy": {
    "public_assets": true,
    "allow_network_discovery": true
  }
}
```

If `allowed_licenses` is non-empty, CC0 must be allowed. If CC0 appears in
`forbidden_licenses`, Poly Haven staging is refused.

## Bridge operations

### `asset.public.providers`

Returns supported provider policy and attribution requirements. This is local
metadata and performs no network request.

### `asset.public.search`

Queries the official provider API and returns normalized metadata.

Example:

```json
{
  "protocol": "arcont-bridge",
  "version": 1,
  "request_id": "search-industrial-001",
  "operation": "asset.public.search",
  "arguments": {
    "query": "industrial",
    "asset_type": "models",
    "limit": 10
  }
}
```

Supported type filters are `all`, `models`, `textures`, and `hdris`.

Search results include provider asset ID, name, category, tags, authors,
polycount where present, provider file hash, CC0 policy, API attribution
requirements and a SHA-256 of the observed catalog response.

### `asset.public.files`

Fetches the official file manifest for one provider asset and flattens all file
leaves to stable `file_key` values.

Example result conceptually:

```text
provider_asset_id: sunset_jhbcentral
manifest_sha256:  ...
files:
  - file_key: hdri/1k/hdr
    host: dl.polyhaven.org
    extension: .hdr
    size: ...
    md5: ...
    download_host_allowed: true
    stage_extension_allowed: true
```

The canonical SHA-256 binds the exact manifest observed by the agent.

### `asset.public.stage`

Stages one exact file from a previously observed manifest:

```json
{
  "protocol": "arcont-bridge",
  "version": 1,
  "request_id": "stage-sky-001",
  "operation": "asset.public.stage",
  "arguments": {
    "semantic_id": "industrial_sky",
    "asset_id": "sunset_jhbcentral",
    "file_key": "hdri/1k/hdr",
    "manifest_sha256": "<sha256 returned by asset.public.files>"
  }
}
```

This operation requires `--allow-project-write`.

Before downloading, ARCONT re-fetches the provider file manifest. If its
canonical SHA-256 no longer matches the agent's selected manifest, staging
fails and the agent must rediscover.

The request never accepts a download URL.

Only the exact URL associated with `file_key` in the live provider manifest is
eligible. The URL must use HTTPS and an allowlisted Poly Haven download host.
Redirects are checked again after connection and must remain on the allowlist.

The download is streamed with a hard size bound. If the provider supplies MD5
and byte size, both are verified. ARCONT additionally computes SHA-256.

No archive is extracted.

## Provenance record

A successful stage writes:

```text
assets/public/polyhaven/<semantic_id>/<provider filename>
.arcont/assets/public/<semantic_id>.asset.json
```

The provenance record includes:

- provider and provider asset ID;
- exact provider `file_key`;
- API source endpoint;
- exact download URL returned by the provider;
- file-manifest SHA-256;
- upstream MD5 and verified MD5;
- local SHA-256;
- staged byte count/path;
- CC0 license URL;
- commercial-use status;
- asset attribution requirement;
- API attribution requirement and provider credit;
- API terms URL;
- network/access/extraction state.

The canonical provenance status is:

```text
provider-api-and-download-integrity-verified
```

This means ARCONT verified the provider API path and downloaded bytes against
the provider manifest. It is not a legal warranty or a compliance-grade
provenance attestation.

## Safety boundary

V1 does not allow:

- arbitrary URL download;
- web scraping outside the official adapter;
- arbitrary provider hosts;
- HTTP downgrade;
- redirects outside the host allowlist;
- silent manifest changes;
- archive extraction;
- automatic execution of downloaded content;
- automatic license inference for unknown providers;
- staging if project asset policy disallows public/network assets.

## Extension path

Future providers must be added as explicit adapters with:

1. documented official source/API;
2. machine-readable or otherwise auditable license policy;
3. provider-specific host allowlists;
4. normalized provenance fields;
5. tests and live acceptance evidence.

Adding a source to a catalog is not sufficient to make it executable by an
agent.
