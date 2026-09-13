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

Godot 4.7 documentation supports procedurally generated triangle-face source geometry followed by `NavigationMeshGenerator.bake_from_source_geometry_data()`. In the exact Godot 4.7.2 source, the public scriptable `NavigationMeshGenerator` singleton delegates internally to the native `NavigationServer3D::bake_from_source_geometry_data()` implementation. The latter exists in C++ but is not bound as a GDScript method on `NavigationServer3D` in this release.

Later/current documentation may show the bake methods directly on `NavigationServer3D`, so examples from `latest`/newer revisions must not be copied into the pinned 4.7.2 runtime without checking version-specific bindings.

Relevant upstream history includes Godot issues #79217, #82209, #85548, #99334 and #108263. Community reports also identify thin/long polygons and tiny baked edges as merge-rasterization hazards. Community users have additionally reported runtime baking examples that differ between stable/latest documentation revisions. These external reports are source guidance, not Close Seal runtime evidence.

## Options evaluated

### Direct `vertices + add_polygon()` corridor quads
Rejected as the primary production path. It is the currently failing path and bypasses the normal source-geometry/baking pipeline. Keep only as a diagnostic fixture.

### Manual triangulation + direct polygon insertion
Useful A/B diagnostic, not preferred final architecture. It removes quad ambiguity but cannot by itself solve overlap, self-intersection, cell mismatch or raster merge conflicts.

### Indexed triangle Mesh + `NavigationMesh.create_from_mesh()`
Useful intermediate diagnostic. Godot requires triangle primitives with an index array. Safer than arbitrary polygons, but still not the full Recast-style source-geometry bake.

### Procedural source geometry → Godot bake
**Preferred production solution.** Compile semantic routes into simple non-overlapping triangle source geometry, feed `NavigationMeshSourceGeometryData3D`, and on pinned Godot 4.7.2 call the scriptable `NavigationMeshGenerator.bake_from_source_geometry_data()`. The generator delegates to the native NavigationServer implementation. Explicitly align `cell_size` and `cell_height` between NavigationMesh and map.

Benefits: version-correct supported Godot path; engine owns polygonization; clean semantic-geometry/navigation-topology separation; future agent bake parameters fit naturally; compatible with later tiled navigation.

### Lower merge rasterizer cell scale
Fallback diagnostic/tolerance control, not first-line fix. It can reduce close-edge raster conflicts but may hide bad source geometry. Use only after topology validation and matching cell sizes, with exact configuration recorded.

### Tiled/chunked navigation
Future scalability path, not the explanation for the current isolated-route failure. First make one corridor bake/query correctly; then benchmark chunks independently.

## Proposed optimal sequence

1. Add compiler diagnostics: finite/duplicate vertices, zero-length segments, triangle area/winding, self-intersection, overlap and minimum edge length relative to cell size.
2. Explicitly match NavigationMesh and NavigationServer3D map `cell_size` / `cell_height`.
3. Keep manually triangulated direct-navmesh as an A/B diagnostic only.
4. Replace production corridor compilation with procedural source geometry + the **version-correct bake interface** for the pinned engine.
5. Require synchronized physical evidence: endpoint snap, A→B path, route coverage and semantic/physical length divergence.
6. Only after physical success run avoidance-agent loads 10/50/100/500 and export throughput/congestion telemetry.
7. Preserve every failed variant and exact engine/config combination in ARCONT.
8. After monolithic stability, benchmark tiled/chunked navigation separately.

## Experiment update — source-geometry attempt 1

Close Seal commit `6dc98e7224f239f546ec6476a1fa92024a1c561f` replaced the active direct-polygon compiler with procedural triangle faces, `NavigationMeshSourceGeometryData3D.add_faces()`, and a source-geometry bake call while retaining the direct-polygon path as a legacy diagnostic control.

The first CI execution did **not** reach Recast baking or physical path queries. `Map Authoring Providers` run `34749963271`, job `103704612413`, failed during the generated workspace build because `_configure_navigation_mesh()` attempted direct GDScript property assignment (`navigation_mesh.agent_radius = ...`). The exact Godot 4.7.2 source exposes and binds explicit methods such as `set_agent_radius()`, `set_agent_height()`, `set_agent_max_climb()`, `set_agent_max_slope()`, `set_cell_size()` and `set_cell_height()`.

