# Arcont — Professional Environment Art & Lighting

Status: REFERENCE / reference-lab
Date: 2026-08-31

## Purpose
Turn physically plausible terrain into a professionally directed game environment. Ecological realism is not enough: the player needs visual hierarchy, navigation, contrast, readable combat spaces and deliberate mood.

## Production order
1. Intent and player experience.
2. Macro composition and silhouette.
3. Traversal and gameplay readability.
4. Material families and value structure.
5. Hero landmarks and secondary anchors.
6. Lighting and atmospheric depth.
7. Meso detail.
8. Microdetail and decals.
9. Optimization and real-device validation.

Do not begin with clutter.

## Composition
Every playable view should contain an intentional hierarchy rather than equal visual weight everywhere.

Use:
- dominant focal landmark;
- secondary anchors;
- foreground framing;
- midground gameplay/readability layer;
- background/horizon layer;
- controlled negative space;
- leading lines from trails, ridges, streams, light shafts or architecture.

In forests, dense trunks can produce strong visual rhythm but can also flatten depth. Break repetition with clearings, curved routes, terrain steps, hero trees, rock masses and changes in canopy height.

## Macro / meso / micro
Macro decides whether the environment reads from a screenshot at a distance: terrain silhouette, canopy mass, valley, river, landmark, sky.

Meso creates playable identity: tree clusters, major rocks, fallen logs, path junctions, banks, bridges, ruins, cover groups.

Micro sells material reality: leaves, twigs, bark variation, moss, small stones, decals, wetness and debris.

Performance budget should be spent in that order. Microdetail never repairs weak macro composition.

## Lighting as level design
Lighting must guide the player and explain form, not merely make the image brighter.

Useful patterns:
- brighter or warmer navigational destinations against calmer surroundings;
- silhouette contrast around important traversal openings;
- darker dense forest masses framing lighter clearings;
- directional sun to reveal terrain and trunk depth;
- atmospheric perspective to separate near/mid/far layers;
- local contrast near interactive or dangerous areas.

A GDC lighting-design reference emphasizes a common language between level design and lighting and treats light as part of player behavior and spatial communication, not post-decoration.

## Forest daylight
Start with one dominant sun/sky relationship. Avoid many realtime lights trying to fake natural daylight.

Canopy should modulate the scene spatially:
- dense canopy = darker/cooler ambient impression and stronger local shafts where appropriate;
- gaps = greater sky exposure, clearer value separation and stronger ground illumination;
- wet valleys/riparian pockets can carry softer haze;
- ridges can expose more sky and stronger directional light.

Do not overuse volumetrics on mobile. Most depth should come from value, fog, sky, silhouette and physically coherent material response.

## Color and materials
Choose a restrained environment palette with controlled variation. Forest realism comes from relationships, not maximizing saturation.

Material families should share calibrated PBR behavior:
- dry/wet soil;
- leaf litter;
- bark families;
- moss;
- exposed rock;
- wet rock;
- shallow-water bed;
- deadwood.

Use broad value/color zones first. Vertex/terrain blending, decals and detail textures should break repetition without creating noisy material soup.

## Atmospheric perspective
Distance should progressively simplify:
- lower microcontrast;
- fewer high-frequency normals;
- simpler materials;
- reduced small-shadow detail;
- haze/fog separation;
- HLOD/impostor silhouettes.

This is both artistic depth and performance optimization.

## Landmarks and navigation
A player should be able to answer 'where am I?' from environment shape alone.

Forest landmarks can be:
- unusually large/dead/split tree;
- distinctive rock formation;
- ridge notch;
- waterfall/river bend;
- bridge;
- clearing shape;
- tower/ruin if narrative allows;
- mountain/horizon silhouette.

Do not place landmarks uniformly. They need hierarchy and distinct silhouettes.

## Professional review gates
Before microdetail, capture views from:
- spawn/entry;
- every major route junction;
- main combat clearings;
- longest sightline;
- highest and lowest traversal points;
- river crossings;
- landmark approach and reveal.

Review each capture in grayscale as well as color. If route hierarchy and focal point disappear without color, composition is too dependent on hue.

## Mobile-aware art direction
On mobile, art direction must cooperate with the renderer:
- prefer big readable shapes over dense tiny geometry;
- spend shadows on hero forms;
- use alpha-scissor foliage where acceptable;
- reduce distant normal-map/material complexity;
- use fog and HLOD to simplify depth;
- avoid translucent layers covering large portions of screen;
- tune HDR/post effects only after bandwidth and thermal testing.

## Key references
- GDC Vault, Robert Yang, 'Lighting Design for Level Designers': https://www.gdcvault.com/play/1016450/Lighting-Design-for-Level
- Godot 4.7 rendering architecture and Mobile renderer: https://docs.godotengine.org/en/4.7/engine_details/architecture/internal_rendering_architecture.html
- Godot occlusion/LOD/HLOD guidance: https://docs.godotengine.org/en/4.7/tutorials/3d/occlusion_culling.html

## Arcont decision
Environment art is a gameplay system. Composition, ecology, performance and lighting must be reviewed together, not as independent passes.