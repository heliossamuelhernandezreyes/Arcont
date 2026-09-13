# Map Forge Physical Provider Bridge Observation

**ID:** `ARC-GODOT-OBS-MAP-PROVIDER-BRIDGE-0001`  
**Status:** observed  
**Maturity:** L3 — one production repository / one pinned Godot environment  
**Observed:** 2026-09-13

## Scope

Close Seal Map Forge 0.4 adds a one-way physical authoring bridge from the game-owned canonical map contract into optional third-party authoring providers while preserving the contract as the source of truth.

Observed production revision:

`cf3b4e09809d4f2d793b30f7bd2367fbcd9174b2`

Branch: `art/first-visual-pass`

Environment:

- Godot `4.7.2-stable`
- canonical engine commit `ed1daf0bf001b61586d9930840f2f1394092c079`
- GitHub Actions Linux runner
- exact pinned Terrain3D, Cyclops Level Builder, ProtonScatter and FuncGodot revisions from the Close Seal authoring lockfile

## Materialized bridge

`addons/close_seal_map_forge/map_forge_provider_bridge.gd` builds a generated authoring scene from canonical map semantics.

Observed generated layers:

- `Terrain` — Terrain3D node when the GDExtension class is available; native fallback envelope otherwise.
- `Structures` — Cyclops workspace when the provider script is available plus provider-neutral structure guides and fortress sockets.
- `Scatter` — ProtonScatter node plus real ProtonScatter box-shape zones when installed; native fallback guides otherwise.
- `GameplayGuides` — bases, hero spawns and objectives.
- `NavigationGuides` — route corridors and choke guides.
- `Import` — FuncGodot import socket.

The generated scene and manifest live under `maps/generated/` in the working checkout. Generated provider data is derivative and does not replace the canonical `maps/*.json` contract.

## Authoring semantics added

The canonical map can now carry provider-neutral `authoring` data for:

- terrain data directory, vertex spacing and region size;
- structure guides with position and size;
- scatter/environment zones with center, size and density.

Both the Godot contract validator and editor-independent Python CI validator reject malformed authoring data.

## Validation

Close Seal workflow results at the observed revision:

- `Map Authoring Providers` — run `34747206030` — success.
- `Map Contract Integrity` — run `34747206050` — success.
- `Closeseal Project Integrity` — run `34747206035` — success.
- `Real Prototype Screenshot` — run `34747206034` — success.

The provider workflow performed:

1. exact provider installation;
2. first Godot import pass;
3. clean second Godot editor startup;
4. execution of `tools/map_forge_provider_smoke.gd`;
5. physical authoring-scene generation;
6. reload/instantiation of the generated PackedScene;
7. verification that required generated layers exist;
8. verification that available Terrain3D and Cyclops providers materialize;
9. verification that ProtonScatter materializes the four declared scatter zones.

This is stronger evidence than plugin-detection or parser success: the bridge itself executed and produced a reloadable scene in the observed environment.

## What this establishes

Within the observed environment, a provider-neutral canonical map can be materialized into a mixed authoring workspace containing real Terrain3D, Cyclops and ProtonScatter provider objects without making those provider formats canonical.

It also establishes a useful fallback rule: provider absence does not make the semantic map unreadable or uneditable.

## What this does NOT establish

This observation does **not** establish:

- two-way provider-to-contract synchronization;
- automatic conversion of structure guides into final Cyclops brush solids;
- configured ProtonScatter items/modifier stacks or production vegetation output;
- successful Terrain3D sculpt/paint operations or terrain-region persistence under real authoring sessions;
- navigation baking interoperability across provider geometry;
- Android performance or memory budgets;
- multiplayer balance or gameplay quality;
- future Godot/provider version compatibility.

Those require separate experiments. In particular, this observation should not be cited as proof that Terrain3D or ProtonScatter are production-ready on target Android hardware.

## Next experiments

1. Terrain3D region bootstrap + controlled sculpt/paint round-trip.
2. Structure-guide conversion into editable Cyclops blocks and back to semantic structure metadata.
3. ProtonScatter item/modifier preset generation from provider-neutral biome definitions.
4. Navigation bake over generated terrain/structures and route-connectivity comparison against the canonical topology.
5. Mobile rendering/memory benchmark for terrain and scatter density tiers.
