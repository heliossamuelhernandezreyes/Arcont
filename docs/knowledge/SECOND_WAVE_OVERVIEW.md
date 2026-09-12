# ARCONT — Second Acquisition Wave

Purpose: expand ARCONT from a starter cross-engine library into a broad technical reference for reusable game engineering across 2D, 2.5D, 3D and shared systems.

This wave intentionally prioritizes primary/official sources and open-source implementations. It records transferable concepts, implementation questions and benchmark targets; it does not automatically promote source claims into validated ARCONT rules.

## Domains covered

1. AI navigation and crowd movement.
2. Physics and simulation.
3. Procedural content generation.
4. Animation, IK and retargeting.
5. Data-oriented design / ECS.
6. Rendering and GPU execution patterns.
7. Audio architecture and performance.
8. Asset loading, memory and streaming.
9. Concurrency / multithreading.

## Cross-cutting research principle

For each technique ARCONT separates:

- SOURCE: what the implementation or official documentation states.
- TRANSFERABLE PATTERN: an engineering idea that may apply across engines.
- HYPOTHESIS: what ARCONT expects to observe.
- EXPERIMENT: the minimum reproducible test required.
- RULE: only after evidence reaches the required maturity.

## Initial source families

- Recast & Detour for navmesh generation, queries, tiled navigation and crowds.
- NVIDIA PhysX for rigid bodies, scene queries, articulations, character control and advanced simulation.
- Unreal Engine PCG for data-flow procedural generation and hierarchical/runtime generation.
- Unreal Control Rig / IK Rig for runtime procedural animation, IK and retargeting.
- Unity Entities and Unreal MassEntity for data-oriented/ECS concepts.
- AMD GPUOpen FidelityFX and Arm Mali guidance for GPU workload construction and shader/mobile optimization.
- Godot audio buses and spatial audio as an open engine reference for audio routing/effects.
- Unreal asynchronous asset loading as a concrete reference for avoiding unnecessary hard-reference loading.

## What this wave does not claim

- Recast is not automatically the best navigation solution for every game.
- ECS is not automatically faster than object-oriented architecture.
- Async loading is not automatically better for every asset size or access pattern.
- A GPU optimization from AMD or Arm is not universal across all architectures.
- An Unreal or Unity implementation detail is not treated as a Godot implementation detail.

## First benchmark families produced by this wave

- Navmesh tile size, rebuild scope, query cost and crowd-agent scaling.
- Physics body/constraint/contact scaling and scene-query cost.
- Procedural graph density, partition size and runtime-generation budget.
- IK solver complexity vs bones/effectors and animation update frequency.
- ECS/archetype/chunk iteration vs object-oriented equivalent workloads.
- GPU pass count, synchronization, bandwidth and shader permutation cost.
- Audio voice/effect/bus scaling and inactive-voice behavior.
- Asset-load latency, hitching, memory residency and eviction behavior.
- Worker-thread scaling, task granularity and synchronization overhead.

## Status

This document marks the start of the second large acquisition wave. All extracted knowledge remains subject to ARCONT's evidence, maturity, provenance and revalidation rules.