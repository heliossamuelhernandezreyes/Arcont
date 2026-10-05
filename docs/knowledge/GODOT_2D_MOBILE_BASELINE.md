# Godot 2D mobile production baseline

Status: **working baseline / not yet device-validated**

Trigger consumer: `heliossamuelhernandezreyes/Godot-juegos-2d/Mortofe`

Engine scope: Godot `4.7.2-stable`, commit `ed1daf0bf001b61586d9930840f2f1394092c079`.

## Purpose

This baseline exists because a production 2D game exposed a gap between ARCONT's general 2D knowledge and the operational requirements of a mobile-first Godot game. It is not a game template stored inside ARCONT. The implementation remains in the external consumer; ARCONT records the reusable contract, source trace, evidence and validation backlog.

## Mobile-first rules

1. Mobile is a primary platform from the first playable build, not a late port.
2. Gameplay input must consume normal Godot InputMap actions so touch, keyboard and future gamepad inputs can share gameplay code.
3. Multi-touch controls must permit movement and at least two simultaneous actions without replacing the gameplay controller.
4. Interactive controls must account for display cutouts and safe areas.
5. The base 2D viewport uses `canvas_items` with `expand` unless an art-specific pixel policy demonstrates a better alternative.
6. Orientation is landscape for Mortofe; orientation belongs to product policy and must be explicit.
7. Renderer selection is empirical. Mortofe begins on Compatibility/OpenGL for broad device reach. Mobile/Vulkan is a candidate only after device benchmarks.
8. Android frame pacing defaults are retained unless measurements demonstrate a regression.
9. Runtime frame-time evidence must be collected on device; desktop/headless success is not mobile performance evidence.
10. Engine source modification is the final escalation step, not the first.

## Input contract observed in Mortofe

Consumer implementation: `Mortofe/scripts/mobile_controls.gd`.

Current control surface:

- left virtual analog region -> `move_left` / `move_right` InputMap actions with analog strength,
- attack button -> `attack`,
- jump button -> `jump`,
- dash button -> `dash`,
- raw `InputEventScreenTouch` + `InputEventScreenDrag` finger indices preserve simultaneous touches,
- controls are isolated from gameplay logic,
- desktop keyboard/mouse remains available through the same InputMap actions.

This is a baseline, not a final ergonomic layout. Required device validation includes thumb reach, accidental activation, drag loss, 2/3/4-finger combinations, orientation interruption and touch latency.

## Safe-area contract

Godot source/API path used by the consumer:

- `DisplayServer.get_display_safe_area()` for the unobscured physical area,
- physical safe coordinates are scaled into the active viewport coordinate system,
- Android/iOS only; desktop falls back to the full viewport.

The layout must not assume that the physical screen edge is interactable.

## Rendering/display baseline

Consumer `project.godot` currently fixes:

- logical base: `1280x720`,
- stretch mode: `canvas_items`,
- stretch aspect: `expand`,
- handheld orientation: landscape,
- renderer: `gl_compatibility`, including mobile override,
- physics: 60 ticks/s,
- Android frame-pacing mode: engine default auto policy.

Godot 4.7 changed new-project defaults to `canvas_items` + `expand`, making this a first-party-supported baseline for non-pixel-art 2D. Final art can reopen this decision if sprite scaling quality requires a viewport or integer-scaling policy.

## Android export source trace

The Android exporter was inspected at the exact pinned Godot commit in `platform/android/export/export_plugin.cpp`.

Relevant observed options include:

- `package/unique_name`,
- `package/name`,
- `architectures/<abi>`,
- `screen/immersive_mode`,
- `screen/edge_to_edge`,
- screen-size support flags.

At this Godot revision the exporter enables only `arm64-v8a` by default. Mortofe's initial preset follows that default until device-distribution requirements justify additional ABIs.

## Runtime evidence contract

Consumer implementation: `Mortofe/scripts/mobile_telemetry.gd`.

Current lightweight payload records:

- OS and model,
- renderer name/vendor,
- visible resolution,
- sample count,
- p50/p95/p99/max wall-frame interval.

Limits:

- frame intervals are not direct CPU/GPU timings,
- no thermal measurement,
- no direct display refresh measurement,
- no touch-to-photon measurement,
- headless output is only a parser/runtime sanity check.

For mobile promotion, collect real Android runs and feed normalized evidence into ARCONT's observability/evidence pipeline.

## Initial performance targets

Targets are engineering gates, not claims of current achievement:

- primary target: stable 60 fps on the intended baseline Android tier,
- aspirational high-refresh mode: 90/120 fps on capable devices after gameplay and thermal validation,
- 60 fps frame budget: 16.67 ms,
- 120 fps frame budget: 8.33 ms,
- p95/p99 and sustained behavior matter more than an isolated FPS counter,
- thermal degradation must be measured across extended play windows.

## Escalation ladder

When a mobile requirement cannot be satisfied:

1. Godot public API / project settings,
2. reusable GDScript/C# component,
3. editor plugin or import pipeline,
4. GDExtension,
5. Android v2 plugin when platform APIs are the real requirement,
6. engine module,
7. maintained Godot fork only with reproducible evidence that lower layers are insufficient.

Any source-level intervention must cite the pinned Godot version, commit, subsystem, reason and regression test.

## Validation backlog

- real Android multi-touch matrix,
- notch/cutout screenshots across aspect ratios,
- touch latency protocol,
- 60/90/120 Hz frame pacing,
- sustained thermal test,
- Android APK/AAB CI once SDK/export-template cost is justified,
- controller/gamepad coexistence,
- pause/resume and focus loss,
- low-memory/background restore,
- graphics tier selection from measured device results.
