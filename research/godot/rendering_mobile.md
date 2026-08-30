# Godot — Mobile Rendering

## Arcont target
Android-first visual scalability. Production decisions must be measured on representative phones, not inferred from desktop performance.

## Cost centers to watch
- Draw calls and material/state changes.
- Transparent overdraw: smoke, blood, particles, foliage, decals.
- Shadowed lights.
- Skinned character vertex cost.
- Morph targets.
- Large screen-space effects.
- Shader complexity and texture bandwidth.
- Excessive unique materials.
- Too many simultaneously detailed animated enemies.

## Strategies
- Mobile renderer on capable Android targets; maintain fallback strategy as required.
- Visibility ranges and HLOD-style grouping.
- Mesh LOD and reduced enemy detail at distance.
- Occlusion culling where urban geometry provides useful occluders.
- Conservative shadow budgets.
- Particle LOD and capped gore effects.
- Texture compression and sensible texture resolution.
- Reuse materials/atlases when production art permits.
- Profile CPU and GPU independently.

## Urban design implication
Use large buildings/walls as natural occluders; arrange sight corridors deliberately. Small props should disappear/LOD before they become expensive sub-pixel detail.

## References
- Godot 3D optimization: https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html
- GPU optimization: https://docs.godotengine.org/en/stable/tutorials/performance/gpu_optimization.html
- Occlusion culling: https://docs.godotengine.org/en/stable/tutorials/3d/occlusion_culling.html
- Visibility ranges/HLOD: https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html
- Rendering architecture: https://docs.godotengine.org/en/4.7/engine_details/architecture/internal_rendering_architecture.html

## Status
Scalable performance budget exists in production. Detailed hardware budgets and benchmark scenes remain OPEN.
