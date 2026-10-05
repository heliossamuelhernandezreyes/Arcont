# Godot 2D sprite production pipeline

Status: **frame audit v1 + deterministic normalization v1 implemented/tested; atlas and import adapter still pending**

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

## Automatic normalization

`tools/png_sprite_normalize.py` converts master/source frames into deterministic production PNGs before the frame audit runs.

The normalizer:

- accepts non-interlaced 8-bit RGBA PNG masters,
- measures the source alpha bounds using a configurable alpha threshold,
- preserves aspect ratio,
- aligns a stable horizontal source anchor to a target pivot,
- maps the visible foot baseline to the target baseline,
- scales to an explicit target visual height,
- uses premultiplied-alpha bilinear resampling to reduce dark edge halos,
- clamps pixels below the production baseline,
- refuses to silently crop or violate the requested padding,
- writes the batch only after every frame in the plan validates,
- emits source/output geometry plus content and PNG SHA-256 hashes.

By default `source_anchor_x` is `canvas_center`, which is safer for animation families authored on one stable master canvas because a weapon or cloak extending sideways does not move the body pivot. `alpha_center` exists for tightly cropped symmetric sources. A frame may instead declare an explicit `source_pivot`; its Y coordinate must coincide with the visible alpha bottom because the current production contract defines the foot baseline as the visible bottom.

The batch contract is `schemas/sprite-normalization-plan.schema.json`.

Mortofe's first production profile can use a 384x384 canvas, baseline/pivot Y 350 and stable pivot X 192 without hard-coding those values into the reusable tool:

```json
{
  "schema_version": 1,
  "defaults": {
    "target_canvas": [384, 384],
    "target_pivot": [192, 350],
    "target_visual_height": 300,
    "alpha_threshold": 8,
    "padding_px": 4,
    "source_anchor_x": "canvas_center"
  },
  "frames": [
    {
      "input": "res://art/master/player/idle_01.png",
      "output": "res://art/normalized/player/idle_01.png"
    },
    {
      "input": "res://art/master/player/attack_01.png",
      "output": "res://art/normalized/player/attack_01.png",
      "source_pivot": [512, 930]
    }
  ]
}
```

Run it with:

```bash
python tools/png_sprite_normalize.py path/to/normalization_plan.json \
  --project-root path/to/project \
  --report path/to/normalization_report.json
```

The tool intentionally does not auto-shrink an over-wide attack or silently move a pivot to make a frame fit. Those cases are production errors because per-frame auto-fit would change perceived character scale and introduce animation jitter. Fix the master, use the correct source pivot, or deliberately change the animation-family profile.

## Frame-consistency checks

`tools/png_sprite_audit.py` validates the normalized production frames. It deliberately requires normalized, non-interlaced, 8-bit RGBA PNG inputs so the runtime derivative has one deterministic format.

The validator currently reports or rejects:

- canvas dimension mismatch,
- alpha bounds and fully transparent frames,
- baseline drift,
- declared pivot drift,
- per-state visual-height drift,
- duplicate pixel payloads,
- simple numeric filename/order gaps,
- excessive transparent padding.

The manifest can define global or per-character quality gates such as `max_baseline_drift_px`, `max_pivot_drift_px`, `max_visual_height_drift_pct`, `transparent_padding_warning_pct` and `alpha_threshold`.

Example:

```json
{
  "quality_gates": {
    "max_baseline_drift_px": 2,
    "max_pivot_drift_px": 2,
    "max_visual_height_drift_pct": 4,
    "transparent_padding_warning_pct": 45,
    "alpha_threshold": 8
  },
  "characters": {
    "player": {
      "canvas": [384, 384],
      "baseline_y": 350,
      "pivot": [192, 350],
      "states": {
        "run": [
          {"path": "res://art/normalized/player/run_01.png", "pivot": [192, 350]},
          {"path": "res://art/normalized/player/run_02.png", "pivot": [192, 350]}
        ]
      }
    }
  }
}
```

Run it with:

```bash
python tools/png_sprite_audit.py path/to/production_sprite_manifest.json --project-root path/to/project
```

Normalization and frame audit are mechanical gates, not semantic art judges. They do **not** prove that independently generated frames preserve identity, costume, weapon geometry, camera angle or artistic quality. Those remain explicit visual-review gates. Atlas overflow is also deferred to the deterministic atlas builder.

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

The manifest, normalization and frame-audit portions have moved from contract-only to executable/tested baselines. `sprite_pipeline` remains PARTIAL until ARCONT has validated tooling for:

- deterministic atlas build,
- Godot import adapter,
- mobile memory/package benchmark,
- at least one real Mortofe animated character imported through the complete pipeline.
