# Mobile Performance Foundations

Scope: shared, 2D, 2.5D, 3D
Platform baseline: Android
Status: SOURCE-EXTRACTED; empirical thresholds remain device-specific

## Frame pacing over headline FPS

Android's game guidance treats consistent presentation as a first-class problem. A high peak FPS with irregular frame delivery can feel worse than a lower stable target. Frame pacing interacts with display refresh, presentation queues and input latency.

ARCONT rule of measurement: record frame-time distribution and pacing behavior, not average FPS alone.

## Refresh-rate compatibility

Targets should be evaluated against supported display refresh rates. A target that cannot be paced cleanly on a given display can create uneven presentation. Benchmark metadata therefore records display refresh and target FPS.

## Thermal sustainability

Mobile SoCs do not have a single permanent performance level. Thermal state, power policy and environment can change CPU/GPU capability during a run. Android ADPF exposes thermal/performance information intended for proactive workload adaptation.

ARCONT consequence: short cold benchmarks and sustained warm benchmarks answer different questions. Both may be useful but must not be silently compared as equivalent.

## Adaptive quality

Potential control variables include resolution, shadows, particles, worker behavior, frame-rate target and other fidelity settings. Change them independently where possible so their cost and benefit can be measured.

## Profiling stack to study

- Perfetto/system tracing;
- Android GPU Inspector where supported;
- engine profilers;
- CPU/GPU timing;
- memory pressure;
- thermal headroom/state;
- frame pacing/presentation behavior;
- power where measurement is reliable.

## Benchmark questions generated

1. Cold versus 15+ minute sustained cost curves on representative Android tiers.
2. 30/40/45/60/90/120 FPS targets where display support permits.
3. Dynamic resolution versus fixed resolution for GPU-bound workloads.
4. Thermal response to shadows, particles, resolution and animation independently.
5. Touch-to-display behavior under GPU saturation and different pacing strategies.
6. Memory-pressure behavior during asset streaming and scene transitions.

No device-specific threshold becomes a general mobile rule without cross-hardware evidence.
