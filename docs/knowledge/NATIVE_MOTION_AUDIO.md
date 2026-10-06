# Native motion and recorded audio preparation

Arcont production-0.4.0 supplies an authoring-only global rest-space bone transfer
helper (`tools/native_rest_retarget.gd`) and `production_toolchain.py audio` for
hash/PCM inspection. The helper is copied byte-for-byte into the game's tool
folder and pinned by the game lock; it is excluded from the shipped runtime.

The explicit partial bone map resolves global rotations through different parent
hierarchies. Target bone lengths remain intact. Root/hip displacement has an
explicit scale. Missing or duplicate target bones and empty maps are rejected
before mutation. This is not automatic rig recognition, a universal retargeter,
full-body IK, or contact correction. Native engine/proportion/contact review is
required for each target character. Project recipes and adapters remain game-owned.

Nexo operates the builder through discover/inspect/create-or-replace and saves an
AnimationLibrary in the native writer's output. The bundle command verifies the
exact bytes read and publishes it to a managed asset directory. The game cleans
up metre-based foot trajectories and preserves its physical movement speed.
CC0 source movement is keyframed, not motion capture. The native game tests measure
cadence, both-foot drift, weapon grip, reload events, routing and visible head hits.

Audio inspection checks declared source hashes, complete output closure, native
PCM format, peak and RMS levels. It refuses clipping/effectively silent clips.
It does not validate bus mixing, acoustics, latency, subjective quality or licensing
by sound. The game retains source licenses/credits and its native voice/event checks.

Bundle publication now uses Linux renameat2 (exchange for replacement, no-replace
for creation) under a project publisher lock. It validates the destination receipt,
recorded contents, symlinks and byte limits. An unsupported platform fails while
preserving the old directory; no two-rename atomicity claim remains. Atomic namespace
replacement is tested; filesystem durability after power loss is not established.
