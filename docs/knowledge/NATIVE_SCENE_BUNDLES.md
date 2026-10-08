# Verified native scene bundles

The public `production_toolchain.py bundle` operation relocates a candidate produced
under a game's `.arcont/runs` into that game's managed `assets` directory. The game
owns native meshes, editor adapters, scenes, collision, lighting and runtime code.
Arcont owns reusable transport and integrity rules.

Supply a JSON record with project-relative `source`, `destination`, and explicit
`files` mapping relative artifact names to SHA-256. The command verifies every byte
before publication, rejects empty artifacts, traversal, symlinks, unsupported files
and references to other unpublished candidates. Text scene/resource paths are
relocated; opaque binary resources are copied unchanged. It refuses unmanaged
destinations. `--replace` replaces only its own marked directory, with rollback if
publication fails. The receipt preserves original and relocated hashes.

```sh
python tools/production_toolchain.py bundle candidate.json --project /path/to/game
```

Reopen the relocated scene in the exact engine, import its textures and validate its
exported resource closure. Compressed binary external references cannot be inspected
by this tool. Prefer external text resources for references that require relocation.
Any later bake is a separate game-owned operation and needs its own output hashes;
the original receipt must remain an honest description of the pre-bake candidate.

Godot's native LightmapGI can supply static indirect light and probes for moving
actors. UV2 resources and geometry ownership need to survive saving and reopening.
Keep imported scene ownership when packing: flattening every descendant may embed
duplicate mesh data. Discover the installed API before choosing an adapter.
Godot 4.7.2 does not expose `LightmapGI.bake` to GDScript; an editor operation needs
a tested game-owned editor adapter. A discovered class alone is not bake support.

The engine's Compatibility renderer can display baked lightmaps; baking requires
a RenderingDevice backend. Do not infer performance gains or Android compatibility
from successful authoring. Measure the exported game on its actual target handset.
Keep matched camera/resolution captures, collision/navigation checks and source
hashes alongside each visual revision. Numerical integrity does not certify AAA art.

Primary references:

- https://docs.godotengine.org/en/stable/classes/class_lightmapgi.html
- https://docs.godotengine.org/en/stable/tutorials/3d/global_illumination/using_lightmap_gi.html
- https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html
- https://www.gdcvault.com/play/1025165/Inertialization
