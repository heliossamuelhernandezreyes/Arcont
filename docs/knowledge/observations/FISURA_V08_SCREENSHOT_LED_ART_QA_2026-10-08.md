# FISURA 0.8 — screenshot-based visual QA observation

**Engine:** Godot 4.7.2-stable. **Source:** independent FISURA production repository. **Date:** 2026-10-08.

The Reactivo-13 mission passed map, animation and gameplay tests but real 1280×720 screenshots exposed a small on-screen player, an oversized flat blast door and repeated, brightly lit floors. An older architectural generator retained coordinates designed for a 44×44 scene, whereas the new map was 84×66. This is a concrete limit of technical validation without multi-view visual review.

### Reusable changes

- Design multiple screenshot viewpoints: insertion, node A, reactor, and boss fight, with reproducible positions.
- Check captures as binary evidence with `tools/viewport_evidence_gate.py`: PNG signature and IHDR CRC, same viewport size, substantial file size, distinct SHA256 hashes.
- Record protagonist silhouette/readability, landmark hierarchy, HUD obstruction, floor/material contrast and lighting.
- Keep gameplay geometry authored by mission/map contracts; ensure render-only dressing adds no collision.
- Require tactical ranged attacks to show meaningful telegraph before damage: Reactivo EyeDrone prototype uses a 0.72 s warning.

### Evidence boundaries

PNG integrity does not verify image origin or artistic quality. The game CI supplies source-versioned Godot execution logs, named positions and screenshots. Humans must inspect images and actual controls. Godot 4.7 Linux screenshots do not imply target Android frame pacing or thermal stability.

The Bulwark upgrade reuses an existing CC0 skinned machine and separate armored visual parts; it is not a unique high-budget rig. Geometry, light and VFX budgets are preliminary, not profiled device measurements. ARCONT is a generic technical laboratory: no production game or binary art is copied here.

### Next QA gates

1. Render comparison across four points with human accept/reject notes.
2. Runtime tests for charge/windup/damage fairness, animation state and crowd pressure.
3. Scene-performance counters and 15-minute physical Android frame-time/thermal validation.
4. Professionally authored boss silhouette, advanced animation blending and high-quality audio/art direction.