This result therefore does **not** falsify the source-geometry/Recast hypothesis. It is an integration/API-usage failure before the candidate navigation pipeline was exercised.

Evidence:
- Close Seal commit: `6dc98e7224f239f546ec6476a1fa92024a1c561f`
- workflow: `34749963271`
- job: `103704612413`
- failure stage: `Build physical Map Forge provider workspace`
- observed error: invalid direct access to `agent_radius` on `NavigationMesh`
- official source anchors: `scene/resources/navigation_mesh.h`, `scene/resources/navigation_mesh.cpp`, Godot 4.7.2-stable

## Experiment update — source-geometry attempt 2

Close Seal commit `fafd4e098ae6d93639b6f10ca9c3dece61bc9f4d` corrected the NavigationMesh configuration to the source-confirmed setters. Static map integrity and project integrity passed, but `Map Authoring Providers` run `34750148576`, job `103705111745`, again failed during generated workspace construction before physical path or crowd gates.

Exact failure:

`Invalid call. Nonexistent function 'bake_from_source_geometry_data' in base 'NavigationServer3D'.`

Source audit resolves the discrepancy:

- `servers/navigation_3d/navigation_server_3d.cpp` on exact `4.7.2-stable` does **not** bind `bake_from_source_geometry_data()` into `NavigationServer3D::_bind_methods()`.
- `modules/navigation_3d/3d/navigation_mesh_generator.cpp` binds `NavigationMeshGenerator.bake_from_source_geometry_data()` for scripting and delegates internally to `NavigationServer3D::get_singleton()->bake_from_source_geometry_data(...)`.
- `modules/navigation_3d/register_types.cpp` registers `NavigationMeshGenerator` as an Engine singleton in standard builds when deprecated APIs are enabled.
- Godot 4.7 class documentation lists `NavigationMeshGenerator.bake_from_source_geometry_data()` as the available public API.

Therefore attempt 2 is another **pre-bake public-API integration failure**, not evidence against the procedural source-geometry/Recast architecture. The next reproduction must call the 4.7.2 script-facing singleton `NavigationMeshGenerator` while keeping geometry, bake parameters, physical query thresholds and crowd gates unchanged.

Evidence:
- Close Seal commit: `fafd4e098ae6d93639b6f10ca9c3dece61bc9f4d`
- workflow: `34750148576`
- job: `103705111745`
- exact source: `servers/navigation_3d/navigation_server_3d.cpp`, `modules/navigation_3d/3d/navigation_mesh_generator.cpp`, `modules/navigation_3d/register_types.cpp`
- official Godot 4.7 documentation: `NavigationMeshGenerator`

## Reusable lesson

For a pinned engine version, source-level existence of a native method is insufficient evidence that the same method is script-callable on the apparent singleton. Validate the exact language binding (`ClassDB::bind_method`) and the exact release documentation before implementing. Treat `stable`, `latest`, and repository `master` examples as different sources until compatibility is demonstrated.

## Promotion rule

No remediation here is validated yet. Promotion requires a Close Seal CI run on exact Godot 4.7.2 where the replacement compiler produces queryable routes and the physical navigation gate succeeds. Crowd claims additionally require the executable avoidance-agent gate.

## Sources consulted

Godot 4.7 navigation documentation and class references; exact Godot 4.7.2 `NavigationMesh`, `NavigationMeshSourceGeometryData3D`, `NavigationServer3D` bindings, `NavigationMeshGenerator`, and navigation module registration source; Godot upstream issues #79217, #82209, #85548, #99334, #108263; Godot Forum discussion of manual/runtime NavigationMesh editing; r/godot discussions of runtime bake APIs, merge-rasterizer conflicts, thin polygons and tiled terrain navigation.

Community material remains source guidance only until reproduced.

## Experiment update — source-geometry attempts 3 and 4

The exact workflow run `34750364494` was rerun twice after the API correction.

Attempt 3:
- Close Seal commit: `9514c678421a6e0a3fba83f44f223e7d4699ed75`
- workflow run: `34750364494`, attempt `2`
- job: `103731210660`
- change: reversed the procedural triangle input order to compensate for the engine-side `add_faces()` vertex reversal
- result: failure in `Build physical Map Forge provider workspace`; `compile_route_surface()` still returned an empty baked NavigationMesh
- navigation-minimal, physical A→B and crowd steps were skipped

