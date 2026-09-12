# ARCONT Foundation Acquisition 01

Status: ACTIVE
Scope: shared + 2D + 2.5D + 3D
Purpose: acquire high-value transferable game-engineering knowledge without mirroring the web.

## Evidence policy

Priority order:
1. specifications and pinned source code;
2. official platform/engine documentation;
3. peer-reviewed papers and conference courses;
4. technically strong implementation notes with reproducible reasoning;
5. secondary material only as a discovery lead.

A source being registered does not make every statement in it an ARCONT rule. Claims must be extracted, scoped, linked to evidence, and tested when empirical.

## Wave A — graphics and asset delivery

- Vulkan synchronization, resource lifetime, descriptors, pipeline behavior and validation.
- glTF runtime asset delivery.
- KTX 2.0 and Basis Universal texture delivery.
- GPU texture compression, mip chains, streaming and memory residency.
- draw submission, batching, instancing, culling, LOD/HLOD and occlusion.
- 2D sprite batching, atlases, tilemaps and overdraw.
- 2.5D mixed pipelines: sprites in 3D, orthographic/perspective cameras, depth and hybrid lighting.

Primary families: Khronos specifications/guides, engine source, platform/vendor profiling documentation.

## Wave B — frame loop, mobile and performance

- fixed/variable timestep and interpolation.
- frame pacing and presentation latency.
- CPU/GPU bound diagnosis.
- thermal headroom, sustained performance and power.
- memory pressure and resource streaming.
- high-refresh-rate behavior.
- multithreading and render/game thread interaction.

Android is the first mobile reference platform because ARCONT already has an Android-first benchmark strategy.

## Wave C — simulation and gameplay foundations

- broadphase/narrowphase physics concepts.
- collision layers and query cost.
- deterministic versus non-deterministic simulation.
- navigation graphs, A*, Dijkstra, hierarchical pathfinding, grids and navmeshes.
- steering/local avoidance.
- state machines, behavior trees, utility systems and planners.
- procedural terrain/world/dungeon generation and reproducible seeds.

## Wave D — networking

- authoritative server architecture.
- snapshots and interpolation.
- client prediction and reconciliation.
- rollback where appropriate.
- deterministic lockstep and its constraints.
- bandwidth, serialization, quantization, packet loss and jitter.
- networked physics.

Networking recommendations must state latency model, player count, simulation model and authority assumptions.

## Wave E — animation, audio and presentation

- skeletal animation and skinning.
- animation graphs/state machines/blending.
- IK and procedural animation.
- animation update-rate optimization.
- audio voices, buses, streaming, spatialization and mixing.
- particles/VFX, decals and post-processing.
- UI rendering/input/accessibility implications.

## Required output from each acquisition

Every useful source should eventually produce one or more of:
- source registry entry;
- source trace;
- extracted claim with scope;
- experiment question;
- negative result;
- pattern/anti-pattern;
- benchmark case;
- knowledge-graph relation.

## Stop rule

Do not wait until the library is 'complete'. There is no complete library of game development. Acquisition and empirical research proceed in parallel after this foundation is populated.
