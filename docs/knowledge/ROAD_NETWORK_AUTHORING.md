# Explicit road-network authoring

RoadGenerator is integrated as a game-owned provider through the existing
general Godot bridge. ARCONT owns source validation and revisioned recipe
publication, not a copied addon, game project or traffic generator.

`tools/road_network_contract.py` accepts an explicit version-1 network:
`roads` is an array of stable-ID chains. Each road specifies an ordered array
of `forward`/`reverse` lanes, lane width, shoulder width, deck thickness,
mesh density (metres between cuts), optional `closed`, and `points`.
Each point has a globally unique ID, position `[x,y,z]`, tangent `[x,y,z]`,
and optional nonnegative `handle_in`/`handle_out` magnitudes. Positive local Z
follows the tangent. Coordinate units are metres. Validation checks finite
values and topology prerequisites; it does not assess road safety, curvature,
intersection correctness or art quality. It does not choose geometry.

```bash
python tools/road_network_contract.py network.json
python tools/godot_authoring_control.py --project /path/to/game --request request.json
```

The game adapter invokes RoadManager/RoadContainer/RoadPoint and real provider
connection/rebuild methods using a trusted `script` recipe step. Native `set`
and `call` can operate registered points/containers; discovery exposes real
provider methods. Scene recipes can be edited through the same revision-checked
CLI, Map Forge Control panel or MCP writer. Stable-ID JSON patch example:

```json
{"protocol_version":1,"operation":"patch","document_id":"urban_roads",
 "if_revision":"<current revision>","dry_run":false,
 "options":{"render":true,"audio_driver":"Dummy"},
 "patch":[{"op":"replace",
 "path":"/steps/@roads/args/network/roads/@boulevard/points/@west_bend/position",
 "value":[-55,0.08,-14]}]}
```

Close Seal's implementation saves an editable scene of source points and
connections, rebuilding runtime caches on load, and a separate baked scene
containing native meshes, trimesh collision, baked navigation and lane paths.
Generated segments are excluded from the editable PackedScene because their
upstream constructor requires a container argument. Baked lane links are
provider-relative provenance metadata, not a portable traffic controller.

Source pin: `TheDuckCow/godot-road-generator` commit
`9d144dc4a28dd6bee870895d2b77d69174356281`, MIT; only the addon directory is
installed and its license is retained. Existing game assets retain their own
CC0 source lock. See the game recipe `authoring/recipes/urban_roads.json` and
`docs/map_forge/ROAD_NETWORK.md` for the measured acceptance scope and evidence.
Terrain flattening, procedural intersections, traffic and target-device FPS
need separate acceptance; API availability alone does not validate them.
