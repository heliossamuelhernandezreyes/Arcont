# Production evidence: FISURA Vanguard native humanoid animations

**ID:** ARC-GODOT-OBS-VANGUARD-0001  
**Engine:** Godot 4.7.2-stable (Linux GitHub Actions)  
**Observation date:** 2026-10-08 UTC  
**Game:** [FISURA](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-)  
**CI evidence:** [runtime run 37730621172](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-/actions/runs/37730621172)

## Experiment design

Replace a hand-animated mesh-part humanoid in the independent game with a complete imported humanoid *without* changing player physics, combat or controls. Select Quaternius Ultimate Modular Men `Spacesuit.gltf` from a third-party source mirror pinned to `agentkaerf/FreeModels@db3df04d1e4714298a09510b26fb6de6645138a2`, verify its CC0 license, hash the vendored game file, and test native animation states on exact Godot version.

This is **native animation playback**, not general-purpose human rig retargeting. The separate Quaternius Universal Animation Library was not adapted for this experiment.

## Measured evidence (automated)

- The source JSON contains 24 distinct animations and a rig. `tests/vanguard_import.gd` confirms Godot imports **one Skeleton3D with 62 bones**, **four MeshInstance3D with 10,558 triangles**, and **24 animations**. It starts the Run clip and verifies AnimationPlayer is running.
- `tests/vanguard_gameplay.gd` instantiates the actual FISURA scene and verifies **Idle_Gun → Run → Run_Shoot → Roll → HitRecieve → Death**, with the original physics/cooldown maintained. The camera target is approximately **7.38 world units from the player** in the test spawn.
- The real rendering workflow also produced a Godot framebuffer screenshot. Import and animation-state evidence **cannot** establish whether gameplay motion is comfortable or visually polished; manual judgment and playtesting remain necessary.
- The source asset, its CC0 license and SHA-256 provenance live in the FISURA game. ARCONT stores **only this observation and normalized metadata**, respecting the no-production-game-code invariant.

## Gaps and reusable implications for ARCONT

1. Prefer **rig-authored native clips** as the first integration path when a suitable character exists. Test separate retargeting only after rig-map, rest-pose and bone naming compatibility are known.
2. Build an automated `animation audit`: imported Skeleton3D bone count; skin, mesh, all named AnimationPlayer clips; actual triggering from gameplay states; visual screenshot; platform-specific performance gate.
3. Treat a valid AnimationPlayer as necessary but not sufficient: IK, foot contact, aim offsets, turn-in-place, upper/lower body layers, reload, transition durations and root-motion calibration remain unmeasured.
4. Do not confuse a Linux software-render proof with Android performance. No APK, frame-pacing distribution, thermal measurement or input latency was measured.
5. Maintain `game-owned physics body → separately instanced visual rig` to preserve movement, collisions and AI when models are exchanged.
6. Source-pinned CC0 asset provenance is distinct from an assertion of AAA quality. The low/mid-poly styling may not fit the eventual art direction.

**Status:** executable integration validated in Linux CI; physical/mobile product quality remains unverified. ARCONT contains no playable game or model binaries.
