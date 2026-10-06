# ARCONT Model Forge

Status: experimental execution layer.

Model Forge turns Asset Vault records into reproducible, production-evaluable 3D candidates. It does **not** replace Asset Vault, Map Forge, the game repository, or mature geometry/texture tools.

## Architecture

ASSET VAULT
-> canonical trust/license gate
-> acquisition
-> SHA-256 provenance
-> safe unpack
-> binary inspection
-> normalization/conversion
-> glTF specification validation
-> production profile validation
-> LOD/collision processing
-> texture delivery processing
-> game staging
-> Godot import
-> target-camera/runtime evidence

## Implemented on this branch

- canonical GREEN/trust gate through `tools/license_policy.py`
- acquisition with SHA-256 and byte size
- ZIP traversal protection
- 3D source inventory
- dependency-free glTF 2.0 / GLB inspector
- production profiles and budget validator
- CLI orchestration; integrity and unit checks in GitHub Actions
- unit tests for trust gate and GLB parsing
- Close Seal environment seed manifest

## Deliberately external processors

ARCONT should orchestrate and pin mature processors rather than write fragile geometry codecs from scratch:
- Khronos glTF Validator: spec validation
- meshoptimizer/gltfpack: mesh optimization and simplification candidate
- Khronos KTX-Software: KTX2/Basis texture processing candidate
- Blender: fallback DCC/conversion path for source formats where needed

These are not treated as production-approved merely because they are named here. Versions, licenses, deterministic behavior, Godot compatibility and runtime impact require pinned experiments.

## Ownership boundary

ARCONT stores:
- policies
- source/catalog metadata
- transformation recipes
- production profiles
- manifests/hashes
- validation/evidence

A production game stores:
- the approved GLB/textures it ships
- game-specific import settings
- game-specific semantic mapping
- gameplay/runtime integration

Temporary downloaded/generated binaries remain workflow artifacts unless an explicit archival decision says otherwise.

## Current limitation

The current agent stack exposes local project-owned inspection, budget validation, collision-policy derivation and deterministic staging through `tools/model_forge_control.py`; see [`../AGENT_CONTROL_PLANE.md`](../AGENT_CONTROL_PLANE.md). The Nexo acceptance uses already normalized GLB/glTF and does not invoke external geometry or texture processors. The stylized tactical 3D standard is a separate profile; it is not silently imposed on the third-person shooter.

The branch can inspect and validate GLB/glTF already present in an acquired package. Automatic conversion of OBJ/FBX/DAE/BLEND, automatic LOD/collision generation, KTX2 processing, and cross-repository staging are the next execution gates and must be implemented with pinned toolchains plus tests, not ad-hoc transformations.
