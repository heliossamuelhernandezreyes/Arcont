# Map Forge observation — Citadel of the Five Roads

**Date:** 2026-09-13
**Implementation:** `heliossamuelhernandezreyes/Closeseal`
**Branch:** `art/first-visual-pass`
**Navigation validation:** Map Authoring Providers run `34763576913`
**Final visual/provider validation:** Map Authoring Providers run `34785401546`; Real Prototype Screenshot run `34785401517`
**Engine:** Godot `4.7.2-stable`
**Maturity:** L3 observed on GitHub Ubuntu/Godot 4.7.2; not independently reproduced across games, hardware or engine versions.

## Result

Close Seal's canonical map contract was expanded into a large tactical arena named **Citadel of the Five Roads**. The map remains generated from semantic JSON and does not create a second gameplay source of truth.

- Bounds: `96 x 64 m`.
- Bases: two fortified team bases with hero spawns.
- Routes: one primary lane, two secondary objective lanes and two jungle flank routes.
- Objectives: central seal, relics, wards and watchpoints.
- Regions: formation basins, chokes, objective zones, spawn zones, cover and neutral forest rims.
- Structures: keeps, gatehouses, towers, ruins, obelisks, pillars and bridge markers.
- Environment: pine belts, deadwood, rock fields and rune gardens.
- Authoring metadata: asset catalog, material palette, provider roles and navigation parameters.

## Physical evidence

The final workflow passed:

1. Exact provider installation, including the pinned Cyclops Godot 4.7 release archive.
2. Clean editor import pass.
3. Source geometry diagnostics.
4. Physical provider workspace generation.
5. Recast NavigationMesh bake.
6. NavigationServer3D synchronization.
7. A→B queries for all five canonical routes.
8. Traffic telemetry.
9. Executable avoidance-agent flow.

The physical navigation probe reported all five routes queryable, with route detour ratios approximately `0.981–0.988` and total physical path length approximately `379.5 m`. The endpoint projection remained within the configuration-derived tolerance.

Crowd probes retain operability and saturation as separate evidence classes: low loads are completion gates; high loads are bounded stress measurements. This is a capacity observation, not a claim of Android performance or final multiplayer balance.

## Runtime visual implementation evidence

Close Seal now consumes the canonical contract through a deterministic runtime visual kit rather than rendering only the primary-lane greybox. The real-project capture verified:

- all five canonical routes, compiled into 28 visible route segments;
- all 20 structure guides represented by modular keeps, gatehouses, towers, ruins, obelisks, pillars and bridges;
- all seven objectives represented by readable platforms, seals, shrines or beacons;
- 154 deterministic environment instances across forests, deadwood, rock fields and rune gardens;
- contract material IDs converted to Godot StandardMaterial3D profiles;
- mobile-oriented batching of repeated environment meshes with MultiMesh;
- a full-map tactical camera and a corrected nine-patch HUD layout.

The screenshot workflow now performs a Godot editor import before runtime capture, rejects script/resource-loader errors, and gates on the expected visual-build counts. The final screenshot and visual logs are preserved by workflow run `34785401517`.

## Negative evidence and correction

Two failures were preserved as implementation knowledge:

1. **Godot 4.7.2 static inference:** the first visual-provider run `34784771680` failed because a loop-derived `z` coordinate had no statically resolvable type. Explicit `float` typing corrected the parser failure; no canonical geometry changed.
2. **Cyclops execution context:** runtime-headless provider smoke could create the workspace marker but emitted preload/class errors from Cyclops editor-only `@tool` resources. Running physical workspace generation inside Godot's headless editor context and rejecting any script error removed those false-positive logs. Final provider run `34785401546` reported zero script errors while preserving workspace, Recast, A→B and army-flow success.

This establishes a reusable rule at L3: editor-oriented authoring providers must be validated in editor context; runtime navigation probes remain separate headless-runtime tests.

## Assets and materials

The map contract names provider-neutral asset IDs and material IDs. The bridge now exports the visual style, material palette and asset catalog in the generated manifest and applies material profiles to procedural structure guides. This makes the visual pass replaceable without changing route semantics.

External providers remain projections:

- Terrain3D: terrain authoring.
- Cyclops: modular structure authoring.
- ProtonScatter: vegetation/rock/rune scatter.
- FuncGodot: optional interchange socket.
- Godot Recast: physical navigation.

## Known boundary

The current output is a detailed, contract-driven tactical map with a modular procedural runtime presentation, imported UI art, provider-ready authoring layers and physically validated navigation. It is not an approved final production asset kit, a final Terrain3D sculpt, Android-device performance evidence, multiplayer balance validation, or provider-to-contract round-trip proof. The next independent maturity step is reproduction on a defined Android reference device and reuse by a second game/runtime implementation.
