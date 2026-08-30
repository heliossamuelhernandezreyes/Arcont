# Environment Art Guide

## Goal
Build urban spaces that read clearly, support tactical combat and provide occlusion/performance structure at the same time.

## Modular kit
Define consistent module dimensions before producing volume: wall widths, floor heights, door openings, windows, curbs, road lanes, cover heights and prop categories. Validate every kit piece in the metric calibration scene.

## Composition hierarchy
- Macro: street shape, building masses, skyline, large occluders, landmarks.
- Meso: storefronts, barriers, vehicles, facade breakup, tactical cover.
- Micro: debris, signs, cables, stains and storytelling props.
Do not use microdetail to compensate for weak macro composition.

## Tactical readability
- Cover silhouettes should be obvious.
- Flank routes should read from spatial composition.
- Use lighting/color to support navigation without glowing every interactable.
- Keep enemy silhouettes separable from background values/colors.
- Avoid clutter around common aim heights.

## Mobile-friendly urbanism
- Use buildings and walls as natural occluders.
- Limit extremely long uninterrupted sightlines unless intentionally budgeted.
- Use visibility ranges/HLOD for distant facade/prop groups.
- Simplify distant materials as well as geometry when profiling supports it.
- Prefer opaque geometry and atlas/reuse over layers of transparency.
- Consider MultiMesh for repeated low-interaction elements.

## Surface storytelling
Use layered logic rather than random dirt:
1. Base construction material.
2. Age/weather exposure.
3. Human use/contact wear.
4. Conflict/destruction.
5. Recent event-specific traces.

## Destruction
Author clear intact/damaged/destroyed states for gameplay-critical cover. Cosmetic debris should have strict lifetime/performance policies.

## Calibration anchors
Maintain recognizable metric references: ~2.1 m door, ~1 m cover, ~4.5 m passenger vehicle, human ~1.75–1.85 m. An environment pass is blocked if these proportions do not read naturally together.
