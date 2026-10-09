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

An opt-in native Godot adapter exports real camera transforms and world-space MeshInstance3D AABBs under test. The standalone example remains **synthetic**.

## Real FISURA 0.9.8 acceptance

The additional `.github/workflows/fisura-real-camera-acceptance.yml` checks out the **exact game source commit** `dad2f97a0dee570b097448143fff263fe203ea80` from the separate FISURA repository, imports its real Reactivo-13 third-person scene in Godot 4.7.2, freezes gameplay without changing collision or light nodes, and runs the shared ARCONT camera exporter over the original cinematic mesh subtree. It then passes that actual native shot to the standalone Visual Director Python analyzer.

The first successful real-shot acceptance read **399 cinematic meshes**, with **247 projected into the viewing region**. Some geometry intersects the camera near clipping plane; the old conservative rectangle approach incorrectly marked several such pieces as occupying 100% of the screen. That has now been made a distinct `needs_geometry_review` category, with `near_plane_uncertain` warnings and **no asserted full-screen obstruction**. Original authored `semantic_art_tag` labels and stable SHA-bound IDs for deeply nested GLB nodes help match warnings to actual meshes.

The CI output includes source commit, .tscn SHA-256, camera-shot SHA-256, read-only invariants and a bounded alert preview. The evidence is real Godot geometry/camera data, **not a color screenshot, GPU depth image, measured pixel occlusion, physical Android benchmark or autonomous level fix**. AABB screen/depth-overlap claims remain provisional. Reports need the original frame/image and gameplay-aware human review before modifying camera-sensitive level geometry.

The scene is a **fixed external integration fixture**, not bundled into ARCONT and not edited in its source repository. To update acceptance to a newer FISURA revision, intentionally change and verify the pinned source SHA in the CI config.

## Agent Bridge: explicit permission to stage a project-local archive

A second operation, model.archive.stage, connects Model Forge to the normal ARCONT Bridge. It accepts only an archive already inside the external game, a catalog_path inside ARCONT assets/catalog, a caller-supplied exact source SHA-256, a prefix, selected members and a new game-relative destination.

Invoking the operation **without --allow-project-write** fails before creating any folder. The existing project boundary, license gate, ZIP safety checks, source closure and no-overwrite guard all still apply. This is not an unbounded internet downloader or permission to modify existing gameplay.

Example (the ZIP has already been obtained and its source SHA independently reviewed):

~~~json
{"protocol":"arcont-bridge","version":1,"request_id":"stage-kenney","operation":"model.archive.stage","arguments":{"archive_path":"sources/kenney_factory-kit_3.0.zip","catalog_path":"assets/catalog/kenney/factory-kit.asset.json","expected_sha256":"7e31fb2308e90304672bd15cd18fa9d9f02c03731a8cbc57a8e3e1c181dfb0a7","prefix":"Models/GLB format","models":["machine-window.glb"],"destination":"assets/vendor/arcont_kenney_candidate"}}
~~~

Security and claim limitation: a SHA-256 supplied by an agent **only verifies consistency with its declared bytes**, not independent upstream authenticity. Official source/download verification remains the external producer's duty. A bundle is only source-closure-and-geometry validated, NOT game-approved or Android-certified.

## CI and acceptance

- Synthetic Kenney-style GLB references a shared palette PNG; imported models pass existing ARCONT inspectors, and archive malicious/partial cases are refused.
- Synthetic third-person shot detects a foreground pillar, reticle interference and enemy-box overlap. Negative cases check duplicates, non-finite values, reversed camera direction and up-axis problems.
- Knowledge Integrity runs all unit tests. This proves deterministic tooling, **not Android runtime or final visual superiority**.
- Full production promotion still requires the actual Godot scene, screenshot/provenance and hardware device tests.
