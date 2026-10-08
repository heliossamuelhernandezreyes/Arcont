# Map Forge editor control protocol v1

For arbitrary native engine and installed provider APIs beyond the canonical
map contract, use [General Godot authoring control](GODOT_AUTHORING_CONTROL.md).

This interface lets a human or assistant **operate the editor**. It does not
generate designs, call a model, interpret a prompt or require an API key. The
author decides every coordinate, material, route, object and mesh.

## Ownership

ARCONT owns the reusable protocol and `tools/map_forge_control.py`. A game owns
`map-forge.authoring.json`, its adapter, its contract, its editor and its runtime.
The control tool is an authoring-time dependency, never a shipped game dependency.

## Setup and discovery

Check out ARCONT separately and point `ARCONT_ROOT` to that directory. The game
configuration supplies `adapter_command` as an argv list; no shell interpolation
is used. `GODOT_BIN` selects the exact engine executable for engine operations.

```bash
python "$ARCONT_ROOT/tools/map_forge_control.py" --project /path/to/game --request request.json --output response.json
```

Start with `{ "protocol_version": 1, "operation": "capabilities" }`, then `list`
and `inspect`. Responses are JSON. A failed operation returns `ok: false` and a
nonzero process status. Complete map and optional physical-profile data are
returned by `inspect`, together with a revision hash.

## Operations

| Operation | Purpose |
|---|---|
| capabilities / list / inspect | Discover controls, maps and their complete state. |
| create / replace | Supply an entirely authored state. |
| patch | Edit any field using JSON Patch plus stable ID selectors. |
| restore | Restore a recorded revision after project validation. |
| validate / analyze | Ask the game adapter for contract validity or geometric analysis. |
| materialize / capture | Build native editor output and inspect rendered evidence. |

State is `{ "map": {...}, "physical": {...} }`; `physical` may be null. No
presets, art styles or genre-specific field allowlists are imposed by ARCONT.
The project validates its own rules and can preserve arbitrary extension fields.

## Editing loop for an assistant

1. Inspect the complete state and retain its `revision`.
2. Design explicit changes. Read project contracts; do not infer plugin support.
3. Submit create/replace/patch with `dry_run: true` (the default).
4. Read validation errors and changed paths; correct the request.
5. Submit with `dry_run: false` and `if_revision` for an existing map.
6. Materialize, capture several camera views, inspect the images and iterate.
7. Run navigation/playtest/device gates appropriate to the requested map.
8. Commit the authored source in the game repository. Store reusable findings
   in ARCONT rather than copying the game into this laboratory.

Example patch (replace the revision with the inspect response):

```json
{
  "protocol_version": 1,
  "operation": "patch",
  "map_id": "my_arena",
  "if_revision": "SHA256_FROM_INSPECT",
  "dry_run": false,
  "patch": [
    {"op": "replace", "path": "/map/routes/@main_lane/width", "value": 12},
    {"op": "replace", "path": "/map/authoring/terrain/landforms/@north_ridge/height", "value": 24}
  ]
}
```

`@id` selects exactly one array item by its stable ID. Numeric array indices,
escaped JSON pointers, add/remove/replace/test/copy/move are also supported.
Objects and unknown extension fields remain editable. New collection items are
added at `/-`; required parent objects must already exist or be added first.

## Integrity and limits

Edits operate on a copy, validate the final state, check the existing revision
again under a writer lock, archive revisions and replace source files. A failed
write attempts to restore the original source bytes. Map and physical files are
separate filesystem replacements; external readers should read after a completed
response. This is not a filesystem-wide atomic transaction.

Validation is mechanical. It does not establish gameplay balance, asset quality,
optimal navigation or Android performance. A capture is visual evidence. Adapter
execution requires the configured project tools and engine. Stale lock files
after an interrupted writer must be reviewed before removal.

## Close Seal reference integration

The reference adds a World 3D panel, a complete JSON inspector, a Control panel,
native mesh definitions and placement of imported PackedScenes. Its Python
adapter reuses the existing game validators, and its Godot worker builds and
captures the same authored state. See the game-owned authoring documentation.
Runtime confidence remains tied to the exact engine checks performed in CI.

## General environment authoring

A project can distinguish `purpose: environment` from competitive game rules.
Environment mode must permit empty gameplay collections and must not inject
unrequested battlefields, rivers or boundaries. Arbitrary meshes (including
UVs and collision), resource instances, transform groups, heightfield chunks,
PBR materials and authored lights form a reusable scene composition contract.
The project owns its renderer and acceptance gates.

`brush` is an explicit editor operation with the same revision, dry-run,
validation, history and rollback semantics as patch. Options: `heightfield_id`,
world `center: [x,z]`, `radius`, `strength`, and `mode`: raise, lower, flatten,
smooth, paint, hole or fill. Flatten also accepts `height`; paint requires an
existing `material` id. Each heightfield stores columns/rows, positive X/Z
spacing, translated origin, row-major vertex heights, and row-major cell paint
and hole arrays. Heightfields are axis-aligned; use triangle geometry for
overhangs and caves. Brushes never decide the map layout.

`edit` lets the game adapter prepare a new state (for example `terrain_pull`
from an installed terrain provider). The tool validates and commits that state
through the ordinary revision-checked transaction. A successful provider
response is not permission to bypass canonical validation. Provider writes
and external files are not covered by the JSON writer's rollback guarantee.

World navigation should be baked from actual collision geometry when obstacles
must affect movement. Route-only navigation remains a different supported mode.
Rendered geometry, saved collision and successful path queries are distinct
acceptance evidence.
