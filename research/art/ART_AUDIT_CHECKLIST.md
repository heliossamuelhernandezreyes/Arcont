# Art Audit Checklist

Use this for every asset set, scene milestone and visual regression review.

## Technical validity
- Metric bounds make sense.
- Pivot/orientation/naming are consistent.
- Collision is appropriate.
- Character rig/bone mapping/rest pose validated.
- Tangents/normals correct where required.
- No accidental 100x/0.01x transform compensation chains.

## Visual design
- Silhouette readable at gameplay distance.
- Primary/secondary/tertiary form hierarchy exists.
- Faction/role language is recognizable.
- Detail density is controlled.
- Color accents have purpose.

## Materials
- PBR logic plausible.
- Roughness defines material identity.
- Metallic values physically sensible.
- Texture scale/texel density coherent with neighbors.
- Albedo is not carrying baked fake lighting.
- Normal detail survives screen-space size.

## Lighting response
- Reads under neutral calibration.
- Reads under current Arcont environment.
- Threats remain visible in dark values.
- Highlights do not clip distractingly.
- Local shadow lights justify their cost.

## Animation / characters
- No bind/T-pose at runtime.
- Feet/weapon/hands remain convincing.
- Transitions do not pop.
- ADS and locomotion layers coexist.
- Damage state does not destroy silhouette/readability.

## VFX
- Effect communicates cause immediately.
- Critical telegraphs dominate cosmetic effects.
- Transparency footprint is tight.
- Particle/decal lifetime is capped.
- Worst-case overlap tested.

## Mobile
- Check on target phone, not only editor screenshot.
- Measure frame pacing and GPU/CPU time.
- Inspect thermal degradation.
- Inspect readability at real physical screen size.
- Verify LOD transitions are not distracting.

## Decision
Assign one status: BLOCKED / PROXY / ART-PASS-1 / ART-PASS-2 / MOBILE-VALIDATED / FINAL-CANDIDATE.
Record why and what must happen before promotion.
