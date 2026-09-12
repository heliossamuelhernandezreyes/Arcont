# AI Navigation and Crowd Systems

Dimensions: shared, 2D, 2.5D, 3D
Status: source-derived starter knowledge; not yet validated by ARCONT benchmarks

## Source anchors

### Recast / Detour

Recast Navigation is structured into distinct modules:

- Recast: navmesh generation.
- Detour: runtime navmesh loading, pathfinding and queries.
- DetourTileCache: tiled navmesh streaming / rebuilding.
- DetourCrowd: local movement, collision avoidance and crowds.

Recast's documented build pipeline rasterizes triangle geometry into voxels, filters unwalkable voxels, partitions walkable regions, then triangulates them into navigation polygons. Tiled navmeshes trade additional complexity for large-world support, rebaking and streaming.

## Transferable patterns

### Separate navigation layers

Do not collapse these into one subsystem:

1. representation of walkable space;
2. global path query;
3. local steering / avoidance;
4. dynamic obstacle handling;
5. streaming/rebuild policy.

They have different costs and update frequencies.

### Tiled navigation as locality control

The transferable idea behind tiled navmeshes is not merely 'use tiles'. It is to bound invalidation and rebuild work spatially. ARCONT should therefore measure the cost of a local world edit as a function of tile dimensions and affected-tile count.

### Pathfinding is not crowd simulation

A valid shortest path does not guarantee believable or collision-free local motion. Local avoidance, desired velocity, acceleration limits, agent radius and density need separate testing.

## Research questions

- At what map size does a monolithic navmesh become inferior to tiled navigation on each platform?
- How does path-query latency scale with polygon count, path length and query concurrency?
- What is the cost of rebuilding 1, 4, 16 or N neighboring tiles after destruction?
- How does crowd simulation scale with agent density rather than only agent count?
- When does local avoidance become the dominant cost compared with path queries?
- How much navigation data can be streamed before memory or latency becomes a bottleneck?

## Benchmark families

### NAV-001: query scaling
Variables: navmesh polygon count, start-end distance, concurrent agents.
Metrics: p50/p95/p99 query time, allocations, path length, failures.

### NAV-002: local rebuild
Variables: tile size, geometry edit size, number of invalidated tiles.
Metrics: rebuild time, peak memory, hitch duration, affected agents.

### NAV-003: crowd density
Variables: agents, area, radius, avoidance quality/update frequency.
Metrics: CPU time, collisions, deadlocks, path deviation, velocity jitter.

### NAV-004: streaming
Variables: active tile radius, I/O bandwidth, prefetch distance.
Metrics: memory, load latency, stalls, missing-navigation incidents.

## Anti-patterns to test rather than assume

- Rebuilding the entire navmesh after every local destruction event.
- Running full pathfinding every frame for every agent.
- Treating steering oscillation as only an animation problem.
- Using identical update rates for distant and nearby agents.
- Assuming higher navmesh resolution always produces better gameplay.

## Engine transfer

Recast/Detour concepts are especially useful to ARCONT because the project is used by multiple engines and therefore gives us a relatively engine-independent implementation reference. Engine integrations can still diverge in threading, caching, obstacle systems and API semantics, so cross-engine claims require separate evidence.