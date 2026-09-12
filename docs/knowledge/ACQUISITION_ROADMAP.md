# ARCONT — Knowledge Acquisition Roadmap

The goal is broad coverage without turning ARCONT into an uncurated dump.

## Wave 0 — Taxonomy and source control

Status: STARTED.

- Game Development Atlas.
- Curated source registry.
- provenance/licensing rules.
- shared / 2D / 2.5D / 3D applicability.
- existing Evidence Ledger, Knowledge Graph, maturity and confidence machinery remain authoritative.

## Wave 1 — Fundamentals shared by almost every game

Acquire and extract primary material for:

- game loop, fixed/variable timestep and scheduling,
- coordinate systems/transforms,
- CPU/GPU frame pipeline,
- frame pacing and latency,
- memory/allocation/cache behavior,
- resources/assets/loading/streaming,
- input and UI,
- profiling and debugging,
- data/state/events and common architecture patterns.

Output: source cards + transferable claims + validation questions.

## Wave 2 — 2D

- sprites, atlases, batching and texture sampling,
- tilemaps/chunks and large 2D worlds,
- Canvas transforms/cameras/parallax,
- 2D lighting/shadows,
- particles and custom drawing,
- 2D collision/physics,
- 2D skeletal/sprite animation,
- navigation/grids/flow fields,
- pixel-art constraints and resolution scaling,
- mobile 2D performance.

## Wave 3 — 2.5D

Treat each implementation model separately:

- plane-constrained gameplay in a 3D scene,
- 2D sprites/billboards in 3D,
- orthographic/isometric 3D,
- layered depth and parallax worlds,
- hybrid 2D/3D collision,
- camera/depth sorting/transparency problems,
- lighting consistency between sprites and geometry,
- navigation and interaction across dimensional boundaries.

## Wave 4 — 3D

- mesh pipeline and vertex/index costs,
- materials/shaders/PBR,
- forward/deferred/tiled/clustered concepts,
- lighting/shadows/reflections/GI,
- visibility/frustum/occlusion,
- instancing, LOD/HLOD/impostors,
- skeletal animation, IK, ragdolls,
- rigid bodies/constraints/vehicles/destruction,
- navmeshes/agents/crowds,
- world partition/chunking/streaming,
- terrain/foliage/procedural worlds,
- VFX/particles/decals.

## Wave 5 — Systems that cut across dimensions

- AI/behavior/state/planning,
- multiplayer/replication/prediction/rollback,
- audio and spatialization,
- save systems and deterministic data migrations,
- procedural generation,
- accessibility,
- localization,
- testing and telemetry,
- security/anti-cheat concepts where legitimate and defensive.

## Wave 6 — Platform engineering

Priority starts with Android/mobile because it creates the harshest useful constraints for ARCONT's early research.

- Android frame pacing, refresh rates, thermals and power,
- Vulkan/OpenGL ES behavior,
- GPU/CPU profiling,
- memory pressure and storage,
- touch latency,
- device capability tiers,
- quality scaling.

Later: desktop, web, console and XR from publicly accessible primary material.

## Wave 7 — Cross-engine comparative studies

For a common problem, compare implementations rather than declaring an engine winner. Examples:

- scene/node/object lifecycle,
- rendering submission and batching,
- physics stepping,
- animation evaluation,
- navigation update strategies,
- resource loading,
- threading/job systems,
- mobile frame pacing.

Each comparison must separate public API, internal implementation, measured behavior and platform effects.

## Ingestion unit

Every acquired source should eventually produce a small source card with:

- stable ARCONT ID,
- source tier,
- canonical URL/reference,
- publisher/author,
- version/date,
- license/archival permission if known,
- dimensions/platforms/topics,
- extracted concepts (paraphrased),
- candidate claims,
- contradictions/open questions,
- experiments needed,
- graph/ledger relationships.

## Stop rule

Do not postpone experiments until the library is “complete”; it never will be. After Wave 1 has enough coverage to support clean experiments, acquisition and empirical research run in parallel. New sources are prioritized by the questions current experiments expose.