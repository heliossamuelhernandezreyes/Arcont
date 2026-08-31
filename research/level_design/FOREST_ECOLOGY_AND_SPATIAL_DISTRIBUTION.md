# Arcont — Forest Ecology & Spatial Distribution

Status: REFERENCE / reference-lab
Date: 2026-08-31

## Purpose
Translate real forest structure into practical game-world generation rules. The goal is not botanical simulation for its own sake, but believable spatial logic that improves realism, navigation, sightline control, and performance.

## Core ecological principles
Real forests are heterogeneous mosaics. Tree positions, canopy gaps, regeneration, understory and deadwood are shaped by disturbance, competition, moisture, light, topography and stand history rather than uniform random scatter.

Research from the US Forest Service shows that intact or historically frequent-fire forests can exhibit clustered tree groups separated by gaps, and that this variability is an important structural feature. Other work shows canopy gaps alter light, soil moisture and regeneration, while slope aspect, elevation and landscape position can strongly influence understory distribution and canopy structure.

## Spatial model for Arcont
Use five nested spatial layers:
1. Macro stand zones — ridge, midslope, cove/toeslope, riparian strip, clearing/disturbance patch.
2. Canopy groups — clusters of mature trees with variable group size and spacing.
3. Canopy gaps — nonuniform openings created by terrain, disturbance or designed gameplay rooms.
4. Understory patches — shrubs, saplings, ferns/herbs and young trees responding to light/moisture.
5. Ground layer — litter, deadwood, roots, stones, mushrooms and microdetail.

Avoid Poisson-like uniform scatter as the final distribution. Use clustered point processes or noise fields with exclusion radii, then bias those fields by environmental masks.

## Environmental drivers
### Moisture
Use a derived moisture field rather than elevation alone. A practical approximation can combine:
- upslope contributing area / accumulated flow;
- local concavity or convexity;
- slope aspect and solar exposure;
- slope steepness;
- soil/water-holding class if authored;
- proximity to stream or wet depression.

A USFS GIS-derived Integrated Moisture Index combines slope-aspect shading, cumulative downslope water flow, landscape curvature and soil water-holding capacity. Arcont can adapt this idea into a normalized `moisture_index` map.

### Aspect and exposure
Aspect is a proxy, not a complete physical model, but it is useful. In Northern Hemisphere studies, south-facing slopes generally receive greater solar load and can be warmer/drier; north-facing slopes often support cooler/moister understory conditions. Do not encode a universal species rule solely from aspect: use aspect as one input to heat/moisture fields.

### Topographic position
Ridges, convex shoulders, midslopes, coves and toeslopes should not carry identical forest structure. Research reports changes in canopy height, biomass and understory density across elevation, exposure and convexity. For procedural generation, topographic position should affect tree density, average tree size, understory density and deadwood probability.

### Canopy gaps
Gaps are normal components of mature forests and increase landscape heterogeneity. Gap size and age can affect seedling density and species richness. In game terms, use gaps as ecological and tactical units rather than arbitrary empty circles.

## Practical distribution rules
Each vegetation species or family should expose:
- moisture preference curve;
- light/canopy preference;
- elevation range;
- slope range;
- aspect/heat tolerance;
- riparian affinity;
- cluster radius and cluster intensity;
- minimum spacing;
- succession/disturbance affinity;
- edge affinity;
- maximum density;
- LOD class;
- collision/gameplay importance.

The final placement probability should be the product or weighted blend of environmental suitability and a deterministic cluster field, then filtered by spacing and gameplay exclusions.

Suggested conceptual form:
`P = biome * moisture * slope * light * topographic_position * disturbance * cluster_noise * gameplay_mask`

Do not let any single environmental factor dominate unless a species deliberately requires it.

## Forest architecture for gameplay
- Dense tree groups become visual masses and occlusion tools.
- Gaps become combat rooms, landmarks or breathing spaces.
- Edges between forest and clearing receive transition vegetation rather than abrupt density changes.
- Trails should pass through weaker-density corridors and terrain saddles where possible.
- Riparian strips should read differently from dry ridges.
- Fallen logs and snags should correlate with mature stands, disturbance and wet areas rather than appear uniformly.
- Large hero trees should be placed compositionally, then the ecological scatter should support them.

## Deterministic implementation contract
EnvironmentScatter should generate a stable ecology field from a seed. Same seed + terrain + rules must reproduce the same forest.

Required derived maps:
- elevation;
- slope;
- aspect/solar exposure;
- curvature;
- flow accumulation;
- moisture index;
- distance-to-water;
- disturbance/clearing mask;
- gameplay exclusion mask;
- canopy-density field.

Required vegetation outputs:
- canopy anchors;
- canopy groups;
- saplings;
- shrubs;
- ground cover;
- deadwood;
- rocks linked to terrain/geology rules.

## Validation
The forest should fail review if:
- tree spacing is visibly uniform;
- density ignores terrain and water;
- all slopes have identical vegetation;
- clearings have hard artificial boundaries;
- understory density is independent of canopy/light;
- riparian zones are visually indistinguishable from uplands;
- deadwood/rocks are noise-scattered without ecological or terrain logic;
- combat readability is lost.

## Primary references
- USDA Forest Service Research: Lydersen et al. 2013, tree groups and gaps in mixed-conifer forests, https://research.fs.usda.gov/treesearch/44828
- USDA Forest Service Research: North et al. 2004, old-growth stand structure and clustered/gap patterns, https://research.fs.usda.gov/treesearch/24983
- USDA Forest Service Research: Iverson & Prasad 2003, GIS-derived Integrated Moisture Index, https://research.fs.usda.gov/treesearch/11583
- USDA Forest Service Research: Warren 2008/2009, slope aspect and understory distribution, https://research.fs.usda.gov/treesearch/33840
- USDA Forest Service Research: Clinton et al. 1994, canopy gaps/topographic position/regeneration, https://research.fs.usda.gov/treesearch/4703
- USDA Forest Service Research: Clinton 2003, light/temperature/soil moisture response to canopy gaps, https://research.fs.usda.gov/treesearch/6246
- USDA Forest Service Research: Dymond et al. 2017, topographic/vegetative controls on plant-available water, https://research.fs.usda.gov/treesearch/54881

## Arcont decision
Forest generation must be terrain- and ecology-conditioned. Pure random scatter is permitted only as an intermediate noise source, never as the final placement model.