# Project Bootstrap + User Asset Intake v1

This layer lets a fresh ARCONT-compatible agent start from an existing **empty
external directory** and turn it into a minimal runnable Godot project, then
stage individual files supplied by the user.

It does not make ARCONT a game repository. Generated production files live only
in the external project.

## Bootstrap

Bridge operation:

```json
{
  "protocol": "arcont-bridge",
  "version": 1,
  "request_id": "bootstrap-001",
  "operation": "project.bootstrap",
  "arguments": {
    "template": "godot-3d-minimal",
    "intent": {
      "protocol": "arcont-project-intent",
      "version": 1,
      "project_id": "my_game",
      "title": "My Game",
      "genre": "third-person action",
      "targets": ["Windows", "Android"],
      "asset_policy": {
        "user_assets": true,
        "public_assets": false,
        "commercial_use_required": true,
        "allow_network_discovery": false
      }
    }
  }
}
```

The caller must pass `--allow-project-write`.

Supported templates:

- `godot-3d-minimal`
- `godot-2d-minimal`

The destination must already exist and be empty. Bootstrap prepares the full
tree in a sibling staging directory and only then replaces the empty target.
It creates:

```text
project.godot
project.intent.json
scenes/main.tscn
assets/user/
incoming/
scripts/
materials/
audio/
authoring/recipes/
authoring/scenarios/
tests/
.arcont/bootstrap.json
.arcont/assets/user/
```

The bootstrap receipt records hashes of the canonical starter files. No network
access occurs.

## User asset intake

Files supplied by the user are first placed below:

```text
incoming/
```

V1 accepts individual local files only. It does not extract archives.

For 3D user models, V1 accepts **GLB only** so the staged file is self-contained. Dependency-bearing formats such as `.gltf`, `.obj`, `.dae`, and `.fbx` are rejected until ARCONT can validate and stage a complete dependency closure.

Read-only inspection:

```json
{
  "protocol": "arcont-bridge",
  "version": 1,
  "request_id": "asset-inspect-001",
  "operation": "asset.user.inspect",
  "arguments": {
    "source": "incoming/hero.glb"
  }
}
```

Staging:

```json
{
  "protocol": "arcont-bridge",
  "version": 1,
  "request_id": "asset-stage-001",
  "operation": "asset.user.stage",
  "arguments": {
    "asset_id": "hero",
    "source": "incoming/hero.glb",
    "rights": {
      "basis": "user-owned",
      "commercial_use": true,
      "redistribution": false,
      "license_name": null,
      "attribution": null
    }
  }
}
```

Staging requires explicit project-write permission.

The asset is copied to a type-specific path below `assets/user/` and ARCONT
writes a provenance record below:

```text
.arcont/assets/user/<asset_id>.asset.json
```

The record stores source/staged path, SHA-256, bytes, kind, extension and the
user's rights declaration.

## Rights boundary

ARCONT does **not** infer ownership or license rights from a file.

The v1 declaration basis is one of:

- `user-owned`
- `licensed`
- `public-domain`

A record is explicitly marked:

```text
user-declared-not-verified-by-arcont
```

If the project intent requires commercial-use assets, staging refuses a
declaration with `commercial_use=false`. Licensed assets can also be checked
against the project's allowed/forbidden license lists.

This is provenance and policy enforcement, not legal verification.

## V1 limits

The following are intentionally not part of #33:

- Internet asset search or download;
- ZIP/archive extraction;
- automatic license inference;
- Blender/FBX conversion;
- rig/animation semantic validation;
- generated gameplay code beyond the minimal Godot shell;
- unattended iterative game generation.

Those belong to later layers after the local creation path is proven.
