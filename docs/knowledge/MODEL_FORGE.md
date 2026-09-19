# ARCONT Model Forge v0.1

Model Forge turns catalogued 3D assets into reproducible, game-consumable candidates without making the Asset Vault a binary dump.

## First objective

Materialize legally reusable 3D environment assets already indexed by ARCONT, beginning with CC0 sources, then normalize and validate them for Godot/Close Seal.

Pipeline:

ASSET VAULT RECORD -> LICENSE GATE -> SOURCE FETCH -> HASH -> EXTRACT -> 3D INVENTORY -> NORMALIZATION PLAN -> GAME STAGING -> GODOT IMPORT/RUNTIME EVIDENCE

## Rules

- The Asset Vault record remains provenance metadata.
- Never download an asset whose exact license gate fails.
- Prefer CC0 for automatic materialization.
- Downloaded archives and generated binaries are workflow artifacts by default, not committed to ARCONT.
- Record hashes for reproducibility.
- Maps reference semantic asset IDs, not filenames.
- Render collision, navigation and gameplay semantics remain independent from visual geometry.
- A successful download/import is not evidence of acceptable runtime performance.

## Close Seal environment seed set

The first materialization campaign targets environment construction rather than hero generation:
- Kenney Castle Kit
- Kenney Fantasy Town Kit
- compatible CC0 Poly Haven models/materials selected through Asset Vault queries

These assets can cover walls, towers, gates, town modules, props and environmental dressing while original art remains reserved for identity-critical units and structures.

## Provider architecture

Model Forge providers expose:
- resolve(record)
- license_gate(record)
- fetch(record)
- inventory(workspace)
- normalize(workspace)
- manifest(workspace)

v0.1 implements a conservative direct-download materializer. Provider-specific resolvers can be added without changing the game-facing semantic IDs.
