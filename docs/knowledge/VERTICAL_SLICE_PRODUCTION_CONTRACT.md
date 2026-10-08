# ARCONT — Mission / Vertical Slice Contract (design-only)

**Purpose:** Give an AI agent or developer a portable way to specify a small complete game mission, detect contradictory objectives, unreachable phase states, unsupported encounter rosters, and missing QA gates **before** changing any production game.

ARCONT is a technical knowledge laboratory. This contract and validator are **generic tooling**, not a playable project, a Godot editor, or a game-specific feature.

## Canonical assets

- **Schema:** [`schemas/vertical-slice-contract.schema.json`](../../schemas/vertical-slice-contract.schema.json), Draft 2020-12 structural fields.
- **Validator:** [`tools/vertical_slice_contract.py`](../../tools/vertical_slice_contract.py), Python standard library, semantic cross-reference/graph checks.
- **Example:** [`templates/mission_slice/mission_contract.example.json`](../../templates/mission_slice/mission_contract.example.json), deliberately generic; no FISURA production data.
- **Tests:** `tests/test_vertical_slice_contract.py`, positive and negative controls.

## Validation tiers (never confuse these)

| Tier | Evidence | Claims allowed | Cannot claim |
|---|---|---|---|
| M0 — schema/contract | Positive/negative tool tests + validated JSON | IDs, caps, zone membership, phase reachability, reference integrity | World navigable, playable mission |
| M1 — map/runtime | Exact-engine scene load, navigation reachability, FSM playthrough | Specific quest implemented and completable in controlled setup | Combat fairness, visual polish |
| M2 — art & combat | Controlled rendered screenshots + telemetry and actor tests | Specific systems visibly render / obey rules | AAA-like feeling, human comprehension |
| M3 — physical device | Install + launch + sustained device traces | Target device frame pacing, thermals, touch behaviour **on tested configuration** | General Android performance |
| M4 — playtest | Human observational sessions with stated method | Measured comprehension, frustrations and mission duration | Commercial AAA production maturity |

The `implementation_status` flag tells whether the JSON is **`design_only`**, **`in_development`**, or **`implemented`**. A validator PASS does not promote it.

### Run the semantic gate

```bash
python tools/vertical_slice_contract.py templates/mission_slice/mission_contract.example.json
python -m unittest tests.test_vertical_slice_contract -v
```

A game repo can pin a proven ARCONT revision and run, for example:

```bash
python _arcont_reference/tools/vertical_slice_contract.py missions/my_mission.slice.json
```

Only GitHub branches with tool + tests merged and passing may be described as a supported validator version. **Do not** use "latest main" silently for evidence-sensitive QA; pin a commit hash.

## Design fields and dependencies

The reusable mission JSON contains `map`, `duration_minutes`, hostile `caps`, gameplay `zones` and `anchors`, enemy `roles`, required `objectives`, ordered `phases`, grouped `encounters`, guarded `transitions`, terminal/failure states and `qa_gates`.

- **Zones** are declared rectangles; **anchors** must fall inside named zones and overall map bounds. This is a *design* coordinate check, not physics.
- **Objectives** belong to a phase and point to either a zone or an interactable anchor.
- **Encounters** declare role counts, spawn references, max concurrent attackers and telegraph timing; the validator rejects impossible static quotas.
- **Transitions** cite required objectives and form a graph from the first phase to victory. The validator detects missing required gates and unreachable phases.
- **Hostile caps** distinguish a conservative suggested mobile count from an absolute ceiling. These are *design budgets*, not measured CPU/GPU budgets.

### Missing evidence this tool intentionally does not fabricate

- It **does not** assess whether a corridor contains accessible walkable geometry or a functional navmesh, nor compute distances to doors through actual walls.
- It **does not** assert enemies spawn fairly relative to a live player or cannot fire through walls.
- It **does not** test game feel, artistic quality, audio, frame time or mobile input.
- It **does not** import/simulate Godot or generate any scene.
- It **does not** automatically open a gate; the production game must implement its own authoritative FSM.

### Suggested independent rubrics

1. **Encounter clarity:** role recognition, attack pre-warning, suitable counterplay, spawn visibility, target priority and recovery time. Record evidence with player footage and deterministic combat tests.
2. **Spatial readability:** objective line-of-sight, route alternatives, obstruction-proof camera, cover accessibility, height changes and sightline audit. Mark *testable on map* versus *requires gameplay observation*.
3. **Art direction:** shot consistency (same camera position/time/resolution), silhouette and hierarchy, PBR material provenance and thermal budget, not asset quantity.
4. **Game feel:** movement starts/stops, ability to fire while moving, damage fairness, perceptual recoil, missed-input frequency and accessibility controls. Human test required.
5. **Android performance:** export → install → launch → 15-minute run → p50/p95/p99 frame intervals, thermal context, GPU if available, input multi-touch and crashes; never infer from a successful APK build.

### ARCONT responsibility and limitations

A useful next tool would correlate mission objectives with actual Godot scene anchors and navigation reachability, **without bringing gameplay into ARCONT**. Prefer engine-neutral data exchange and **game-owned harnesses**. The existing Map Forge validator already handles map semantics but cannot substitute this mission graph, and the mission graph cannot substitute Map Forge's spatial contract.

## ARCONT mission-to-map bridge

`tools/mission_map_bridge.py` cross-validates one game-owned mission and its Map Forge JSON: declared path, level bounds, anchor IDs/coordinates and spawn team/kind. It resolves a separate semantic drift failure discovered while moving FISURA Reactivo-13 from document into a real Godot scene. It **cannot** prove pathfinding, physical collision, camera quality or playing the scene. Invoke `python tools/mission_map_bridge.py missions/example.slice.json maps/example.json` and separately validate the actual scene in the target engine.
