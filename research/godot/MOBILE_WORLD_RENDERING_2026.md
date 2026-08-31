# Arcont — Mobile World Rendering 2026

Status: REFERENCE / reference-lab
Date: 2026-08-31

## Purpose
Define the current mobile-first rendering and scalability rules for large outdoor Arcont maps in Godot 4.x, with Android as the primary target.

## Renderer baseline
Godot's Mobile renderer is designed for mobile GPU constraints: battery, heat and memory bandwidth. Mobile GPUs are typically tile-based and benefit from minimizing render passes, bandwidth and overdraw. Forward+ is substantially less efficient on mobile-class hardware and should not be assumed as the default performance target.

For Android, Vulkan is the primary low-level graphics API according to current Android game-development guidance. Arcont should target Godot's Vulkan-based Mobile renderer where supported and keep a compatibility path only when device coverage requires it.

## LOD stack
Use all levels together rather than expecting one feature to solve world cost.

1. Imported mesh LOD — Godot automatically generates mesh LOD for imported 3D scenes and chooses LOD by screen coverage.
2. Manual HLOD / visibility ranges — replace many nearby objects with cheaper grouped geometry or impostors at distance.
3. Spatial chunking — split repeated scenery so frustum/occlusion culling can remove whole cells.
4. Impostors/cards — far trees and canopy masses should become very cheap representations.
5. Disappearance — microdetail should have finite visibility.

Automatic mesh LOD and manual visibility ranges can coexist.

## MultiMesh policy
MultiMesh is essential for repeated forest objects because thousands of individual MeshInstance3D submissions are expensive. However, every instance in one MultiMesh is spatially treated as one object for culling and uses the same selected mesh LOD at a given time.

Therefore:
- never build one forest-wide MultiMesh;
- partition by spatial cell;
- partition by asset/material/LOD class where beneficial;
- keep collision/gameplay objects outside decorative MultiMeshes;
- keep cell AABBs tight;
- tune cell size empirically against draw calls and culling efficiency.

Initial forest cell test range remains approximately 32–64 m for trees and 24–40 m for ground scatter, but these are benchmark candidates, not canon.

## HLOD ladder for forest
Near:
- LOD0/automatic high detail;
- selected shadow casters;
- full foliage material only where screen contribution justifies it.

Mid:
- lower automatic LOD or authored simplified mesh;
- cheaper material;
- reduced or disabled shadows on low-value trees;
- lower wind complexity.

Far:
- grouped canopy/trunk HLOD or Sprite3D/impostor;
- no local collision;
- no expensive normal mapping where imperceptible;
- minimal wind.

Very far:
- horizon canopy card/silhouette or no object.

## Occlusion and terrain
Godot documents that occlusion culling can provide particularly strong benefits with the Mobile renderer because Mobile does not use Forward+'s depth prepass. Outdoor forest scenes have fewer ideal occluders than interiors, so occlusion must be designed into the map.

Use:
- ridges;
- rock walls;
- dense opaque terrain masses;
- large structures;
- curved paths and valleys.

Do not expect individual tree trunks or tiny rocks to justify CPU occlusion cost. LOD/HLOD and visibility ranges remain primary tools for open views.

## Foliage transparency and overdraw
Tile-based mobile GPUs are sensitive to bandwidth and overlapping transparent layers.

Rules:
- prefer opaque geometry where possible;
- prefer alpha scissor/alpha testing to full alpha blending for leaf cards when quality is acceptable;
- avoid many stacked foliage planes filling the screen;
- reduce distant foliage material complexity;
- cap ground-cover density near the camera based on measured overdraw;
- avoid large translucent fog cards stacked through the entire forest.

## Lighting
Use one dominant DirectionalLight3D for outdoor sun/moon and let environment/sky/lightmaps carry broad illumination.

Godot's Mobile renderer has explicit per-mesh light limits and shadowed lights are significantly more expensive than unshadowed lights. Natural forest daylight should not be represented with many realtime local lights.

For static or mostly static areas, evaluate LightmapGI where compatible with the map workflow and memory budget. Dynamic lights are for gameplay events and hero moments.

## Adaptive quality controller
Arcont should not expose a static Low/Medium/High selector only. Build a runtime quality controller capable of changing world cost while preserving gameplay.

Candidate controls:
- internal render scale;
- tree visibility distance;
- HLOD transition multiplier;
- ground-cover density/range;
- shadow distance/quality;
- number of shadow-casting dynamic lights;
- particle density;
- water/reflection quality;
- post-processing quality;
- environmental effects density.

Adjust slowly with hysteresis. Do not visibly pump quality every few frames.

## Sustainable performance
Peak benchmark FPS is insufficient. Android documentation emphasizes thermal throttling: prolonged CPU/GPU load heats the device, reducing clocks and therefore performance.

Test sustained sessions and record:
- average frame time;
- 1%/slow-frame behavior where available;
- CPU/GPU bottleneck indication;
- thermal state;
- render scale and quality tier;
- battery/power behavior when practical.

The quality system should respond proactively to thermal pressure rather than waiting for severe throttling.

## Android platform guidance
Current Android guidance provides:
- Thermal API / ADPF for dynamic thermal and CPU management;
- Game Mode/Game State APIs for performance vs battery preference;
- Android Frame Pacing (Swappy) for smooth presentation in native/OpenGL/Vulkan engines;
- Android GPU Inspector and system profilers for GPU analysis;
- Vulkan Profiles for defining device capability targets in native renderers.

Godot abstracts much of the native renderer, so integrate platform-specific APIs only when they can be supported cleanly through the engine/plugin layer. The design principle remains valid even when an API is not directly exposed.

## Performance acceptance matrix
Every map build should benchmark at least:
- spawn/static view;
- walking through dense understory;
- longest view across valley/river;
- dense canopy looking toward sun;
- rapid camera pan;
- combat + particles;
- sustained 15–30 minute traversal/combat session on real Android hardware.

A desktop CI screenshot proves correctness, not mobile performance.

## Primary references
- Godot 4.7 internal rendering architecture: https://docs.godotengine.org/en/4.7/engine_details/architecture/internal_rendering_architecture.html
- Godot occlusion culling: https://docs.godotengine.org/en/4.7/tutorials/3d/occlusion_culling.html
- Godot visibility ranges/HLOD: https://docs.godotengine.org/en/4.6/tutorials/3d/visibility_ranges.html
- Godot mesh LOD/MultiMesh behavior: https://docs.godotengine.org/en/4.6/tutorials/3d/mesh_lod.html
- Android power efficiency / Thermal API / Game Mode, updated 2026-02-26: https://developer.android.com/games/optimize/power
- Android Dynamic Performance Framework, updated 2026-02-27: https://developer.android.com/games/optimize/adpf
- Android Vulkan native engine support: https://developer.android.com/games/develop/vulkan/native-engine-support
- Android Frame Pacing: https://developer.android.com/games/sdk/frame-pacing

## Arcont decision
Performance target is sustained mobile quality. World density, LOD, shadows and render scale must be runtime-scalable and validated on device.