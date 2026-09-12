# ARCONT — Game Development Atlas

ARCONT is a general, evidence-oriented knowledge bank for game engineering. Godot is the first deeply traced engine, not the boundary of the project.

## Dimensions

Knowledge is classified by applicability rather than copied into silos:

- `shared` — engine- and dimensionality-independent principles.
- `2d` — dedicated 2D rendering, physics, tile/grid worlds, sprites, 2D lighting, parallax and cameras.
- `2_5d` — mixed-dimensional techniques: 3D worlds with 2D gameplay constraints, 2D visuals in 3D, layered depth, billboard/sprite hybrids, orthographic/perspective hybrids and constrained physics/navigation.
- `3d` — 3D rendering, spatial worlds, meshes, skeletal animation, 3D physics/navigation, LOD/HLOD and streaming.

A topic may belong to multiple dimensions. Do not duplicate evidence merely to fit folders; link it through metadata/graph relationships.

## Core domains

1. Frame lifecycle, timing and scheduling
2. Rendering architecture and graphics APIs
3. Lighting, shadows and materials/shaders
4. Cameras, visibility, culling and occlusion
5. Geometry, sprites, tilemaps, meshes and instancing
6. Physics, collision, constraints and destruction
7. Animation, skeletal systems, IK and procedural animation
8. Navigation, pathfinding, steering and AI
9. Gameplay architecture, state, events, ECS/data-oriented patterns
10. Input, latency and controls
11. Audio, spatial audio and mixing
12. UI/HUD and accessibility
13. Asset import, compression, caching and streaming
14. World generation and procedural content
15. Networking, replication, prediction and rollback
16. Save/data/versioning
17. Profiling, observability and debugging
18. CPU, GPU, memory, storage and loading performance
19. Mobile: thermals, power, frame pacing and device fragmentation
20. Build, packaging, deployment and platform constraints
21. Tooling/editor pipelines and content production
22. Testing, determinism, reproducibility and regression detection

## Engine lenses

ARCONT may learn from multiple engines while preserving provenance:

- Godot — source-level canonical study begins at the pinned Godot snapshot in `docs/godot/SOURCE_PIN.md`.
- Unreal Engine — official documentation and publicly inspectable source/reference material where licensing permits.
- Unity — official manuals/API documentation and public technical material.
- Custom/open-source engines — only when they expose a useful transferable implementation or experiment.

Engine-specific claims stay engine/version scoped. Transferable conclusions require either direct reasoning with explicit assumptions or independent validation.

## Source hierarchy

1. Exact pinned source code / standards / specifications.
2. Official engine or platform documentation.
3. Peer-reviewed papers and proceedings.
4. First-party technical presentations/postmortems (GDC, SIGGRAPH, engine/platform teams).
5. Reproducible open-source implementations and issue/PR evidence.
6. ARCONT experiments and measurements.
7. Secondary technical sources, clearly labeled.

Popularity is not evidence quality.

## Acquisition rule

ARCONT does **not** mirror the internet. For every useful source we retain the smallest lawful durable representation:

- source identity and canonical URL,
- publisher/author,
- date/version when known,
- license/redistribution status when known,
- topics/dimensions/platforms,
- concise technical extraction,
- claims worth validating,
- links to experiments/ledger/graph,
- local copy only when redistribution/storage is allowed and useful.

Videos, books, courses and copyrighted pages are referenced and summarized rather than copied wholesale unless their license explicitly permits archival redistribution.

## 2.5D definition used by ARCONT

`2.5d` is not treated as one engine feature. It is a design/implementation family where presentation and simulation dimensionality differ or depth is deliberately constrained. Each entry must say which model it uses, for example:

- 3D rendering + movement constrained to a plane,
- 2D sprites/billboards inside a 3D world,
- layered 2D with simulated depth,
- orthographic 3D presented as 2D,
- 3D physics with 2D gameplay rules.

This prevents vague recommendations such as “use the 2.5D pipeline”.

## Success criterion

The atlas is successful when a future game can ask a concrete engineering question and ARCONT can return: relevant techniques, primary sources, known costs, platform/version limits, contradictory evidence, experiments, confidence/maturity and a conditional recommendation.