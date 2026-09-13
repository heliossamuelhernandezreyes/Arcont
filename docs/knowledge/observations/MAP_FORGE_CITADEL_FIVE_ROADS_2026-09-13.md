# Map Forge observation — Citadel of the Five Roads

**Date:** 2026-09-13
**Implementation:** `heliossamuelhernandezreyes/Closeseal`
**Branch:** `art/first-visual-pass`
**Validation:** Map Authoring Providers run `34763576913`
**Engine:** Godot `4.7.2-stable`
**Maturity:** L4 limited to Ubuntu/Godot 4.7.2 CI; not cross-hardware or production validation.

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

## Assets and materials

The map contract names provider-neutral asset IDs and material IDs. The bridge now exports the visual style, material palette and asset catalog in the generated manifest and applies material profiles to procedural structure guides. This makes the visual pass replaceable without changing route semantics.

External providers remain projections:

- Terrain3D: terrain authoring.
- Cyclops: modular structure authoring.
- ProtonScatter: vegetation/rock/rune scatter.
- FuncGodot: optional interchange socket.
- Godot Recast: physical navigation.

## Known boundary

The current output is a detailed, validated greybox/authoring map with procedural visual guides and provider-ready assets. It is not yet final art, final terrain sculpt, Android performance validation, or production balance. The next step is a mobile readability pass followed by replacement of procedural guides with approved modular asset kits.
