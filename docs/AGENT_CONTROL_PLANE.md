# ARCONT Agent Control Plane v1

ARCONT already contains validators, evidence tooling, Asset Vault checks and external runtime contracts. The missing layer was a stable machine-readable surface that an AI agent can query before deciding which tool to use.

`tools/arcont_agent.py` is that surface. It is deliberately conservative: ARCONT itself remains read-only to the control plane, production games stay external, project mutation requires an explicit opt-in on every invocation, and the external Runtime Lab is never executed silently.

## Goals

1. Give an agent one deterministic entry point for capability discovery.
2. Make repository guards explicit in every discovery response.
3. Run a bounded `doctor` over whitelisted read-only checks.
4. Inspect an external game repository without modifying it.
5. Invoke registered external-project authoring tools only with explicit write permission.
6. Keep runtime execution and production game code outside ARCONT.

The registry lives in `agent.capabilities.json` and is described by `schemas/agent-capability-registry.schema.json`.

## Discover capabilities

```bash
python tools/arcont_agent.py capabilities
```

The response is JSON and includes the ARCONT protocol/schema version, repository guards, capability IDs, availability, access mode, and whether a capability participates in `doctor`.

## Run the bounded doctor

```bash
python tools/arcont_agent.py doctor
```

`doctor` executes only registry entries that are both `doctor: true` and `access: read-only`. Each check has a timeout and returns a normalized record with exit status plus parsed JSON or bounded text output.

Capabilities marked `external-project-write` or `external-runtime` are never executed by `doctor`.

## Inspect an external project

```bash
python tools/arcont_agent.py inspect-project ../MyGame
```

The inspection is static and read-only. It detects common engine markers, counts source/assets/scenes/resources, summarizes extensions and top-level directories, skips symlinks and common generated/cache directories, and caps the number of observed files.

The result explicitly states its limits: it does **not** prove scene quality, animation quality, correctness, performance, rendering quality or AAA presentation.

## Invoke authoring and Map Forge

The control plane can now invoke two registered external-project writers: `godot.authoring.control` and `map-forge.editor.control`. Requests use the same versioned JSON contracts as the underlying tools.

```bash
python tools/arcont_agent.py invoke godot.authoring.control \
  --project ../MyGame \
  --request request.json \
  --allow-project-write

python tools/arcont_agent.py invoke map-forge.editor.control \
  --project ../MyGame \
  --request map-request.json \
  --allow-project-write
```

The permission flag is mandatory even for a request that intends to be a dry run, because initializing an external authoring adapter may touch project-owned control state. The wrapper rejects ARCONT itself and any project embedded below the ARCONT repository root.

Godot authoring exposes revisioned `capabilities / discover / list / inspect / create / replace / patch / restore / build / playtest`. Playtest reopens an accepted scene bundle and runs a bounded project-owned input/observation session. Map Forge exposes revisioned map inspection/editing, explicit terrain brushes, validation, materialization and capture.

The MCP transport is also registered as `godot.authoring.mcp`, but it is not routed through one-shot `invoke`; it is a persistent stdio server and must be connected by an MCP client.

## Architecture boundary

The control plane does not change ARCONT's canonical rule:

- `production_game_code_allowed = false`
- `embedded_godot_project_allowed = false`

Game-owned adapters, scenes, gameplay, animation state machines and rendered evidence stay in the game repository. Runtime experiments stay in the external ARCONT Runtime Lab. ARCONT owns contracts, validation, evidence, reusable knowledge and agent-facing capability metadata.

## Extension path

Future capabilities should enter the registry only when their implementation and dependency closure are present on the same branch. The control plane must never advertise an unavailable writer. Production-toolchain, animation/audio review and native scene publication remain separate follow-up gates until their dependency/hash contracts are rebased onto the current canonical branch.
