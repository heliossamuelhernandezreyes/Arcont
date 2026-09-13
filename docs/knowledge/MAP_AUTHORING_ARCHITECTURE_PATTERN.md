# Map Authoring Architecture Pattern

**ID:** `ARC-PATTERN-MAP-AUTHORING-0001`  
**Status:** observed architecture pattern  
**Maturity:** L3 — observed in one production repository / one validated engine environment  
**Observed:** 2026-09-13

## Problem

A production game needs powerful terrain, blockout, scatter and import tools without allowing any one editor addon to become the owner of gameplay semantics or the permanent storage format of the game map.

Tightly coupling bases, objectives, routes, chokepoints, spawns or tactical regions to a third-party addon creates migration risk, version lock-in, difficult source control and unclear ownership of gameplay-critical data.

## Pattern

Use a **game-owned canonical semantic map contract** as the stable layer, and treat editor addons as replaceable authoring providers.

```text
                     GAME-OWNED MAP CONTRACT
                              │
             gameplay topology / semantics
                              │
      ┌───────────────┬───────┴────────┬───────────────┐
      ↓               ↓                ↓               ↓
   Terrain         Structures        Scatter        Import
   provider         provider         provider        provider
      │               │                │               │
      └──────────── optional / replaceable adapters ──┘
```

The canonical contract owns concepts such as:

- map bounds
- teams and bases
- hero/unit spawns
- objectives
- routes and route widths
- tactical regions
- chokepoints
- gameplay metadata

Provider-specific terrain meshes, brush data, scatter graphs or external import files must not be required to understand the gameplay topology.

## Reference implementation observed

The pattern was exercised in the Close Seal production repository on branch `art/first-visual-pass` at commit:

`072bdfb0d4f2c07f467d044bb2354b50f5d158af`

Reference components:

- `src/map/map_contract.gd` — canonical game-owned contract and structural validation.
- `src/map/map_analyzer.gd` — derived tactical metrics and heuristic warnings.
- `addons/close_seal_map_forge/map_forge_plugin.gd` — editor workspace.
- `addons/close_seal_map_forge/map_forge_canvas.gd` — provider-neutral tactical topology canvas.
- `tools/validate_maps.py` — editor-independent repository validator.
- `.github/workflows/map-contract-integrity.yml` — canonical map CI gate.
- `.github/workflows/map-authoring-providers.yml` — exact-provider Godot editor validation.

The reference workspace is versioned as **Map Forge 0.2.0**.

## Provider model observed

The validated authoring provider set was:

| Role | Provider | Integration role |
|---|---|---|
| Terrain | Terrain3D | terrain authoring / rendering provider |
| Structures | Cyclops Level Builder | structural blockout / brush geometry |
| Scatter | ProtonScatter | procedural environment population |
| Import | FuncGodot | external brush-map interchange |

These providers are optional from the perspective of the canonical map contract. Their exact upstream revisions and licensing are tracked separately in `MAP_AUTHORING_TOOLCHAIN.yaml`.

## Validation layers

### 1. Static contract validation

Map data is validated without launching the game engine. This catches malformed JSON, missing required fields, invalid route/region types, duplicate IDs, non-positive widths/bounds, invalid points and structurally incomplete maps.

This layer is fast and suitable for every pull request.

### 2. Editor integration validation

The exact authoring providers are installed, then the pinned Godot editor is launched twice:

1. first import pass;
2. second clean editor startup after imports exist.

The second pass is the meaningful clean-start assertion because asset import and editor plugin registration can create transient first-import conditions.

### 3. Production project regression validation

The production project still runs its own project-integrity checks and real render/screenshot validation. A map-editor change must not silently break the playable project.

## Observed evidence

Environment:

- Godot `4.7.2-stable`
- canonical engine commit `ed1daf0bf001b61586d9930840f2f1394092c079`
- GitHub Actions Linux runner
- Close Seal commit `072bdfb0d4f2c07f467d044bb2354b50f5d158af`

Successful Close Seal workflows at that revision:

- `Map Authoring Providers` — run `34742577350` — success
- `Map Contract Integrity` — run `34742577353` — success
- `Closeseal Project Integrity` — run `34742577312` — success
- `Real Prototype Screenshot` — run `34742577276` — success

The provider workflow demonstrated that the pinned provider set installs and survives a clean second editor startup in the observed environment.

## Useful failure observed during validation

An early Map Forge analyzer implementation failed under Godot strict warnings because numeric values derived from `Variant` dictionaries were inferred as `Variant`.

The production fix was to make derived numeric state explicit (`float`, `Vector3`, typed dictionaries/arrays where appropriate) and use typed numeric helpers such as `maxf`, `minf`, `absf` and `clampf`.

This is an example of why the editor integration gate is required even when independent static validation succeeds.

## Tactical canvas

The reference editor includes a provider-neutral 2D tactical topology view capable of displaying:

- map bounds
- bases
- hero spawns
- objectives
- routes
- route widths
- regions
- chokepoints

It supports zoom, pan and feature selection. Because it consumes only the canonical map contract, it remains useful even if every third-party authoring provider is replaced.

## Analyzer boundary

The reference analyzer derives values such as:

- base separation
- map area
- route lengths
- north/south flank length delta
- objective-distance balance
- choke widths
- route symmetry score

These values are **engineering signals, not validated gameplay-balance truths**.

A threshold such as an 8% flank-length warning is a design heuristic until correlated with gameplay experiments, simulation or playtest evidence. ARCONT must not promote such thresholds into universal rules without additional evidence.

## Design rules supported by the observation

Within the observed scope, the following practices worked:

1. Keep gameplay topology in a game-owned, source-control-friendly format.
2. Make provider-specific data optional from the canonical gameplay layer.
3. Keep a native/fallback authoring path.
4. Validate canonical map data independently of the editor.
5. Validate editor addons with the exact engine revision used by production.
6. Include a second clean editor startup after first import.
7. Keep tactical visualization dependent on semantic map data rather than provider internals.
8. Treat balance analyzers as heuristics until runtime/playtest evidence exists.
9. Preserve exact provider revisions and license provenance separately from production map data.

## What this evidence does NOT establish

This observation does not prove:

- Android runtime performance of Terrain3D, Cyclops or ProtonScatter;
- production-scale navigation interoperability;
- acceptable memory/draw-call budgets on target mobile devices;
- optimal map dimensions, route widths or choke widths;
- multiplayer balance;
- universal compatibility across future Godot versions;
- that this provider set is superior to every alternative toolchain.

Those claims require separate experiments and evidence.

## Promotion path

To advance beyond L3:

- reproduce the workflow on target Android hardware/export paths;
- benchmark terrain/scatter density and memory cost;
- validate navigation bake interoperability;
- test map round-tripping and source-control behavior across multiple real maps;
- correlate analyzer metrics with simulation/playtest outcomes;
- reproduce the architecture in another game or engine version without semantic lock-in.
