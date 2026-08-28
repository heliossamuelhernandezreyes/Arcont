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

## Arcont performance tiers
Potential knobs: enemy AI cadence, animation update rate, enemy visual detail, visibility distance, prop density, shadow count/distance, particles/gore, decals, physics debris, audio polyphony and post-processing.

## Benchmark philosophy
Create repeatable stress scenes: combat crowd, urban vista, gore burst, tactical squad, traversal, boss/VFX and worst-case mixed encounter. Record device + build + settings + measurements.

## References
- Godot profiler: https://docs.godotengine.org/en/stable/tutorials/scripting/debug/the_profiler.html
- 3D optimization: https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html
- CPU optimization: https://docs.godotengine.org/en/stable/tutorials/performance/cpu_optimization.html
- GPU optimization: https://docs.godotengine.org/en/stable/tutorials/performance/gpu_optimization.html

## Anti-patterns
- Optimizing only desktop.
- Chasing FPS average while ignoring stutter.
- Disabling systems blindly instead of identifying bottlenecks.
- Assuming lower polygon count solves draw-call/material/overdraw bottlenecks.
