# Map-authoring providers — Godot 4.7.2 observation

Observation ID: `ARC-GODOT-OBS-MAP-AUTHORING-0001`

Date: 2026-09-12

Maturity: **L3 observed** for the narrow compatibility claim below. This does not promote performance, Android compatibility, production stability, navigation interoperability, or authoring quality.

## Subject

Close Seal installed the pinned map-authoring provider set defined by its `third_party/map_authoring.lock.json` and opened the project with the exact Godot Engine `4.7.2-stable` build (`ed1daf0bf001b61586d9930840f2f1394092c079`) on GitHub Actions Ubuntu.

Pinned providers tested:

- Terrain3D release `v1.0.2-stable`, archive SHA-256 `a071850250ec5e596aa54da61c01d75768774eb379ee997584d426a45f4884a2`.
- Cyclops Level Builder commit `fca8640e3d5e38b1649d503ac62b6dabcbf7b64f`.
- ProtonScatter commit `2ced25f1ebef13648e94d3cc6a643da92a7e33d8`.
- FuncGodot commit `cdf27e3cd8369b405a0ac48649e141238f5cfad5`.

## Evidence

Close Seal workflow: `Map Authoring Providers`

- workflow run: `34720004774`
- Close Seal head: `c8bf73093e9e6fbc41c09b7a873bd4542513750e`
- environment: GitHub-hosted Ubuntu runner
- exact editor: Godot 4.7.2 stable Linux x86_64

Observed sequence:

1. Exact pinned provider installer completed for all four providers.
2. Installer post-check reported all four provider markers as `READY`.
3. A first editor pass imported assets/resources.
4. A second clean editor import completed successfully without the workflow's failure signatures for GDScript parse errors, addon load errors, failed scripts, or GDExtension load failures.

The earlier validation run `34719928306` failed. Investigation showed the blocking parse error came from Close Seal's own HUD using `preload()` on not-yet-imported SVG resources in a fresh checkout, not from provider installation. Close Seal changed those textures to deferred `load()` and changed validation to a first import pass followed by a clean second pass. The corrected run then succeeded.

## Supported claim

On the observed GitHub Linux environment, this exact pinned provider set can be installed into the Close Seal project and survives a clean second editor import using the exact Godot 4.7.2-stable editor.

## Unsupported claims

This observation does **not** establish:

- Android editor/runtime support;
- Android export correctness;
- Terrain3D production performance;
- ProtonScatter density budgets;
- Cyclops production geometry cost;
- FuncGodot imported-map semantic correctness;
- navigation bake interoperability;
- simultaneous interactive editor use over long sessions;
- compatibility on Windows/macOS;
- future-version compatibility.

Those remain separate experiments.
