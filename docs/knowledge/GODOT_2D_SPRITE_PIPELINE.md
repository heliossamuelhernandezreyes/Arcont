# Godot 2D sprite production pipeline

Status: **first operational tooling / Mortofe validation in progress**

Trigger consumer: `heliossamuelhernandezreyes/Godot-juegos-2d/Mortofe`

This document complements `GRAPHICS_ASSET_FOUNDATIONS.md`. It does not replace general texture/performance guidance; it defines the operational contract for character/environment sprite delivery.

## Goals

- Accept hand-drawn, generated or externally authored 2D art.
- Preserve visual consistency across animation frames.
- Make pivots and gameplay alignment deterministic.
- Produce atlas/import settings suitable for Godot and mobile.
- Keep source/master art separate from runtime-optimized derivatives.

## Master-canvas contract

Every animation set must declare:

- source canvas width/height,
- character reference height in pixels,
- pixels-per-game-unit or equivalent world-scale convention,
- baseline/foot contact coordinate,
- facing convention,
- intended pivot,
- whether frames may be trimmed,
- color-space/alpha expectations.

Character frames in one animation family should not silently change canvas dimensions or world scale.

## Pivot contract

The gameplay pivot is not the visible image center by default. For grounded characters, the preferred anchor is a stable foot/baseline reference unless the animation explicitly requires another semantic anchor.

All frames must resolve to the same world-space anchor after trimming. A visual frame may move inside its canvas; the gameplay body should not jitter because transparent margins changed.

## Frame-consistency checks

The first operational validator/packer is `tools/sprite_pipeline.py`. It currently checks dimensions, alpha bounds, transparent padding, fully transparent frames and byte-identical duplicates, then emits deterministic page/slot metadata. The generic contract still requires further checks for:

- baseline drift,
- pivot drift,
- sudden silhouette/scale discontinuity,
- semantic costume/weapon/camera drift,
- filename/order gaps,
- atlas overflow against the target device profile.

Generated frames require stronger consistency checks because independent generation can mutate costume, proportions, weapon geometry or camera angle.

## Source vs runtime assets

Keep:

1. master/source frame or layered artwork,
2. normalized frames,
3. atlas/runtime derivative,
4. Godot import metadata/profile.

Do not overwrite the master simply to satisfy runtime packing.

## Atlas contract

Atlas assembly must preserve:

- deterministic frame order,
- per-frame source rectangle,
- pivot/baseline metadata,
- animation names and timing,
- padding/extrusion sufficient to prevent sampling bleed,
- optional separation by material/shader needs.

One giant atlas is not automatically optimal. Atlas policy must consider texture size limits, memory residency, draw batching and content streaming.

`tools/sprite_pipeline.py pack` creates deterministic PNG atlas pages and `atlas_manifest.json`. Page count, grid and cell size are explicit inputs rather than hidden heuristics.

## Tool contract

Example audit:

```bash
python tools/sprite_pipeline.py audit path/to/player.sprite.json --output /tmp/player-audit.json
```

Example deterministic atlas build:

```bash
python tools/sprite_pipeline.py pack path/to/player.sprite.json \
  --output-dir /tmp/player-atlas \
  --cell 256x256 \
  --grid 4x4 \
  --colors 256
```

Pillow is an image-operation dependency of this tool and is intentionally loaded lazily so ARCONT's dependency-light integrity suite can still test the pure ordering/layout contract without Pillow.

## Godot import profile

Mortofe is not pixel art by default, so its first import profile should favor smooth high-resolution illustration rather than nearest-neighbor assumptions.

The mobile pipeline must explicitly choose:

- filtering,
- mipmap policy,
- compression/import format,
- max texture size,
- lossless/lossy policy where supported,
- ETC2/ASTC import compatibility for Android,
- atlas/page size.

Any profile change should be benchmarked on target Android hardware rather than justified only by desktop appearance.

## Animation integration

Runtime animation may use `Sprite2D` + `AnimationPlayer`, `AnimatedSprite2D`, or another Godot-native representation. ARCONT should choose based on needs rather than forcing one type.

The import adapter must be able to produce:

- idle,
- run,
- jump/fall,
- dash,
- attack phases,
- hurt/death,
- later parry/ability animations,

while preserving the same gameplay pivot/body relationship.

## Mortofe visual direction constraints

Mortofe's product direction is dark medieval/baroque illustration. The reusable pipeline must not bake this art direction into generic tools. It only informs the first consumer workload: detailed silhouettes, cloth/metal ornament, dramatic lighting compatibility and non-pixel-art scaling.

## Current Mortofe gate

The first recovered production candidate has coherent separated frames for idle, run, jump, attack and dash. Hurt and death are intentionally not promoted yet because the available older generated sheets drift in armor/weapon identity. That is a correct pipeline failure, not missing bookkeeping: identity consistency has priority over filling every state with incompatible art.

The next promotion gate is to import the candidate into Mortofe, validate gameplay-scale readability and animation stability on Android, then author coherent hurt/death frames from the approved master identity.

## Promotion backlog

`sprite_pipeline` remains PARTIAL until ARCONT has validated the complete path for:

- manifest format;
- frame audit;
- semantic normalization;
- deterministic atlas build;
- Godot import adapter;
- mobile memory/package benchmark;
- at least one real Mortofe animated character imported through the pipeline.

The tool implementation alone does not promote the capability to a validated rule.