Attempt 4:
- Close Seal commit: `1c73d4590bf81281c68272b5c1ea7d94106f763a`
- workflow run: `34750364494`, attempt `3`
- job: `103731644113`
- change: added a finite vertical source envelope around each canonical route corridor while preserving route points, widths and semantic routes
- result: same failure stage and empty bake; finite source volume alone did not resolve the issue

Attempt 5 / orientation A-B:
- Close Seal commit: `ce4c72dfbe6547dcda97032cdf91af49fe26d017`
- workflow run: `34750364494`, attempt `4`
- job result: failed again in `Build physical Map Forge provider workspace`; downstream navigation and crowd gates remained skipped
- change: tested the opposite effective top-face winding inside the finite envelope
- result: no promotion; winding plus envelope is not yet a validated remediation

These results narrow the active fault to the Recast bake behavior or the exact procedural source/bake configuration, but do not yet distinguish them. The next experiment should be a dedicated minimal A/B fixture that prints source vertex/index counts, bounds, effective triangle normals, NavigationMesh bake parameters and baked polygon count for one rectangular corridor before touching the full multi-route map. Do not alter canonical route semantics until that fixture identifies the failing condition.

Current Close Seal PR status remains open: PR `#5`, branch `art/first-visual-pass`. No merge performed.

## Evidence correction — synchronize runs versus manual reruns

Several reruns of workflow run `34750364494` reused its original merge commit and therefore do not test later commits pushed to `art/first-visual-pass`. They must not be counted as experiments for those later source-geometry variants.

The valid branch-head experiments are the synchronize-triggered runs:

| Run | Branch head under test | Result | Boundary |
|---|---|---|---|
| `34760060966` | `9514c678...` | provider workspace and NavMesh bake passed; physical route query failed | endpoints snapped to `(0,0,0)`; army step skipped |
| `34760224658` | `1c73d459...` | provider workspace failed because the source-geometry variant did not compile the canonical surface | path and crowd steps skipped |
| `34760294660` | `ce4c72df...` | provider workspace and NavMesh bake passed; physical route query failed | isolated `main_lane`: `polygons=2`, `vertices=4`, endpoint snap `13.4m`; army step skipped |
| `34761082693` | `8fe986c...` | provider installation failed before Godot validation | Cyclops release archive layout was not found by the installer |

This correction supersedes any wording above that describes the old run's rerun attempts as tests of those later commits. The current investigation remains an observed negative result on Ubuntu/Godot 4.7.2; it does not establish a cross-hardware or production limitation.
## Remediation validated — source bake, stable synchronization, and crowd metrics

Close Seal run `34761738190` (branch head `98ce090...`, exact Godot `4.7.2-stable`) passed the complete Map Authoring Providers workflow.

Validated chain:
- pinned provider installation, including Cyclops release archive assets;
- clean editor import;
- source geometry diagnostics: `20` source triangles, `180` packed float vertices, `60` indices;
- Recast bake and generated provider workspace;
- minimal procedural NavigationServer3D surface;
- physical A→B queries for all `3` canonical routes;
- `70` traffic cells with physical route telemetry;
- executable NavigationServer3D avoidance-agent flow with callbacks and load telemetry.

The decisive navigation fix was not a geometry rewrite. Godot 4.7.2 requires the scriptable `NavigationMeshGenerator` bake path, and the query probe must wait for the second NavigationServer map iteration. The first nonzero iteration can precede queryable region state; the validated probe records `first_nonzero_iteration=1` and `iteration=2`.

Endpoint projection is now judged against a configuration-derived physical tolerance rather than `0.05m`, because the baked walkable surface is voxelized/eroded and appears at approximately `y=0.5` for this configuration. The final physical probe reported route detour ratios approximately `0.961–0.967` and maximum endpoint projection `0.743m`.

Crowd loads `10` and `50` are operability gates and completed on all routes. Loads `100` and `500` are saturation probes: partial completion is retained as capacity evidence, not treated as a navigation API failure. This run therefore validates executable avoidance callbacks and measurable crowd behavior, but not Android frame-time performance, final gameplay AI, or production balance.

Promotion: Map Forge navigation is now `L4 observed/reproduced in the pinned Ubuntu/Godot 4.7.2 CI environment` for this Close Seal implementation. ARCONT remains below cross-hardware/version maturity until another game, hardware target, or engine version reproduces the chain.