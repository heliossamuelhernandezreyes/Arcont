# ARCONT Map Forge Standard

**Status:** reusable engineering standard derived from observed production work  
**Maturity:** L3 for the architecture pattern; reusable contract/template are normative ARCONT artifacts, not runtime evidence  
**First observed implementation:** `heliossamuelhernandezreyes/Closeseal`

## Purpose

Map Forge is an ARCONT-standardized map-authoring architecture for games that need a stable semantic map model while remaining free to change engines, editor plugins, terrain systems, structure tools, scatter systems, navigation backends or import pipelines.

The standard is intentionally **not a Godot project** and **not production game code**. ARCONT keeps the portable contract, validation rules, evidence, provider registry and integration guidance. A production game owns its editor implementation and runtime bridge in its own repository.

## Core rule

> Gameplay semantics belong to the game-owned canonical map contract. Authoring providers are replaceable projections of that contract.

```text
                 GAME-OWNED SEMANTIC CONTRACT
                           │
              anchors / routes / regions
                           │
         ┌─────────────────┼─────────────────┐
         ↓                 ↓                 ↓
      Terrain          Structures          Scatter
      adapter           adapter            adapter
         │                 │                 │
         └──────── generated authoring workspace ────────┐
                                                         ↓
                                                   engine/runtime
```

## Portable contract

ARCONT defines the generic schema in:

- `schemas/map-authoring-contract.schema.json`
- `templates/map-forge/map_contract.example.json`
- `tools/map_forge_contract.py`

The generic contract uses seven top-level concepts:

1. `version` — contract version.
2. `id` — stable map identifier.
3. `bounds` — semantic world envelope.
4. `anchors` — point-like semantic objects such as spawns, objectives, bases, portals, checkpoints or resource nodes.
5. `routes` — ordered paths with widths and game-defined roles.
6. `regions` — areas such as chokepoints, formation spaces, hazards, cover, capture zones, encounter rooms or biome volumes.
7. `authoring` — provider-neutral hints and optional provider assignments.

Games MAY add extra fields. The generic schema intentionally allows extension because ARCONT should not force RTS-specific semantics onto other genres.

## Why `anchors` instead of Close Seal's `bases/objectives`

Close Seal's first implementation proved the architecture with RTS-specific collections (`bases`, `objectives`, `routes`, `regions`). The ARCONT standard generalizes point-like objects into `anchors` so the same model can serve:

- RTS maps;
- action RPG encounter spaces;
- shooters;
- racing/checkpoint layouts;
- extraction games;
- tower defense;
- survival worlds;
- puzzle levels;
- open-world subregions.

A game-specific adapter may expose convenience collections internally, but interoperability should map those concepts into the generic semantic categories.

## Provider roles

ARCONT recognizes provider **roles**, not permanent product names:

| Role | Responsibility | Current observed Godot candidate |
|---|---|---|
| Terrain | terrain surface / height / painting / terrain data | Terrain3D |
| Structures | blockout, walls, rooms, bridges, fortifications | Cyclops Level Builder |
| Scatter | foliage, rocks, props, biome population | ProtonScatter |
| Import | external level-format interchange | FuncGodot |
| Navigation | walkability/bake/query layer | engine-specific |
| Runtime | game-specific materialization | game-owned |

Products may be replaced without changing the semantic contract.

## Adapter contract

A provider adapter SHOULD expose these conceptual operations even if its engine API differs:

```text
probe()                     -> availability/capabilities
materialize(contract)       -> generated provider workspace
refresh(contract, workspace)-> update generated projection
validate(workspace)         -> provider-specific errors/warnings
manifest()                  -> exact provider/version/provenance
```

Adapters MUST NOT silently rewrite gameplay semantics as a side effect of generating provider data.

Two-way editing is permitted only when round-trip behavior is explicit, conflict-aware and tested. Until then, semantic contract → provider workspace is the safe canonical direction.

## Generated-workspace rule

Generated provider data is derivative.

A production implementation SHOULD separate:

```text
maps/
  canonical-map.json        <- source of truth

maps/generated/
  authoring-scene           <- disposable / reproducible projection
  provider-data/            <- provider-specific generated state
  manifest.json             <- generation/provenance record
```

Provider data may become hand-authored after generation, but the project must then explicitly document ownership and round-trip semantics. ARCONT does not assume that arbitrary provider edits can be reconstructed from the canonical contract.

## Validation layers

A mature implementation should use independent gates:

### Layer A — semantic contract

Validate JSON/schema and cross-object constraints without opening the engine.

ARCONT provides:

```bash
python tools/map_forge_contract.py templates/map-forge/map_contract.example.json
```

### Layer B — editor/provider import

Install exact provider revisions and verify a clean editor startup.

### Layer C — physical materialization

Build the generated authoring workspace and assert that required provider roles materialized successfully.

### Layer D — runtime bridge

Verify that the playable game consumes the same canonical semantic data rather than duplicate hardcoded coordinates.

### Layer E — gameplay evidence

Navigation, balance, performance, multiplayer fairness, formation fit or encounter quality require runtime experiments/playtests. Editor success is not evidence for these claims.

## First observed production implementation

Close Seal implemented and validated the pattern through its Map Forge 0.4 provider bridge.

Observed pipeline:

```text
Close Seal canonical map JSON
        ↓
Map Forge editor
        ↓
provider bridge
        ├─ Terrain3D node
        ├─ Cyclops workspace + structural guides
        ├─ ProtonScatter node + semantic scatter shapes
        ├─ FuncGodot import socket
        ├─ gameplay guides
        └─ navigation guides
        ↓
generated PackedScene + manifest
```

The physical-provider CI at Close Seal commit `cf3b4e09809d4f2d793b30f7bd2367fbcd9174b2` completed successfully under Godot `4.7.2-stable` on GitHub Actions Linux. The provider workflow was run `34747206030`.

This observation establishes that the specific pinned provider set could be installed and materialized in that environment. It does **not** prove Android performance, universal provider interoperability, navigation correctness, multiplayer balance or cross-engine portability.

## Adoption recipe for a new game

1. Copy the semantic schema concepts, not Close Seal gameplay fields.
2. Create a game-owned map JSON format compatible with or transformable to the ARCONT contract.
3. Add fast independent validation in CI.
4. Choose provider roles required by the game.
5. Pin exact provider versions/revisions and licenses.
6. Implement adapters in the production repository.
7. Generate provider workspace into a clearly derived location.
8. Make runtime consume canonical semantics.
9. Add provider/materialization smoke tests.
10. Use Runtime Lab for claims that require actual execution/performance evidence.

## Genre profiles

Map Forge should be specialized by profile rather than forked into unrelated architectures.

### RTS / tactics

Useful semantics: bases, lanes, flanks, chokepoints, formation spaces, creep/resource zones, objectives, tower coverage.

### Shooter / action

Useful semantics: spawn anchors, encounter regions, cover volumes, sightline corridors, traversal routes, extraction/objective anchors.

### Racing

Useful semantics: spline routes, checkpoints, track widths, overtake regions, hazard zones, pit/service anchors.

### RPG / open world

Useful semantics: encounter regions, settlements, travel routes, biome zones, quest anchors, streaming cells, traversal constraints.

## Boundaries

ARCONT Map Forge is not:

- a production game editor embedded inside ARCONT;
- a replacement for engine-native terrain or navigation systems;
- a promise of automatic round-trip editing;
- a universal map-balance oracle;
- evidence that any specific provider is optimal.

It is a reusable architecture and contract for keeping semantic map ownership stable while toolchains evolve.
