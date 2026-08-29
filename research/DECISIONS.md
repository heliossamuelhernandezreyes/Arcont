# Technical Decision Ledger

A lightweight ADR index for knowledge that already influenced Arcont.

## Implemented / established

### TPS camera collision ownership
Status: IMPLEMENTED
Decision: SpringArm3D owns physical third-person camera collision. ThirdPersonADS owns the pivot height, shoulder origin and desired `spring_length`, but it must not continuously overwrite the direct Camera3D child's local transform. SpringArm3D dynamically moves its direct children along local +Z to the solved arm endpoint (or nearer collision point), so a runtime Camera3D local Z near the arm length is expected in open space and must not be treated as a contract failure.
Reason: avoids FPS/TPS coupling and conflicting camera controllers; preserves Godot's native SpringArm collision solution and lets the camera remain a direct child so the camera near-plane shape can be used when no explicit arm shape is supplied.
Evidence: Godot 4.x SpringArm3D class/tutorial documents that the arm moves direct child nodes to the end of its length or the collision point. Runtime CI evidence on 2026-08-29 showed that forcing `camera.position = Vector3.ZERO` each physics tick collapses the effective TPS distance to the shoulder offset (~0.82 m), while allowing SpringArm3D to place the camera yields local Z ~4.65 m in open space.
Test contract: verify desired arm length/shoulder origin plus rendered camera-to-pivot distance and on-screen operator visibility. Do not require Camera3D local position to remain zero after physics processing.
Re-audit: camera architecture rewrite, Godot engine major change, or replacement of SpringArm3D.

### Touch ownership
Status: IMPLEMENTED
Decision: track touch fingers independently; disable emulated mouse/touch crossover for gameplay.
Reason: movement, look and combat must coexist reliably.
Re-audit: input architecture or platform change.

### World-space weapon mounting
Status: IMPLEMENTED
Decision: equipment follows the character rig/weapon mount rather than living under the physical camera.
Reason: supports visible body, melee, cover, shoulder camera and animation.
Re-audit: final production rig / IK pipeline.

### Animation architecture
Status: IMPLEMENTED / EVOLVING
Decision: use AnimationTree/state-machine/layered animation as locomotion complexity grows instead of manually swapping isolated clips.
Re-audit: production animation set, root-motion policy, motion-matching research.

### Mobile-first scalability
Status: IMPLEMENTED / EVOLVING
Decision: gameplay systems must expose scalable visual/performance budgets rather than relying on a single desktop-quality configuration.
Re-audit: target-device matrix changes.

### Anatomical damage is functional
Status: IMPLEMENTED / PROVISIONAL
Decision: hit regions and limb state affect combat capability/locomotion, not only gore visuals.
Reason: creates tactical value and systemic identity.
Re-audit: final character/gore pipeline.

## Candidate decisions

### Data-driven gameplay definitions
Status: CANDIDATE
Proposal: move weapon, enemy, material, damage and encounter definitions toward typed custom Resources as content count grows.
Reason: reduce hard-coded tables and separate tuning/content from controller logic.

### Root motion only for committed actions
Status: CANDIDATE
Proposal: prefer code-driven locomotion for ordinary movement while evaluating root motion for vaults, mantles, executions and selected melee actions.
Reason: retain responsive player control while allowing authored contact-heavy actions.

### Budgeted AI updates
Status: CANDIDATE
Proposal: schedule perception/path/tactical updates across frames and distance/importance tiers.
Reason: crowds and mobile CPU constraints make uniform per-frame AI wasteful.

## Rejected/superseded knowledge
Keep rejected approaches here rather than deleting their history. The old camera-attached FPS weapon/camera coupling is SUPERSEDED by the current TPS ownership model.
