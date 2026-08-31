# Arcont Reference Index

This branch is the project research/reference lab. It stores audited guides, external references, decisions, gaps, and source/provenance policy. Runtime code must not absorb research blindly: promote only after implementation and validation.

## Core governance
- `research/AUDIT_PROTOCOL.md` — how references and implementation claims are audited.
- `research/DECISIONS.md` — project decisions and accepted constraints.
- `research/KNOWLEDGE_GAPS.md` — unresolved questions and validation gaps.
- `research/FULL_GAME_AUDIT_2026-08-29.md` — historical whole-project audit snapshot.
- `research/REALISTIC_ASSET_WAREHOUSE.md` — realistic asset-source warehouse and promotion policy.

## Level design / world construction
- `research/level_design/MAP_CREATION_AND_MOBILE_WORLD_GUIDE.md` — map workflow, chunking, LOD/HLOD, scatter and validation baseline.
- `research/level_design/REALISTIC_FOREST_SETTLEMENT_CONSTRUCTION_GUIDE.md` — believable forest/settlement construction and mobile foliage rules.
- `research/level_design/URBAN_VILLAGE_ASSEMBLY.md` — urban/village composition reference.
- `research/level_design/FOREST_ECOLOGY_AND_SPATIAL_DISTRIBUTION.md` — ecology-conditioned forest distribution: groups, gaps, moisture, aspect, topographic position and deterministic scatter inputs.
- `research/level_design/TERRAIN_HYDROLOGY_AND_GEOMORPHOLOGY.md` — drainage-first terrain, rivers, erosion, rock placement, ridges/valleys and traversal landforms.

## Art direction
- `research/art/ART_BIBLE.md` — visual-direction baseline.
- `research/art/ENVIRONMENT_ART.md` — environment-art principles.
- `research/art/LIGHTING.md` — lighting baseline.
- `research/art/MATERIALS_PBR.md` — PBR material policy.
- `research/art/MOBILE_VISUAL_BUDGETS.md` — mobile visual-budget baseline.
- `research/art/ART_AUDIT_CHECKLIST.md` — visual acceptance checklist.
- `research/art/PROFESSIONAL_ENVIRONMENT_ART_AND_LIGHTING.md` — professional composition, hierarchy, landmarks, forest lighting and mobile-aware art direction.
- `research/art/AI_ASSET_PIPELINE.md` — AI-assisted asset workflow constraints.
- `research/art/ANIMATION_QUALITY.md` — animation quality research.
- `research/art/CHARACTERS.md` — character-art research.
- `research/art/MODEL_ASSET_CATALOG.md` — model asset catalog.

## Godot technical references
- `research/godot/rendering_mobile.md` — mobile renderer notes.
- `research/godot/performance.md` — performance principles.
- `research/godot/navigation.md` — navigation reference.
- `research/godot/resources_architecture.md` — resource architecture.
- `research/godot/input_mobile.md` — mobile input.
- `research/godot/camera_tps.md` — TPS camera reference.
- `research/godot/animation.md` — animation architecture reference.
- `research/godot/audio.md` — audio reference.
- `research/godot/MOBILE_WORLD_RENDERING_2026.md` — current large-world mobile rendering policy: Godot Mobile, Vulkan-era Android guidance, LOD/HLOD, MultiMesh chunking, sustained performance, thermal adaptation and frame pacing.

## External source / provenance policy
- `research/references/POLY_HAVEN_INGEST_AND_PROVENANCE_2026.md` — approved Poly Haven CC0 ingest, provenance and runtime-derivative policy.

## Forest-map working synthesis
For the new forest map, consume the lab in this order:
1. terrain drainage and macro landforms;
2. gameplay routes / clearings / landmarks;
3. derived terrain fields: slope, aspect, curvature, flow and moisture;
4. ecology-conditioned canopy groups and gaps;
5. rocks/deadwood/riparian detail from terrain logic;
6. professional composition and lighting pass;
7. chunked MultiMesh + automatic LOD + authored HLOD/impostors;
8. adaptive quality and real Android profiling.

## Required implementation tools still to build or validate
- `EnvironmentScatter`: deterministic placement from ecology/terrain/gameplay masks into spatially chunked optimized outputs.
- `MapValidator`: automated warnings for texture/material/visibility/shadow/MultiMesh/nav/sightline/VFX problems.
- terrain analysis baker: elevation, slope, aspect, curvature, flow accumulation, moisture and distance-to-water maps.
- HLOD/impostor builder for forest cells.
- mobile adaptive quality controller with hysteresis and sustained-performance telemetry.

## Promotion rule
Reference-lab is evidence and design guidance. It is not runtime canon by itself. New runtime systems must cite the relevant lab rules, define measurable acceptance criteria, and be tested visually and on Android before promotion.