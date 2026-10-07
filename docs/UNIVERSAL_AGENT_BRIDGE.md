# ARCONT Universal Agent Bridge v1

The Universal Agent Bridge is the stable front door for an external AI agent.

Its purpose is not to replace ARCONT's internal authoring tools. It prevents an
agent from needing to know those implementation details before it can understand
and operate an external game project.

## Design goal

A fresh compatible agent should be able to:

1. discover ARCONT and its safety boundary;
2. inspect an external project;
3. bootstrap a new external Godot project when explicitly authorized;
4. read persistent project intent owned by the project;
5. inspect/stage local user-provided assets with declared provenance;
6. discover and read allowlisted authoring recipes/scenarios;
7. submit a model-authored hypothesis through the existing safety gate;
8. execute an existing bounded ARCONT plan;
9. receive normal ARCONT evidence and receipts.

The bridge uses one-request JSON over stdin/stdout. MCP, HTTP, local sockets or
provider-specific adapters can wrap this protocol later without duplicating
ARCONT's execution/security logic.

## Invocation

```bash
python tools/arcont_bridge.py \
  --project /path/to/external/game \
  --request bridge-request.json
```

A write-capable plan additionally requires:

```bash
python tools/arcont_bridge.py \
  --project /path/to/external/game \
  --request bridge-request.json \
  --allow-project-write
```

The flag does not itself authorize a mutation. The embedded
`arcont-agent-plan` must also declare `permissions.project_write=true`, use a
registered invocable writer, remain inside its capability allowlist and satisfy
all ordinary revision/expectation checks.

## Request envelope

```json
{
  "protocol": "arcont-bridge",
  "version": 1,
  "request_id": "agent-001",
  "operation": "discover",
  "arguments": {}
}
```

The request schema lives at
`schemas/agent-bridge-request.schema.json`.

## Operations

### `discover`

Returns the bridge protocol, available bridge operations, mutation boundary,
external project root and the ordinary ARCONT capability snapshot. This is the
recommended first call for an agent that has no prior ARCONT context.

### `project.inspect`

Runs ARCONT's existing static project inspection. It detects the engine and
summarizes code/assets/scenes/resources without modifying the game.

### `project.intent.read`

Reads `project.intent.json` from the external project root. Missing intent is
reported explicitly; ARCONT does not invent product requirements from chat
memory.

The persistent intent contract is
`schemas/project-intent.schema.json`.

### `project.bootstrap`

Creates a minimal Godot 2D or 3D project in an existing empty external
directory. It requires explicit project-write opt-in and a validated persistent
project intent. The detailed contract lives in
`PROJECT_BOOTSTRAP_ASSET_INTAKE.md`.

### `assets.inspect`

Inventories local project assets with relative path, type, extension, byte size
and bounded SHA-256 hashing. It does not download assets and does not infer
copyright or license rights from file contents.

Public asset discovery remains a future bridge operation. Asset Vault remains
the trust/provenance layer for public sources.

### `asset.user.inspect / asset.user.stage / asset.user.list`

User-supplied files are accepted only below `incoming/`. Inspection is
read-only. Staging requires explicit project-write opt-in, copies the file into
a type-specific `assets/user/` location, hashes it and records the user's
rights declaration below `.arcont/assets/user/`. ARCONT does not infer or
independently verify ownership/license rights.

V1 rejects archive extraction and network download.

### `asset.public.providers / asset.public.search / asset.public.files / asset.public.stage / asset.public.list`

Public assets use explicit provider adapters rather than arbitrary URLs. V1
supports the Poly Haven official API. Search and file-manifest discovery are
read-only but require project policy to allow public/network assets. Staging
requires explicit project-write opt-in and a `manifest_sha256` returned by
`asset.public.files`.

The live file manifest is re-fetched before staging. Any change invalidates the
selection. Download hosts and redirects are allowlisted, provider MD5/size are
verified when available, and ARCONT computes SHA-256 plus a persistent
provenance record. API attribution requirements are kept separate from the
asset's CC0 attribution requirements.

See `PUBLIC_ASSET_DISCOVERY.md`.

### `authoring.catalog`

Discovers project-owned JSON documents under the allowlisted
`authoring/recipes` and `authoring/scenarios` roots. It returns path, kind,
size, parse status and lightweight metadata such as `id`/version when present.
It also reports whether the normal Godot/Map Forge authoring contracts exist.

### `authoring.document.read`

Reads one JSON document from those allowlisted authoring roots. Parent traversal,
symlinks, non-JSON files and oversized documents are rejected. This gives a
fresh agent the recipe/scenario content needed to construct a normal bounded
plan without exposing arbitrary project files.

### `hypothesis.evaluate`

Routes a model-authored hypothesis and structured evidence through the existing
Hypothesis Gate. It adds no repair primitive and performs no mutation.

### `plan.execute`

Routes a normal `arcont-agent-plan` through the existing bounded execution
loop. The bridge does not create a second execution engine.

## Project intent

A project's intent belongs in the game repository, not in a specific chat:

```json
{
  "protocol": "arcont-project-intent",
  "version": 1,
  "project_id": "example",
  "title": "Example",
  "genre": "third-person shooter",
  "targets": ["Android", "Windows"],
  "visual_style": "dark realistic urban",
  "priorities": ["movement", "combat", "performance"],
  "performance": {"target_fps": 60},
  "asset_policy": {
    "user_assets": true,
    "public_assets": true,
    "commercial_use_required": true,
    "allow_network_discovery": false
  }
}
```

This is deliberately product intent, not an implementation plan. An agent may
use it when planning work, but technical claims still require evidence.

## Safety boundary

Bridge v1 does **not**:

- execute arbitrary shell commands;
- let the bridge invent arbitrary writer capabilities;
- weaken revision checking;
- permit silent mutation retries;
- infer a missing project goal;
- download from arbitrary public URLs or unsupported providers;
- extract user/public archives;
- infer asset license rights;
- embed a production game in ARCONT.

The bridge is a common doorway to the control plane, not a bypass around it.

## Extension path

The next bridge capabilities should be added only when backed by tested ARCONT
subsystems. Planned directions include project bootstrapping, user asset intake,
license-aware public asset discovery, structured code edits, visual/feel
evidence and provider-specific MCP/HTTP adapters.
