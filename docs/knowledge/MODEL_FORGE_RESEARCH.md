# Model Forge — researched production baseline

Date: 2026-09-20

## Decisions

1. Canonical delivery format is glTF 2.0 / GLB. Godot recommends glTF 2.0 and supports GLB directly.
2. Godot coordinate convention is right-handed, Y-up. Oriented glTF assets use +Z as model front; this is the canonical Model Forge convention.
3. OBJ is accepted only as source material because it cannot carry the full production feature set (skeletons, animation, PBR, pivots).
4. Validation has two layers: ARCONT production policy plus Khronos glTF Validator when available.
5. Mesh simplification/optimization should use a proven external processor such as meshoptimizer/gltfpack rather than an ARCONT-written geometry algorithm. Simplification must preserve measurable error and must be benchmarked.
6. KTX2/Basis is an optional delivery optimization, not an unconditional conversion. KTX2/Basis must be evaluated for visual quality, transcode/upload cost, resident memory and target-device support.
7. Model Forge must reuse Asset Vault license/trust policy and Map Forge's provider-neutral architecture.
8. Generated/downloaded third-party binaries remain ephemeral artifacts in ARCONT. Production game assets live in the game repository.

## Execution stages

DISCOVER (Asset Vault)
-> TRUST GATE
-> ACQUIRE
-> HASH
-> UNPACK
-> INSPECT
-> NORMALIZE/CONVERT
-> SPEC VALIDATE
-> PRODUCTION VALIDATE
-> LOD
-> COLLISION
-> TEXTURE DELIVERY
-> STAGE TO GAME
-> GODOT IMPORT
-> TARGET-CAMERA EVIDENCE
-> RUNTIME EVIDENCE

## Tool boundaries

ARCONT owns orchestration, policy, manifests and evidence. Mature external tools own complex geometry/texture codecs. Provider/tool versions must be pinned before a result is promoted beyond experimental evidence.
