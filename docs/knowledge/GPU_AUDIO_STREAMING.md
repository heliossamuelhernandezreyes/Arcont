# GPU Workloads, Audio, Memory and Streaming

Dimensions: shared, 2D, 2.5D, 3D
Status: source-derived starter knowledge

## GPU workload construction

AMD GPUOpen's FidelityFX material provides concrete examples of reducing synchronization and redundant work. Single Pass Downsampler generates mip chains with a single-dispatch strategy and uses local/shared data plus optional wave operations; Variable Rate Shading demonstrates selectively reducing shading work where neighboring pixels provide less unique information. Arm's mobile GPU guidance emphasizes frame construction, efficient API usage, content and shader practices on Mali architectures.

### Transferable GPU questions

- How many passes and synchronization points are required?
- Is the workload ALU-bound, bandwidth-bound, latency-bound or occupancy-bound?
- Does an optimization reduce work or merely move it?
- Are intermediate render targets consuming avoidable bandwidth/memory?
- Do subgroup/wave operations help on the tested architecture?
- Does FP16/packed math improve throughput without unacceptable quality loss?
- How portable is an optimization across desktop and tile-based mobile GPUs?

### GPU benchmark families

GPU-001: multipass vs fused/single-pass work.
GPU-002: render-target bandwidth and resolution scaling.
GPU-003: shader permutation complexity and compile/runtime cost.
GPU-004: FP16 vs FP32 where supported.
GPU-005: subgroup/wave path vs shared-memory fallback.
GPU-006: variable-rate/foveated/selective shading quality-cost curves.
GPU-007: thermal sustained GPU load on mobile.

## Audio architecture

Godot's audio documentation provides a useful open-engine reference: audio can be routed through buses, effects are ordered on buses, buses can route into other buses, and silent buses may be disabled automatically. Hardware ultimately limits practical bus/effect counts.

### Transferable audio layers

1. decoded/streamed source voices;
2. positional/spatial processing;
3. voice prioritization/virtualization;
4. bus routing;
5. effects/DSP;
6. mixing;
7. device output / latency.

### Audio research questions

- How does CPU cost scale with active audible voices rather than total registered emitters?
- When should distant/inaudible sounds be culled or virtualized?
- What is the cost of spatialization vs non-positional playback?
- Which DSP effects dominate CPU cost?
- How do streamed and fully resident audio differ in latency and memory?
- What buffer size gives acceptable latency without underruns on each platform?

### Audio benchmark families

AUD-001: active voice count.
AUD-002: positional vs non-positional voices.
AUD-003: bus/effect chain depth.
AUD-004: streaming vs memory-resident assets.
AUD-005: sample rate / channel layout / buffer size.
AUD-006: adaptive culling and voice virtualization.

## Asset loading, memory and streaming

Unreal's asynchronous asset-loading documentation demonstrates the distinction between hard references that can cause assets to load with their owner and soft references that can be resolved on demand. Its StreamableManager can request asynchronous loads rather than blocking the main thread.

The transferable principle is explicit residency control, not the Unreal API itself.

### Memory/streaming questions

- What is resident at startup and why?
- Which references unintentionally keep large dependency graphs resident?
- What load operations block the frame thread?
- What is the I/O -> decompression -> parse -> upload pipeline cost?
- How much prefetch distance is needed at a given traversal speed?
- What is the eviction/reload churn cost?
- Which assets should be streamed vs resident?

### Streaming benchmark families

STREAM-001: synchronous vs asynchronous asset load hitching.
STREAM-002: small-many vs large-few assets.
STREAM-003: prefetch distance / traversal speed.
STREAM-004: decompression/transcode cost.
STREAM-005: CPU-to-GPU texture/mesh upload.
STREAM-006: memory budget and eviction policy.
STREAM-007: dependency graph caused by hard vs deferred references.

## Combined-frame principle

CPU simulation, GPU rendering, audio mixing and I/O may each look acceptable in isolation and still produce frame-time spikes when their peak work aligns. ARCONT's combined-system tests must therefore preserve timelines and p95/p99 behavior, not only subsystem averages.