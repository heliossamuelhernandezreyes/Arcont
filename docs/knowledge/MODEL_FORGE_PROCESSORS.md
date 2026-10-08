# Model Forge processor contract

Model Forge reuses existing ARCONT policy/evidence systems and delegates codec-heavy transforms.

## gltfpack / meshoptimizer
Use for GLB/glTF optimization and measured LOD candidates. The current wrapper
requires glTF/GLB with resolved local dependencies and produces a self-contained
GLB. It uses `-noq` and does not enable EXT_meshopt_compression: native acceptance
found the quantized output incompatible with the pinned Godot importer despite
passing glTF specification validation. Named nodes/materials can be preserved
with the processor's keep flags when gameplay hooks require them.

## Khronos glTF Validator
Every canonical GLB must pass the official specification validator with zero errors before production-profile validation.

[`processors.lock.json`](../../processors.lock.json) pins gltfpack 1.2 and
glTF Validator 2.0.0-dev.3.10 for Linux x86_64, including archive and executable
SHA-256. Install with `python tools/install_processors.py --destination DIR`
from the repository root and set `ARCONT_PROCESSOR_DIR=DIR`. Wrappers refuse
missing or mismatched binaries. Receipts identify the executable, lock and all
local input dependencies; executable and input hashes are checked again after
processing. Other platforms require a reviewed lock.

The pipeline and staging CLI require the specification gate by default.
`--candidate` explicitly produces an uncertified candidate. The control API
retains candidate as its compatibility default; request
`delivery_mode: "validated"` with an inline budget profile to certify the
staged bundle against specification and budgets. Runtime validation remains
required in either case. Publication never overwrites an existing bundle.

## KTX2
KTX-Software is an experimental texture-delivery processor. ARCONT does not globally force KTX2: GRAPHICS_ASSET_FOUNDATIONS already requires comparison of transmission size, transcode cost, upload time, resident memory, quality and platform support.

## Collision
ARCONT already states that collision must be simpler than art. Model Forge therefore emits a collision recipe; the game owns final collision semantics and validates them in runtime.

## DCC conversion
GLB/glTF can enter the lightweight processor directly. OBJ/FBX/DAE/BLEND require
a separate pinned conversion/DCC stage with reviewed dependency receipts. No
silent lossy conversion is allowed.
