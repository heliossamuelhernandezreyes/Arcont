# TPS Runtime Diagnostic — 2026-08-29

Status: IMPLEMENTATION IN VERIFICATION

## Problem
The structural TPS contract was green while Android evidence did not show the player operator in the expected over-the-shoulder framing.

## Evidence hierarchy used
- Direct Arcont CI runtime instrumentation.
- Official Godot Camera3D and SpringArm3D documentation.
- Existing Arcont animation/camera research and Android visual evidence.

## Reproduction
Godot CI run 33260790746, commit `f95b68c08460a9c0ccfd68c4136194d18264b022`, added a semantic screen-space diagnostic instead of relying only on node existence.

Observed live runtime values:
- viewport: 1280x720;
- Camera3D global position: approximately `(0.132, 2.510, 52.0)`;
- player global position: approximately `(0.0, 0.930, 52.0)`;
- requested SpringArm length: 4.65 m;
- actual camera-to-rig-target distance: only 0.132 m;
- OperatorModel root visible: true;
- operator geometry descendants: 3;
- visible-in-tree geometry: 0;
- mesh centers in front of camera: 2;
- mesh centers projected inside viewport: 0.

This directly explains the apparent first-person/no-body output: `ThirdPersonADS._update_near_camera_visibility()` deliberately hides the operator shell when the actual distance drops below 0.72 m. The shell was therefore reacting correctly to a camera placement failure.

## Root architectural issue
The previous hierarchy stored the shoulder offset on `Camera3D.position.x` while Camera3D was the direct child whose placement is controlled by SpringArm3D. Official Godot documentation describes SpringArm3D as moving its direct children to the solved collision/end position. Two systems were therefore trying to own the direct camera transform.

## Corrective architecture
Production now uses:

`Player -> CameraRig (orbit/height) -> SpringArm3D (shoulder origin + collision distance) -> Camera3D (local origin)`

The shoulder offset belongs to `SpringArm3D.position.x`; `Camera3D.position` remains zero. This leaves SpringArm as the sole owner of collision-distance placement while preserving the authored shoulder origin.

Production commits:
- `cb67bf18779acaabd64035e885e12a5be8680f23` — move TPS shoulder offset onto SpringArm.
- `2973b6f67a6e78f0c6507703885b9dda17137d7f` — scene hierarchy/initial transforms synchronized.
- `fc17246b137861cab6d235a4bd6a0bb3cd2f62cf` — structural rig test synchronized with the replacement contract.

## Acceptance contract
Do not mark this fixed from code alone. Required evidence:
1. screen-space diagnostic passes in an open mission view;
2. rendered hip-TPS screenshot visibly contains the operator with intentional shoulder framing;
3. rendered ADS screenshot visibly differs and remains readable;
4. moving/locomotion capture shows a posed rather than bind/T-pose operator;
5. Android device verification confirms open-space and collision-compressed camera behavior.

## Durable lesson
For camera and animation systems, test the semantic rendered outcome as well as the structural graph. A requested SpringArm length is not evidence that the Camera3D actually sits at that distance, and a visible root is not evidence that descendant geometry is rendered in frame.
