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

## Production and Model Forge control

The same permissioned `invoke` surface now exposes `production.control` and `model-forge.control`.

`production.control` composes the reusable production gates for asset-plan validation/staging, animation profiles, tactical sectors, performance records, TPS finish review, bounded PCM audio review, and hash-verified native scene bundle publication. Only `assets.stage` and `bundle.materialize` report a project write.

`model-forge.control` intentionally exposes a smaller local surface: inspect GLTF/GLB, validate budgets, derive collision policy, and stage a local candidate. It does not expose URL download or arbitrary external processor execution.

```bash
python tools/arcont_agent.py invoke production.control \
  --project ../MyGame --request production-request.json --allow-project-write

python tools/arcont_agent.py invoke model-forge.control \
  --project ../MyGame --request model-request.json --allow-project-write
```

Technical acceptance remains separate from artistic approval, target-device performance, gameplay feel and rendered presentation.

## Bounded execution loop

`run-plan` executes a declarative plan with at most 24 steps:

```bash
python tools/arcont_agent.py run-plan \
  --project ../MyGame \
  --plan templates/agent/inspect-playtest.plan.example.json \
  --allow-project-write
```

Plans use protocol `arcont-agent-plan` version 1 and are validated against `schemas/agent-execution-plan.schema.json`. They declare a goal, an explicit capability allowlist, project-write permission, ordered steps and optional expectations.

Writer steps require **both** `permissions.project_write=true` in the plan and `--allow-project-write` on the CLI. The plan may only invoke capabilities that are both registered as `external-project-write` and `invocable:true`.

A request can consume a value from a completed prior step using:

```json
{"$from":"inspect_scene","pointer":"/result/revision"}
```

The JSON pointer is resolved only against an already completed step. Forward references are rejected. This is how a plan can carry revisions, accepted bundle directories, hashes and other evidence forward without hardcoding stale values.

Expectations are fail-closed. Operators are `exists`, `equals`, `not-equals`, `truthy` and `falsy`. If execution fails or an expectation is false, later steps are not executed.

Each receipt includes the plan SHA-256, capability-registry SHA-256, ordered step outputs, expectation results, write-step count and the failed step when applicable. The loop does not generate a new plan, execute shell commands, invoke external-runtime capabilities, or silently retry a failed mutation.

The example in `templates/agent/inspect-playtest.plan.example.json` inspects a Godot authoring document, binds its current revision and accepted bundle into a playtest request, and requires `passed=true`.

## Evidence-driven diagnosis and repair proposals

`diagnose` turns structured observations into a bounded hypothesis and, when the policy supplies one, a normal revision-checked `arcont-agent-plan`:

```bash
python tools/arcont_agent.py diagnose \
  --policy path/to/game-policy.json \
  --evidence evidence.json \
  --require-match
```

Policies use `arcont-agent-diagnosis-policy` version 1 and are described by `schemas/agent-diagnosis-policy.schema.json`. The engine is intentionally game-agnostic: game-specific knowledge lives in declarative policy/evidence files, not Python branches inside ARCONT.

Conditions can compare evidence and selected-candidate values with bounded operators. Candidate selection can filter a supplied object list and choose the unique nearest X/Z candidate to an observed position. Equal-distance ties, missing candidates and out-of-range candidates are rejected rather than guessed.

Templates may reference evidence with `{"$evidence":"/pointer"}`, the selected candidate with `{"$candidate":"/pointer"}`, and stable-ID patch targets with `{"$candidate_path":"/size/1"}`. A compiled repair plan contains an explicit capability allowlist, an inspect step and a repair step that binds `if_revision` to the inspection result.

Diagnosis is **read-only**. It never executes the proposed repair, never runs arbitrary code, and never bypasses the normal `run-plan --allow-project-write` permission boundary. If equally prioritized hypotheses match, the result is `ambiguous` and no repair plan is selected.

The generic example in `templates/agent/spatial-collider-repair.policy.example.json` shows a spatial collider diagnosis without referencing any specific game.

## Architecture boundary

The control plane does not change ARCONT's canonical rule:

- `production_game_code_allowed = false`
- `embedded_godot_project_allowed = false`

Game-owned adapters, scenes, gameplay, animation state machines and rendered evidence stay in the game repository. Runtime experiments stay in the external ARCONT Runtime Lab. ARCONT owns contracts, validation, evidence, reusable knowledge and agent-facing capability metadata.

## Extension path

Future capabilities should enter the registry only when their implementation and dependency closure are present on the same branch. The control plane must never advertise an unavailable writer. Production components are exposed individually through versioned controls rather than reviving the stale release-hash manifest from the older integration branch. Future release manifests must be regenerated from the current canonical file set.
