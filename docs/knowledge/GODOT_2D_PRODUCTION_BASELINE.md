# ARCONT — Godot 2D Production Baseline

Status: initial audit, 2026-10-04 local / 2026-10-05 UTC
Consumer that triggered the audit: `heliossamuelhernandezreyes/Godot-juegos-2d`, project `Mortofe/`
Canonical engine: Godot 4.7.2-stable, commit `ed1daf0bf001b61586d9930840f2f1394092c079`

## Purpose

This document records what ARCONT can already support for a production 2D game and what is still missing. It does **not** embed production game code in ARCONT. Mortofe remains an external consumer and acts as a pressure test.

The rule is: audit existing capability first; reuse it if sufficient; otherwise add the smallest reusable knowledge, contract, benchmark or tool needed, then validate it in the external game.

## Capability audit

| Domain | Status | Current ARCONT support | Gap exposed by Mortofe |
|---|---|---|---|
| Godot source trace | READY | Exact 4.7.2 source pin, source-trace protocol, engine atlas | None for baseline work |
| Evidence / reproducibility | READY | Evidence ledger, maturity model, benchmark/result schemas, runtime bridge | Need 2D-specific benchmark campaigns |
| Observability | READY/PARTIAL | Unified evidence ingest; runtime-lab, Perfetto and Tracy providers | Need standard 2D gameplay probes and scene metrics |
| Mobile performance | READY/PARTIAL | Android/frame pacing/performance foundations | Need 2D reference workloads and touch-latency tests |
| Asset provenance | READY | Asset Vault, licensing rules, source registry | Need sprite/atlas import profiles and art-consistency QA |
| 2D rendering knowledge | PARTIAL | Game Dev Atlas scopes sprites, tile/grid worlds, lighting, parallax and cameras | No Godot 4.7.2 production recipe/benchmark set yet |
| CharacterBody2D locomotion | MISSING operational baseline | General physics/gameplay knowledge exists | Need reusable controller requirements + tests: acceleration, coyote, buffer, slopes, one-way, moving platforms |
| 2D combat | PARTIAL | General combat-system patterns | Need hitbox/hurtbox contract, invulnerability, knockback and deterministic test scenes |
| Sprite animation pipeline | MISSING operational baseline | General animation knowledge | Need sprite-sheet/atlas naming, pivot, trimming, frame consistency and import validation |
| TileMapLayer authoring | MISSING operational baseline | Map authoring architecture is mainly dimension-agnostic / 3D-provider oriented | Need 2D semantic map contract and Godot adapter guidance |
| 2D navigation / AI | PARTIAL | General AI/navigation knowledge | Need Godot 2D navigation trace, avoidance/crowd costs and representative tests |
| 2D lighting / shadows | MISSING operational baseline | General graphics foundations | Need CanvasItem/Light2D/occluder/shader cost matrix on PC + Android |
| Camera | PARTIAL | General camera domain is indexed | Need 2D camera smoothing, look-ahead, bounds, shake and pixel/subpixel policy |
| Touch controls | PARTIAL | Mobile foundations | Need reusable 2D touch-control contract and latency/ergonomics validation |
| Save/data | PARTIAL | Domain indexed | Need concrete versioned save contract for production consumers |
| CI for external Godot games | PARTIAL | ARCONT validates itself, not production repos | Need audited headless import/check/export recipe for consumer repos |

## First production experiment: Mortofe

Mortofe begins with a deliberately asset-light vertical slice so systems can be tested before final art masks mechanical defects.

Initial systems under pressure:

- `CharacterBody2D` movement;
- coyote time and jump buffering;
- variable-height jump;
- dash;
- melee hitbox;
- enemy damage loop;
- camera smoothing and limits;
- collision-world construction;
- PC input baseline;
- later Android/touch validation.

Every defect discovered in Mortofe must be classified as one of:

1. `game-specific` — stays only in Mortofe;
2. `reusable-pattern` — document/contract in ARCONT;
3. `engine-behavior` — source trace against the pinned Godot commit;
4. `benchmark-needed` — add a reproducible external runtime experiment;
5. `tooling-gap` — add or audit a reusable tool before adoption.

## Source escalation policy

Do not fork Godot by default. Escalate only when the prior layer is insufficient:

1. public Godot API / scene composition;
2. GDScript or C# implementation;
3. editor plugin/tool script;
4. GDExtension;
5. engine module;
6. maintained fork.

If behavior depends on internals, trace the exact implementation at the pinned upstream commit and record the path and assumptions. A fork is justified only when the capability cannot be cleanly expressed or measured at a higher layer and its maintenance cost is acceptable.

## Immediate ARCONT backlog from Mortofe

- Define a machine-readable 2D capability matrix.
- Add a reference test plan for 2D locomotion and combat.
- Audit Godot 4.7.2 sprite/atlas import and TileMapLayer workflows.
- Define Android touch-control and frame-time probes for 2D.
- Audit a headless Godot CI path before adding it to production repos.
- Build a sprite consistency pipeline: canvas size, pivot, trim, palette/style metadata, atlas assembly and import checks.

## Success criterion

ARCONT is not considered "2D ready" merely because it contains 2D documentation. A capability becomes operationally ready only after an external consumer such as Mortofe uses it successfully and leaves reproducible evidence or a validated contract behind.
