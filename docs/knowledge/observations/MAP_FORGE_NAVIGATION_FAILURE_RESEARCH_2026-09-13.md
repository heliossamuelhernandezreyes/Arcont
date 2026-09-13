# Map Forge physical navigation failure — research record

**ID:** `ARC-GODOT-OBS-MAP-NAV-0001`
**Date:** 2026-09-13
**Engine:** Godot `4.7.2-stable`
**Engine commit:** `ed1daf0bf001b61586d9930840f2f1394092c079`
**Production reference:** `heliossamuelhernandezreyes/Closeseal`, branch `art/first-visual-pass`
**Status:** observed negative result + source-derived remediation plan
**Maturity:** L3 for the Close Seal failure observation; remediation proposed until reproduced successfully.

## Observed negative result

Close Seal Map Forge compiles canonical route corridors into a `NavigationMesh` with non-zero vertices/polygons and synchronizes a `NavigationServer3D` map, but physical closest-point/path queries do not see a usable route surface. A separate minimal procedural NavigationServer3D surface passes in the same Godot 4.7.2 CI environment.

This narrows the failure to the corridor surface produced by `compile_route_surface()`, rather than Godot startup, provider installation, synchronization, or the general procedural region-registration path.

The failing compiler constructs each route as shared left/right vertex pairs with one four-index polygon per segment (`continuous_shared_vertices_per_route`).

## Prior art found

This class of failure has repeatedly appeared in Godot 4.x. Reported causes include: navigation-map `cell_size` / `cell_height` mismatch; crossing or overlapping polygons; more than two edges sharing one rasterization cell; very long/thin or tiny polygons; invalid/ambiguous manual polygon topology; and large monolithic surfaces.

Godot's official navigation documentation supports procedurally generated triangle-face source geometry followed by `NavigationServer3D.bake_from_source_geometry_data()`, and recommends keeping source geometry simple. It also requires NavigationMesh rasterization cell settings to match the navigation map.

Relevant upstream history includes Godot issues #79217, #82209, #85548, #99334 and #108263. Community reports also identify thin/long polygons and tiny baked edges as merge-rasterization hazards. These external reports are source guidance, not Close Seal runtime evidence.

## Options evaluated

### Direct `vertices + add_polygon()` corridor quads
Rejected as the primary production path. It is the currently failing path and bypasses the normal source-geometry/baking pipeline. Keep only as a diagnostic fixture.

### Manual triangulation + direct polygon insertion
Useful A/B diagnostic, not preferred final architecture. It removes quad ambiguity but cannot by itself solve overlap, self-intersection, cell mismatch or raster merge conflicts.

### Indexed triangle Mesh + `NavigationMesh.create_from_mesh()`
Useful intermediate diagnostic. Godot requires triangle primitives with an index array. Safer than arbitrary polygons, but still not the full Recast-style source-geometry bake.

### Procedural source geometry → Godot bake
**Preferred production solution.** Compile semantic routes into simple non-overlapping triangle source geometry, feed `NavigationMeshSourceGeometryData3D`, and let `NavigationServer3D.bake_from_source_geometry_data()` generate final navigation topology. Explicitly align `cell_size` and `cell_height` between NavigationMesh and map.

Benefits: supported Godot path; engine owns polygonization; clean semantic-geometry/navigation-topology separation; future agent bake parameters fit naturally; compatible with later tiled navigation.

### Lower merge rasterizer cell scale
Fallback diagnostic/tolerance control, not first-line fix. It can reduce close-edge raster conflicts but may hide bad source geometry. Use only after topology validation and matching cell sizes, with exact configuration recorded.

### Tiled/chunked navigation
Future scalability path, not the explanation for the current isolated-route failure. First make one corridor bake/query correctly; then benchmark chunks independently.

## Proposed optimal sequence

1. Add compiler diagnostics: finite/duplicate vertices, zero-length segments, triangle area/winding, self-intersection, overlap and minimum edge length relative to cell size.
2. Explicitly match NavigationMesh and NavigationServer3D map `cell_size` / `cell_height`.
3. Keep manually triangulated direct-navmesh as an A/B diagnostic only.
4. Replace production corridor compilation with procedural source geometry + `bake_from_source_geometry_data()`.
5. Require synchronized physical evidence: endpoint snap, A→B path, route coverage and semantic/physical length divergence.
6. Only after physical success run avoidance-agent loads 10/50/100/500 and export throughput/congestion telemetry.
7. Preserve every failed variant and exact engine/config combination in ARCONT.
8. After monolithic stability, benchmark tiled/chunked navigation separately.

## Experiment update — source-geometry attempt 1

Close Seal commit `6dc98e7224f239f546ec6476a1fa92024a1c561f` replaced the active direct-polygon compiler with procedural triangle faces, `NavigationMeshSourceGeometryData3D.add_faces()`, and `NavigationServer3D.bake_from_source_geometry_data()` while retaining the direct-polygon path as a legacy diagnostic control.

The first CI execution did **not** reach Recast baking or physical path queries. `Map Authoring Providers` run `34749963271`, job `103704612413`, failed during the generated workspace build because `_configure_navigation_mesh()` attempted direct GDScript property assignment (`navigation_mesh.agent_radius = ...`). The exact Godot 4.7.2 source exposes and binds explicit methods such as `set_agent_radius()`, `set_agent_height()`, `set_agent_max_climb()`, `set_agent_max_slope()`, `set_cell_size()` and `set_cell_height()`.

This result therefore does **not** falsify the source-geometry/Recast hypothesis. It is an integration/API-usage failure before the candidate navigation pipeline was exercised. The remediation is to use the source-confirmed setters, then rerun the unchanged bake/query/crowd gates.

Evidence:

- Close Seal commit: `6dc98e7224f239f546ec6476a1fa92024a1c561f`
- workflow: `34749963271`
- job: `103704612413`
- failure stage: `Build physical Map Forge provider workspace`
- observed error: invalid direct access to `agent_radius` on `NavigationMesh`
- official source anchors: `scene/resources/navigation_mesh.h`, `scene/resources/navigation_mesh.cpp`, Godot 4.7.2-stable

## Promotion rule

No remediation here is validated yet. Promotion requires a Close Seal CI run on exact Godot 4.7.2 where the replacement compiler produces queryable routes and the physical navigation gate succeeds. Crowd claims additionally require the executable avoidance-agent gate.

## Sources consulted

Godot stable navigation documentation and class references; exact Godot 4.7.2 `NavigationMesh` and `NavigationMeshSourceGeometryData3D` source; Godot upstream issues #79217, #82209, #85548, #99334, #108263; Godot Forum discussion of manual NavigationMesh editing; r/godot discussions of merge-rasterizer conflicts, runtime navmesh generation, thin polygons and tiled terrain navigation.

Community material remains source guidance only until reproduced.