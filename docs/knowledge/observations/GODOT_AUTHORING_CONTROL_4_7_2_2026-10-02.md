# General authoring control — observed Godot 4.7.2 integration

Observed 2026-10-02. This is an integration observation, not a runtime benchmark
or promotion of engine/provider maturity.

## Provenance

- ARCONT source: `63a6a35db7bc28131b3ae3acd8b94a17969f58aa`.
- Closeseal source: `4d5bbeb57665e9447ce208d21328409e398f0bbd`.
- Godot: official 4.7.2-stable, `ed1daf0bf001b61586d9930840f2f1394092c079`.
- ProtonScatter: `3a9c5c1640d0270097370fc3a300bb96348bcfb6` (MIT).
- [Successful acceptance run](https://github.com/heliossamuelhernandezreyes/Closeseal/actions/runs/36952147375), job `110667206175`.
- Artifact `11203888321`, ZIP SHA-256 `dc3610e5421737d201829a4de68c5b29e98bff93109442bca9d08d01217e1673`.
- [Game-owned captures, WAV, report and artifact hashes](https://github.com/heliossamuelhernandezreyes/Closeseal/tree/authoring/godot-api-v1/docs/map_forge/evidence/general_authoring).
- ARCONT's Knowledge Integrity and Closeseal's Project Integrity also passed.

## Observed behavior

The public revisioned CLI queried actual native AudioStreamPlayer3D and installed
ProtonScatter script signatures; created an explicit scene/resource recipe;
built a preview without publishing; committed; rejected a stale revision and
invalid native method; patched a material; and rebuilt a restored source revision.
The previous successful bundle remained byte-identical after the patch.

The provider's real modifier stack generated 24 transforms and 24 rendered
MultiMesh instances. A repeated build with the same seed matched the original
transforms. Save/reopen retained all 24 instances, the material roughness and
44,100 bytes of mono PCM audio. AudioStreamPlayer3D entered playing state using
the runner's Dummy driver; the authored WAV contains one second at 22,050 Hz.

Native navigation baked 44 polygons and returned a four-point path across the
workbench. An actual 1.8m capsule stood on collision geometry and walked
approximately 4.0000005m. A ray after reopening used a separate collision layer
and verified that the collider belonged to the reopened scene.

Actual MCP stdio initialize/tools-list/tools-call/inspect completed through the
same writer. This verifies a local protocol transport, not a configured ChatGPT
remote connector or live graphical editor session.

The same bridge composed the existing Urban Nexo canonical source: 812 native
objects, 301 authored asset placements and two custom meshes. It changed the sun
and environment in a derived lighting scene, saved it, captured plaza/street views
and hit plaza collision. The canonical map bytes remained unchanged. All four
new 1280×720 views (workbench plus city) were visually inspected.

## Failure and correction

Initial discovery unnecessarily started the full editor UI before quitting;
it now uses runtime context by default. The first scene build then exposed
ProtonScatter's untyped local property-list arrays on Godot 4.7.2. Advancing
the pin by exactly one upstream commit corrected those two arrays; the strict
engine-error check was retained. The CI runner's missing sound device is handled
by explicitly choosing Dummy for this test, rather than assuming speaker output.

## Limits

- Engine API availability does not prove every workflow. Full Cyclops editing,
  FuncGodot import, new road/VFX/animation/acoustics providers need separate tests.
- Editor-context APIs, live GUI automation and gamepad/mouse playtesting are not
  validated by this bridge milestone; the existing World 3D gate is separate.
- The workbench uses a placeholder asset and the city uses existing low-poly
  Kenney assets. These captures are not evidence of AAA art quality.
- Linux llvmpipe measurements are authoring diagnostics, not target-device FPS.
- Dummy playback proves stream setup/state and PCM output, not acoustic realism
  or audible output on a physical device.
- Bundle publication preserves the previous head/output; trusted scripts writing
  outside the bundle are not subject to filesystem-wide rollback.
