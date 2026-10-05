# Godot 2D sprite production pipeline

Status: **contract defined / tooling not yet validated**

Trigger consumer: `heliossamuelhernandezreyes/Godot-juegos-2d/Mortofe`

This document complements `GRAPHICS_ASSET_FOUNDATIONS.md`. It does not replace general texture/performance guidance; it defines the missing operational contract for character/environment sprite delivery.

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

A future ARCONT validator should report at least:

- dimension mismatch,
- unexpected alpha-bound jumps,
- baseline drift,
- pivot drift,
- sudden silhouette/scale discontinuity,
- duplicate frames,
- filename/order gaps,
- excessive transparent padding,
- atlas overflow.

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

## Promotion backlog

`sprite_pipeline` remains PARTIAL/MISSING until ARCONT has validated tooling for:

- manifest format,
- frame audit,
- normalization,
- deterministic atlas build,
- Godot import adapter,
- mobile memory/package benchmark,
- at least one real Mortofe animated character imported through the pipeline.
