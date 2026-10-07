# Structured Godot Editing v1

Structured Godot Editing gives a fresh ARCONT-compatible agent enough safe,
revision-checked primitives to turn a newly bootstrapped Godot project into
actual gameplay without requiring a project-specific authoring adapter first.

It complements, rather than replaces, `godot.authoring.control`:

- `godot.authoring.control` remains the richer recipe/adapter layer for
  arbitrary project-owned authoring workflows.
- `godot.structured.control` is the generic baseline available immediately
  after Project Bootstrap.

## Bridge operations

Read-only:

```text
godot.structured.validate
godot.script.inspect
godot.scene.inspect
godot.resource.inspect
```

Write-capable, requiring explicit project-write opt-in:

```text
godot.script.create
godot.script.replace
godot.script.function.replace
godot.scene.edit
godot.resource.edit
godot.input.action.set
```

All existing targets require `if_revision` SHA-256. Creation uses
`if_revision: null`.

## GDScript

Scripts are limited to `scripts/**/*.gd`.

Example creation:

```json
{
  "protocol": "arcont-bridge",
  "version": 1,
  "request_id": "create-player-script",
  "operation": "godot.script.create",
  "arguments": {
    "path": "scripts/player.gd",
    "if_revision": null,
    "source": "extends CharacterBody3D\n\nfunc _physics_process(_delta):\n    velocity = Vector3.ZERO\n"
  }
}
```

The source is written atomically and loaded by Godot. If Godot rejects it, the
previous bytes are restored (or the newly created file is removed).

`godot.script.function.replace` replaces one named top-level function instead
of rewriting the whole file:

```json
{
  "operation": "godot.script.function.replace",
  "arguments": {
    "path": "scripts/player.gd",
    "if_revision": "<current sha256>",
    "function": "_physics_process",
    "source": "func _physics_process(_delta):\n    velocity = Vector3(0, 0, -1)\n"
  }
}
```

V1 deliberately refuses privileged/editor/host surfaces such as:

```text
@tool
EditorPlugin / EditorInterface
OS.*
FileAccess / DirAccess
HTTPRequest / HTTPClient
TCP/UDP/WebSocket APIs
JavaScriptBridge
ProjectSettings.save
ResourceSaver.save
```

These checks are defense-in-depth and are **not** a complete GDScript sandbox.
Structured v1 is intended for ordinary gameplay code, not host automation,
editor plugins, filesystem tooling or networking.

## Scenes

Scenes are limited to `scenes/**/*.tscn`.

Supported changes:

```text
add
remove
set
attach_script
rename
```

The generic `set` operation cannot set `script`, `owner`, or
`scene_file_path`; scripts must go through `attach_script`. Before an
existing project script is attached, ARCONT applies the same structured
GDScript safety checks used for newly generated source.

Example:

```json
{
  "operation": "godot.scene.edit",
  "arguments": {
    "scene": "scenes/main.tscn",
    "if_revision": "<sha256>",
    "changes": [
      {"op":"add","parent":".","name":"Player","type":"CharacterBody3D"},
      {"op":"attach_script","path":"Player","script":"res://scripts/player.gd"},
      {
        "op":"set",
        "path":"Player",
        "property":"position",
        "value":{"$type":"Vector3","value":[0,0,0]}
      }
    ]
  }
}
```

Godot itself loads, mutates, packs and saves the scene.

Structured values support ordinary JSON plus typed descriptors:

```json
{"$type":"Vector2","value":[1,2]}
{"$type":"Vector3","value":[1,2,3]}
{"$type":"Color","value":[1,0.5,0,1]}
{"$type":"NodePath","value":"Player/Camera3D"}
{"$type":"Resource","path":"res://resources/player_mesh.tres"}
```

## Resources

V1 writes text resources below:

```text
materials/**/*.tres
resources/**/*.tres
assets/generated/**/*.tres
```

Example:

```json
{
  "operation": "godot.resource.edit",
  "arguments": {
    "resource": "resources/player_mesh.tres",
    "if_revision": null,
    "resource_type": "BoxMesh",
    "changes": [
      {
        "op":"set",
        "property":"size",
        "value":{"$type":"Vector3","value":[0.8,1.8,0.8]}
      }
    ]
  }
}
```

Existing resources require their current revision. Structured resource edits
cannot set the `script` or `resource_path` properties, and V1 refuses
`GDScript`, `Script`, and `PackedScene` as generic resource types so the
resource editor cannot be used as a back door around the dedicated script/scene
controls.

## Input actions

Input actions modify `project.godot` through Godot's ProjectSettings API.

Supported V1 event descriptors:

```json
{"type":"key","keycode":"W","physical":true}
{"type":"mouse_button","button_index":1}
{"type":"joypad_button","button_index":0}
```

Example:

```json
{
  "operation":"godot.input.action.set",
  "arguments":{
    "if_revision":"<project.godot sha256>",
    "action":"move_forward",
    "deadzone":0.2,
    "events":[{"type":"key","keycode":"W","physical":true}]
  }
}
```

## Relationship to authoring recipes

This layer is intentionally smaller than the existing recipe system.

A generic fresh agent can now:

```text
bootstrap
  -> create input
  -> create GDScript
  -> create resources
  -> edit scene
  -> run/playtest
```

Once a project develops repeated domain-specific workflows, those can graduate
into project-owned recipes and adapters consumed by `godot.authoring.control`.

## Limits

V1 does not claim:

- a complete language sandbox;
- arbitrary editor plugin development;
- arbitrary source-language editing beyond GDScript;
- shader source editing;
- dependency-aware scene refactors across an entire project;
- visual/feel quality;
- Android performance;
- unattended unlimited self-modification.

Mutation remains explicit, revision-checked, bounded and evidence-producing.
