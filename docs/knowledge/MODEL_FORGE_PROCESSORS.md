# Model Forge processor contract

Model Forge reuses existing ARCONT policy/evidence systems and delegates codec-heavy transforms.

## gltfpack / meshoptimizer
Use for GLB/glTF/OBJ optimization and measured LOD candidates. Default production processing does not enable EXT_meshopt_compression because runtime compatibility must be proven independently. Named nodes/materials may be preserved with the processor's keep flags when gameplay hooks require them.

## Khronos glTF Validator
Every canonical GLB must pass the official specification validator with zero errors before production-profile validation.

## KTX2
KTX-Software is an experimental texture-delivery processor. ARCONT does not globally force KTX2: GRAPHICS_ASSET_FOUNDATIONS already requires comparison of transmission size, transcode cost, upload time, resident memory, quality and platform support.

## Collision
ARCONT already states that collision must be simpler than art. Model Forge therefore emits a collision recipe; the game owns final collision semantics and validates them in runtime.

## DCC conversion
Godot recommends glTF 2.0. GLB/glTF/OBJ can enter the lightweight processor directly. FBX/DAE/BLEND require a pinned conversion/DCC stage. No silent lossy conversion is allowed.
