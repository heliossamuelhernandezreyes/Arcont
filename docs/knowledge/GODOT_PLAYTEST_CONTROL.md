# Input-driven playtest and observation v1

`godot_authoring_control.py` and the existing MCP `arcont_authoring` tool share
the `playtest` operation. The project supplies `godot-authoring.json` with
`playtest.script`, pointing to its trusted GDScript runner. ARCONT retains the
reusable session validation, revision lock and immutable evidence writer; the
game retains the runner, controller, geometry, scenes and gameplay.

This is bounded batch control of a fresh saved scene, not a resident remote
editor session. It reuses the general bridge rather than introducing a second
writer. Every operation requires the current document revision and selects a
scene artifact from that document's last accepted bundle. Its SHA-256 is checked
before and after execution. The authored recipe and dependencies are checked;
playtest never publishes a new document head. Referenced asset closure is not
guaranteed beyond the dependencies explicitly pinned by the recipe.

Example, after `inspect` of the scene document:

```json
{"protocol_version":1,"operation":"playtest","document_id":"urban_playtest",
 "if_revision":"<current revision>","scene":"scenes/urban_roads_editable.tscn",
 "options":{"render":true,"audio_driver":"Dummy"},
 "session":{"version":1,"id":"door_check","actor":"Actors/Explorer","seed":41,
 "commands":[{"id":"walk","frames":120,"actions":{"arcont_forward":1},
 "capture":"Cameras/Entrance","expect":{"position":[-30,0.15,16],"tolerance_m":0.8}}]}}
```

The session validator rejects unknown fields, escaping NodePaths, non-finite or
out-of-range strengths, duplicate command IDs and more than 3600 physics frames.
Each command replaces held actions; an empty action map releases them and waits.
Capture requests require rendering. Actual InputMap names must exist in the
loaded scene. `stop_on_failure` defaults to true. Expectations support position
and tolerance, minimum height, and minimum interaction count.

## Execution and outcome

`ok: true` means the runner completed and produced valid evidence. `passed`
reports whether authored expectations were satisfied. A blocked route is a
completed session with `passed: false`, not a successful gameplay result. CLI
exit status and MCP `isError` describe execution; consumers must inspect `passed`.

The reference game actor exposes `begin_playtest`, `end_playtest`,
`playtest_snapshot` and a `playtest_tick(Dictionary)` signal emitted after its
normal physics movement. The runner injects `InputEventAction` through
`Input.parse_input_event`, not direct velocity assignments. The controller reads
Input, performs collision movement and handles interaction events. Production
controllers can implement the same instrumentation; the fixture is not a
validated combat, enemy-AI or networking controller.

Evidence includes a JSONL state/contact trace for each completed actor tick,
checkpoint JSON, real checkpoint camera PNGs, navigation diagnostics, source
scene hashes, session commands and the usual engine logs/artifact manifest.
The scene tree is paused for checkpoint captures so screenshots do not advance
the observed controller. The reference cleans up held input after normal or
expectation-failed sessions. Adapter/process errors remain execution failures.

## Reference acceptance

Close Seal's `playtest_loop_smoke.py` authors a workshop with physical stairs
alongside the existing RoadGenerator scene. It saves and reopens the source,
observes an entrance blocker, patches the editable collision/visual source,
replays exactly the same commands, climbs stairs, interacts with a terminal,
repeats the route and restores the blocked source. Original scene bundles and
canonical map bytes must remain unchanged. The actual editor also opens the
accepted building and edits a source wall through its installed control panel.

Consult the paired PR and engine workflow before treating this acceptance as
validated. Repeatability is checked on the pinned Linux runner with 1mm position
tolerance; it does not establish bitwise/cross-platform determinism. Seeded
sessions do not make every physics backend deterministic. Checkpoint image
timings are not a device FPS benchmark. Live sessions, general audio recording,
video streaming, production controller coverage and device performance remain
separate work.
