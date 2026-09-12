# Data-Oriented Design, ECS and Concurrency

Dimensions: shared, 2D, 2.5D, 3D
Status: source-derived starter knowledge

## Source anchors

Unity Entities and Unreal MassEntity provide two modern production references for data-oriented gameplay architecture. Unreal documents entities as data-only compositions of fragments organized into archetypes; composition changes can be deferred through command buffers and batch-processed. Unity Entities provides a production ECS package for Unity 6.

## Transferable patterns

### Separate data from behavior where scale justifies it

Data-oriented architecture can improve locality and batchability, but ARCONT must test the workload instead of assuming ECS is always faster.

### Archetype/chunk organization

Grouping entities with identical component composition can make iteration over contiguous homogeneous data efficient. The tradeoff is that changing composition may require moving data between archetypes/chunks.

### Deferred structural changes

Batching add/remove-component or composition changes avoids mutating the collection while iterating it and may amortize structural work.

### Job/task granularity

Multithreading only helps when useful work exceeds scheduling and synchronization overhead. Too-small jobs can be slower than single-thread execution.

## Research questions

- When does contiguous archetype iteration outperform object-oriented traversal on each target CPU?
- What is the cost of structural changes compared with simple component-value updates?
- How many entities are needed before ECS overhead is amortized?
- How do cache misses, branch behavior and memory footprint differ?
- What task size is needed before worker-thread dispatch pays off?
- How does false sharing affect parallel update workloads?
- What synchronization/barrier patterns cause main-thread stalls?
- How much scaling remains after 2, 4, 6 or more worker threads on mobile SoCs?

## Benchmark families

### ECS-001: iteration
Identical computation over N objects/entities under object-oriented and data-oriented layouts.
Metrics: CPU time, p95/p99, allocations, memory footprint; hardware counters if available.

### ECS-002: structural mutation
Add/remove components or change archetype for controlled percentages of entities per frame.

### ECS-003: sparse access
Measure workloads that need random cross-entity access instead of linear homogeneous iteration.

### THREAD-001: task granularity
Same total work split into progressively smaller tasks.

### THREAD-002: scaling
Run identical workload across controlled worker counts.

### THREAD-003: synchronization
Measure mutex/atomic/barrier/queue costs under increasing contention.

### THREAD-004: producer-consumer
Game-thread production with worker processing and bounded result consumption.

## Anti-patterns to test

- converting every gameplay object to ECS without a scaling need;
- frequent structural mutation in a supposedly cache-friendly hot loop;
- scheduling thousands of tiny jobs;
- sharing writable cache lines across workers;
- assuming logical CPU count equals useful parallel capacity on thermally constrained mobile hardware;
- hiding blocking waits behind APIs named 'async'.

## Decision rule policy

ARCONT will recommend ECS or multithreading only for a stated workload, scale, hardware class and maintainability constraint. Simplicity is part of the cost model.