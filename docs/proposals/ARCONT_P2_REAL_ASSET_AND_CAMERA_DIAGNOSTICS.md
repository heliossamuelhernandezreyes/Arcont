# ARCONT P2: dependency-complete models and camera-space visibility diagnostics

Status: experimental working PR stacked on ARCONT visual P0/P1 (#49). This is not a released ARCONT 1.2 or an autonomous art director.

## Model Forge: source-verified offline bundle intake

The new tools/model_forge_pack_select.py consumes an already-acquired ZIP and a verified Asset Vault CC0 record. The original archive SHA-256 is mandatory; no network requests are made. Select glTF/GLB members, then the tool parses their real external image and buffer URIs and stages only their full dependency closures, preserving paths.

It rejects missing PNG textures, missing buffers, wrong hashes, missing creator license, symlinks, ZIP path traversal, unsupported models, enormous archives, duplicate destinations and incomplete staged geometry. It reuses canonical ARCONT license policy, production_assets.closure and model_forge_inspect, saves per-file SHA and the original license, and publishes atomically into a new game-owned directory.

**Kenney Factory Kit 3.0 reproduction (source SHA from FISURA 0.9.8):**

~~~bash
python tools/model_forge_pack_select.py \
  --archive /work/kenney_factory-kit_3.0.zip \
  --record assets/catalog/kenney/factory-kit.asset.json \
  --expected-sha256 7e31fb2308e90304672bd15cd18fa9d9f02c03731a8cbc57a8e3e1c181dfb0a7 \
  --prefix "Models/GLB format" \
  --model machine-fortified.glb \
  --model machine-window.glb \
  --model pipe-large-valve.glb \
  --model pipe-large-long.glb \
  --model robot-arm-a.glb \
  --model conveyor-long.glb \
  --model catwalk-straight.glb \
  --out /work/kenney_selected
~~~

**Expected:** stage the GLBs plus their originally referenced Textures/colormap.png; omit unused source models. Keep the official creator license and SHA provenance. The staged results are a candidate for Godot; Android FPS and artistic quality **remain unmeasured**.

## Visual Director: read-only camera-space view obstruction analysis

The new tools/visual_camera_diagnostics.py projects axis-aligned 3D bounds from a supplied camera into the 2D viewport. It identifies:
- scene pieces whose projected AABB consumes 12% or more of the screen;
- possible reticle-intersecting architecture;
- possible overlaps of foreground bounding boxes with enemy/objective projections.

These are **conservative AABB candidate signals**. They do not measure pixel-level occlusion, mesh silhouettes, objective visibility by rays, draw calls, quality, or FPS. Metadata claiming native Godot remains externally self-reported unless independently verified in game CI.

~~~bash
python tools/visual_camera_diagnostics.py templates/visual-production/camera-obstruction.example.json
~~~

Agents can use the read-only Bridge operation visual.camera.analyze with exactly one project-relative argument shot_path. It does not permit writes or arbitrary shell commands.

~~~json
{"protocol":"arcont-bridge","version":1,"request_id":"node-a-camera-check","operation":"visual.camera.analyze","arguments":{"shot_path":"evidence/actual-camera-shot.json"}}
~~~

Camera shot protocol: arcont-camera-shot v1. Fields: camera.position, camera.target, camera.up, camera.fov_y_degrees, camera.viewport; objects (id, center, size, role); optional reticle_region (normalized screen fractions). Camera Y FOV must be vertical, viewport dimensions in pixels, geometry in the same world coordinate system.

A native Godot adapter must export real camera transforms and world-space object AABBs under test. The included example is **synthetic**, not native FISURA data.

## CI and acceptance

- Synthetic Kenney-style GLB references a shared palette PNG; imported models pass existing ARCONT inspectors, and archive malicious/partial cases are refused.
- Synthetic third-person shot detects a foreground pillar, reticle interference and enemy-box overlap. Negative cases check duplicates, non-finite values, reversed camera direction and up-axis problems.
- Knowledge Integrity runs all unit tests. This proves deterministic tooling, **not Android runtime or final visual superiority**.
- Full production promotion still requires the actual Godot scene, screenshot/provenance and hardware device tests.
