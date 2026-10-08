# Quaternius animated robots — evidence-based source intake

**Record:** ARC-GODOT-OBS-QUATERNIUS-0001  
**Engine:** Godot 4.7.2-stable  
**Date:** 2026-10-08  
**Origin:** [Quaternius Sci-Fi Essentials Kit](https://quaternius.com/packs/scifiessentialskit.html), Standard edition, CC0-1.0.

## Scope and licensing

The original creator's pack page declares CC0 1.0. A third-party redistribution under `agentkaerf/FreeModels` was pinned to commit `db3df04d1e4714298a09510b26fb6de6645138a2`. The mirrored pack contains `License_Standard.txt` confirming CC0. ARCONT itself holds **normalized records only**; binary mesh, skeleton, texture and animation resources were placed in the separate FISURA production repository.

This distinction matters: a source-index reference, a valid copyright license, a successful binary acquisition, an animation import, and functional gameplay are different levels of evidence.

## Executable results

FISURA Godot 4.7.2 CI successfully imported:

| Model | Triangles reported by Godot | Skeletons | Animation clips |
|---|---:|---:|---:|
| Enemy_QuadShell | 7,494 | 1 | 8: Attack, Charge, Hit, Idle, Look, Run, TurnOff, Walk |
| Enemy_EyeDrone | 3,530 | 1 | 6: Attack, BackFlip, Charging, Hit, Idle, Look |
| Gun_Rifle | 6,194 | 0 | 0 |

**Evidence:** [FISURA CI run 37728531689](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-/actions/runs/37728531689), script `tests/quaternius_import.gd`. The run verifies loading and skeleton/AnimationPlayer assets. The later production integration also uses `tests/animated_combat.gd` to verify skeletal Idle→Hit transitions while retaining independent collision logic.

## Reusable engineering guidance

- When source glTF files refer to sibling PNG/BIN assets, vendor the full dependency closure and verify every file's SHA-256. Importing only the .gltf is insufficient.
- Check a true Godot `Skeleton3D` and `AnimationPlayer` rather than assuming a model's name or its source label proves animation works.
- Preserve character physics/AI separately from mesh/skin animation. This permits changing visual rigs without perturbing collision and obstacle avoidance.
- Retargeting the Quaternius universal humanoid animation library onto arbitrary enemy robots is **not** automatic. The imported robot rigs use their own animation clips. The humanoid animation library remains a separate prospective investigation.
- Stable CI + skinned scene import does not establish visual AAA quality, gamepad/touch feel, motion plausibility or 60/120 FPS on mobile.
- Do not mirror external assets into ARCONT without a purpose and documented provenance; game-specific assets remain in the game repository.

## Future ARCONT capability gap

A reusable `asset intake` routine could accept a publisher URL and selected source file identities, verify license evidence and hashes, fetch dependency closure, run a Godot skeleton/animation import audit, and produce a normalized catalog record plus tested compatibility level. It must **not** automatically claim support for Android or production-ready animation.

**No FISURA runtime scripts or binary models have been placed in ARCONT.**
