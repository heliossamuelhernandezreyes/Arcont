# Godot — Performance and Profiling

## Rule zero
Optimize measured bottlenecks, but design systems so expensive work can be scaled before a crisis appears.

## Measure
- CPU frame time and script/physics/navigation contribution.
- GPU frame time.
- Frame pacing, not only average FPS.
- Draw calls/objects/vertices.
- Animation and skinning load.
- Navigation/path query load.
- Physics bodies/raycasts.
- Particle counts and overdraw.
- RAM and VRAM pressure.
- Loading spikes and shader compilation/stutter.
- APK/build size.
- Device temperature, throttling and battery drain.

## Built-in runtime monitors to expose in Arcont
Godot 4's `Performance.get_monitor()` provides stable engine-side telemetry that is preferable to inferring all performance from FPS alone. Relevant monitors for the current mobile vertical slice:
- `Performance.TIME_FPS`: rendered FPS, updated approximately once per second.
- `Performance.TIME_PROCESS`: process-frame CPU time in seconds.
- `Performance.TIME_PHYSICS_PROCESS`: physics-frame CPU time in seconds.
- `Performance.OBJECT_COUNT`, `OBJECT_RESOURCE_COUNT`, `OBJECT_NODE_COUNT`, `OBJECT_ORPHAN_NODE_COUNT`: scene/runtime object pressure. Orphan-node count is debug-only.
- `Performance.RENDER_TOTAL_OBJECTS_IN_FRAME`: visible/rendered objects after culling.
- `Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME`: rendered vertices/indices including additional render passes; do not interpret this as source triangle count.
- `Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME`: actual draw calls for the last rendered frame after culling.
- `Performance.RENDER_VIDEO_MEM_USED`, `RENDER_TEXTURE_MEM_USED`, `RENDER_BUFFER_MEM_USED`: renderer memory telemetry where supported.

Source: Godot Engine 4.x `Performance` class documentation, https://docs.godotengine.org/en/4.x/classes/class_performance.html (re-audit when the pinned engine version changes).

Operational rule: expose these values as observational telemetry first. Do not invent universal pass/fail ceilings from desktop/headless CI. Record representative Android device + build + scene + quality tier before promoting any threshold into a production budget.

For route/environment optimization, compare the same deterministic camera/scene before and after a representation change. Track at minimum draw calls, rendered objects, primitives, process/physics time and memory. A lower Node count by itself is not proof of a faster frame, and a higher primitive count is not automatically a regression if draw/visibility behavior improves.

## Arcont performance tiers
Potential knobs: enemy AI cadence, animation update rate, enemy visual detail, visibility distance, prop density, shadow count/distance, particles/gore, decals, physics debris, audio polyphony and post-processing.

## Benchmark philosophy
Create repeatable stress scenes: combat crowd, urban vista, gore burst, tactical squad, traversal, boss/VFX and worst-case mixed encounter. Record device + build + settings + measurements.

## References
- Godot Performance monitors: https://docs.godotengine.org/en/4.x/classes/class_performance.html
- Godot profiler: https://docs.godotengine.org/en/stable/tutorials/scripting/debug/the_profiler.html
- 3D optimization: https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html
- CPU optimization: https://docs.godotengine.org/en/stable/tutorials/performance/cpu_optimization.html
- GPU optimization: https://docs.godotengine.org/en/stable/tutorials/performance/gpu_optimization.html

## Anti-patterns
- Optimizing only desktop.
- Chasing FPS average while ignoring stutter.
- Disabling systems blindly instead of identifying bottlenecks.
- Assuming lower polygon count solves draw-call/material/overdraw bottlenecks.
