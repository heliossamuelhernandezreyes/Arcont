# Map authoring toolchain — ARCONT

Status: source-traced architecture decision. No runtime maturity is claimed by this document.

## Objective

Evaluate permissively licensed Godot map-authoring tools for production projects without embedding a production game inside ARCONT.

## Selected ecosystem

- **Terrain3D** — preferred terrain authoring provider.
- **Cyclops Level Builder** — preferred structural blockout / brush geometry provider.
- **ProtonScatter** — preferred environment population/scatter provider.
- **FuncGodot** — optional interchange route for `.map` / VMF and external brush editors.

All four selected codebases expose permissive MIT licensing at the reviewed upstreams. License compatibility does **not** imply that every demo texture, model, sound or third-party asset is covered by the same terms; those assets remain independently auditable.

## Canonical architectural rule

A production game must not make one of these plugins its map format.

The production project owns a stable, engine-facing map contract. Third-party tools are adapters/providers around that contract:

```text
Terrain3D -----------\
Cyclops --------------> project Map Forge -> canonical map contract -> runtime map
ProtonScatter --------/
FuncGodot -----------/       optional import/interchange only
```

Consequences:

1. Map gameplay metadata remains plugin-neutral.
2. A provider can be upgraded or replaced without rewriting gameplay semantics.
3. Runtime maps do not depend on editor-only classes.
4. Generated geometry/terrain can be baked or referenced separately from gameplay metadata.
5. Native Godot nodes remain a fallback path for tests and CI.

## Close Seal recommendation

For an RTS / Hero RTS workflow:

- Terrain3D: ground, slopes, rivers, cliffs, masks and large-scale terrain.
- Cyclops: walls, bridges, ruins, fortresses, lanes, hard-surface blockout and chokepoint geometry.
- ProtonScatter: trees, rocks, bushes, debris and biome dressing.
- FuncGodot: optional external brush-map interchange and study of entity-definition workflows.
- Close Seal Map Forge: bases, objectives, camps, spawn points, tower anchors, routes, tactical regions, formation-width annotations, navigation validation and balance metadata.

## Validation boundary

Current maturity is **L1: source-traced**. Do not promote claims such as performance, stability on Android, exact compatibility with Godot 4.7.2, navigation interoperability, or safe production scale until measured by a reproducible experiment.

Required experiments are recorded in `MAP_AUTHORING_TOOLCHAIN.yaml`.

## Rejection criteria

A provider should be removed or isolated if it:

- writes opaque gameplay-critical data that cannot be migrated;
- prevents deterministic/source-control-friendly map serialization;
- blocks Android export;
- introduces unacceptable editor instability;
- causes navigation or rendering regressions outside budget;
- has license/provenance ambiguity in code required by the project.

## Rule for production repositories

Vendor or pin dependencies in the production repository, preserve required notices, and keep `THIRD_PARTY_NOTICES` current. ARCONT stores the research, evidence and decisions rather than becoming the dependency host.
