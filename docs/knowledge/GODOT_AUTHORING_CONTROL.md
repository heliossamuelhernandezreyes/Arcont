# General Godot authoring control v1

ARCONT can operate a project's native Godot APIs and installed provider scripts
through one revisioned interface. This complements Map Forge's canonical map
contract. It is not a model endpoint or a prompt-to-map generator.

The reusable Python control and optional MCP stdio server belong to ARCONT. A
game owns its engine adapter, GDScript bridge, authored recipes, scenes, resources
and acceptance checks. ARCONT still contains no embedded Godot game project.

## Entry points

```bash
python "$ARCONT_ROOT/tools/godot_authoring_control.py" --project /path/to/game --request request.json
python "$ARCONT_ROOT/tools/godot_authoring_mcp.py" --project /path/to/game
```

A project supplies `godot-authoring.json`: protocol_version 1,
`adapter_command` argv, `document_directory` and `timeout_seconds`. Start with
`capabilities`, then `discover`. Discovery runs the actual engine and inventories
native classes, singletons, installed scripts with SHA-256, and provider locks.
`options.class` or `options.script` returns properties, methods, signals and
constants from the actual installed version. Availability does not mean an API
was exercised successfully.

The stdio entry point exposes `arcont_authoring`, using exactly the CLI request
contract and writer. It supports initialize, ping, tools/list and tools/call;
UTF-8 JSON-RPC messages occupy one line each. A local MCP client must configure
the command and project path. This does not automatically install a connector
in ChatGPT or create a remote/live editor session.

## Authored documents

Requests use `protocol_version: 1`, an `operation`, and a `document_id` for
document operations. Recipes contain `version: 1`, matching `id`, and explicit
`steps`. There are no fixed genres, primitive presets or plugin method lists.
The reference engine adapter has the following general actions:

| Actions | Authoring capability |
|---|---|
| new / load / singleton / node | Construct any instantiable native class or installed script; load resources/scenes; reference engine services and scene children. |
| set / call | Assign exposed properties; call native or script methods, including asynchronous methods. |
| describe / inspect | Read live object metadata, storage properties and scene hierarchy. |
| attach / remove / wait | Enter the scene tree, delete objects and advance process/physics frames. |
| assert | Require a particular returned value; fail the candidate bundle otherwise. |
| save / capture | Save resources and owned scene hierarchies; capture an authored camera. |
| ray / profile | Query actual collision and collect authoring-process frame/render/memory measurements. |
| script | Run a trusted project `run(context, arguments)` extension for capabilities requiring typed collections, callbacks, baking, custom servers or specialist workflows. |

References use `{"$ref":"object_id"}`. Variant values use
`{"$type":"Vector3","value":[0,2,5]}` (and other advertised types).
`{"$output":"scenes/example.tscn"}` addresses a candidate bundle path.
The script context exposes `object(id)`, `register(id, value)`,
`output_path(relative)`, and the normal SceneTree API. Script extensions have
ordinary trusted Godot permissions. The interface deliberately has no class or
provider-method allowlist; it is not an untrusted-code sandbox.

Example creation, after inspecting the project configuration:

```json
{
  "protocol_version": 1,
  "operation": "create",
  "document_id": "courtyard",
  "dry_run": true,
  "recipe": {
    "version": 1,
    "id": "courtyard",
    "steps": [
      {"op":"new","id":"world","class":"Node3D","name":"Courtyard"},
      {"op":"new","id":"sun","class":"DirectionalLight3D","parent":"world","properties":{"light_energy":1.4}},
      {"op":"attach","target":"world"},
      {"op":"save","target":"world","path":"scenes/courtyard.tscn"}
    ]
  }
}
```

`create`, `replace`, `patch`, `restore`, and `build` actually execute the recipe.
Dry-run defaults to true; it builds evidence without publishing the document.
Existing documents require `if_revision`, including build. JSON Patch supports
stable IDs, e.g. `/steps/@sun/properties/light_energy`. `inspect` returns the
recipe, current revision and last successful bundle. `list` lists documents.
`restore_revision` rebuilds a recorded source revision with the current engine;
it does not pretend that two render runs are byte-identical.

## Publication and recovery

The writer locks the document before checking its revision and running the
engine. Each execution gets a fresh `.arcont/runs/<id>/<uuid>` directory, logs,
request/response and SHA-256 artifact manifest. Failed candidates retain evidence
and do not replace the successful head or its bundle. A successful commit archives
source revisions and atomically replaces **one head JSON file**, including the
recipe and its last-build manifest. A failure before that replacement preserves
the old head. Bundles referenced by successful heads must not be removed manually.

Optional recipe `dependencies` map project-relative paths to SHA-256. They are
checked before and after engine execution. Changed dependencies remain
inspectable and repairable. Recipes without pins deliberately use the current
project source. Provider lock and engine metadata are recorded, but complete
dependency closure, hermetic execution and filesystem-wide rollback are not
claimed. Engine resource UUIDs, timing and output paths may vary between runs.

Built-in saves only write inside the candidate bundle. Trusted adapters or
scripts can write elsewhere; those external side effects are outside this
publication guarantee. Do not invoke setters/methods that overwrite source
files unless their adapter explicitly stages those files. The timeout terminates
the adapter process group on POSIX. Stale writer locks after a crashed host must
be reviewed before removal.

## Evidence and scope

Python tests cover dry-run, immutable previous output, revision conflicts,
engine failure, interrupted publication, locking, symlink rejection, dependency
repair, history corruption and the shared MCP transport. The game reference
adds a pinned-engine acceptance job with real provider output, material edits,
save/reopen, spatial audio, collision rays, capsule movement, navigation paths
and camera captures. Consult the associated workflow result before claiming
engine validation for a particular commit.

This foundation makes additional tools accessible through their real APIs.
It does not establish complete automation of every researched plugin, AAA art
quality, live GUI manipulation, commercial platform readiness or Android FPS.
