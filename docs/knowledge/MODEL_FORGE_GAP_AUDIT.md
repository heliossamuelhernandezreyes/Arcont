# ARCONT Model Forge — Gap Audit

Date: 2026-09-19
Scope: main branch before Model Forge implementation

## Finding

ARCONT already had most of the **control-plane architecture** needed for a 3D production pipeline. It did not yet have a complete **binary transformation pipeline**.

The correct next step is therefore not to create a second Asset Vault or a second Map Forge. Model Forge should be a thin execution layer that reuses both.

## Existing capabilities — reuse, do not duplicate

### Asset Vault
Already canonical:
- provider/source identity
- exact asset-level licensing metadata
- commercial/modification/redistribution gates
- archive/mirroring policy
- SHA-256 field for archived binaries
- normalized catalog and index
- provider adapters and metadata sync
- query filters
- compatibility metadata and evidence strength
- deduplication
- CI integrity/negative controls

Canonical files:
- docs/assets/ASSET_VAULT.md
- docs/assets/INDEXER_SPEC.md
- schemas/asset-record.schema.json
- tools/asset_vault_indexer.py
- tools/asset_vault_bulk_sync.py
- .github/workflows/asset-vault-sync.yml

### Map Forge
Already canonical:
- semantic map contract
- replaceable provider architecture
- provider probe/materialize/refresh/validate/manifest pattern
- separation of gameplay semantics from visual providers
- game-owned runtime bridge
- terrain/structure/scatter/import/navigation roles

Canonical file:
- docs/knowledge/MAP_FORGE_STANDARD.md

### Graphics / runtime knowledge
Already documented:
- draw-call/material/instance concerns
- LOD/HLOD as independent study dimensions
- texture residency/streaming
- KTX2/Basis evaluation
- mobile/runtime evidence requirement
- Godot source/evidence framework

## What was NOT implemented on main

The audit found no canonical executable pipeline that performs all of these operations on downloaded 3D binaries:

1. resolve a catalog record to a verified downloadable binary;
2. acquire it reproducibly and preserve the binary hash;
3. inspect actual mesh/material/texture/animation contents;
4. normalize axes, units, pivots and naming;
5. convert supported source formats to canonical glTF/GLB;
6. generate or validate render LODs;
7. generate simplified collision geometry;
8. optimize/convert texture delivery;
9. validate triangle/material/texture budgets against an asset class;
10. stage the result into a game-facing semantic asset ID;
11. import it into Godot and record runtime evidence;
12. render/capture the asset from the actual target-game camera.

Asset Vault describes and indexes. Map Forge projects semantic maps. Graphics docs describe what must be measured. None of them replaces this execution layer.

## Assessment of PR #13

PR #13 should be treated as **Stage 0 / acquisition prototype**, not as a new subsystem replacing existing ARCONT facilities.

Useful new behavior:
- acquire a specifically selected binary;
- hash the acquired bytes;
- unpack an archive;
- inventory known 3D file extensions;
- retain the result as an ephemeral CI artifact.

Overlap to avoid:
- license policy must call/reuse Asset Vault policy rather than invent a second policy;
- provenance should update/emit data compatible with the canonical asset record;
- provider discovery belongs to Asset Vault adapters;
- semantic placement belongs to Map Forge/game bridges.

## Minimal Model Forge architecture

MODEL FORGE SHOULD BE:

Asset Vault
  -> Acquisition Adapter
  -> Binary Inspector
  -> Normalizer/Converter
  -> LOD + Collision + Texture processors
  -> Production Validator
  -> Game Stager
  -> Godot Runtime Evidence

It should NOT own:
- source discovery/catalog indexing;
- canonical license policy;
- map semantics;
- gameplay semantics;
- a duplicate asset database.

## Implementation order

P0 — refactor Stage 0 to consume canonical Asset Vault trust/license validation.

P1 — binary inspector: format, meshes, triangles, materials, textures, skeleton, animations, bounds.

P2 — canonical GLB normalization: scale, axes, pivots, naming and deterministic manifest.

P3 — LOD and collision processing with explicit quality/budget evidence.

P4 — texture pipeline and mobile delivery experiments.

P5 — Close Seal staging bridge: semantic ID -> visual asset, without moving gameplay semantics into ARCONT.

P6 — Godot import + tactical-camera screenshot + runtime/performance evidence.

## Decision

Do not build a Tripo clone yet.

First make the existing Asset Vault assets executable through the missing transformation stages. Generative providers can later plug into the same acquisition boundary and therefore inherit the same normalization, validation and runtime gates.
