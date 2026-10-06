# TPS mobile finish acceptance

This profile complements the separate tactical RTS 3D standard. Close third-person
cameras need contacts, signed movement/cadence, transitions, weapon hand alignment,
material/lighting coherence and readable hostile silhouettes.

`production_toolchain.py finish native-record.json --profile profile.json` validates
native measurements emitted by a game-owned adapter. ARCONT contains the validator,
profile and quality policy; character rigs, clips, gameplay, assets and captures
remain in the production game. Exit 1 also indicates a completed but technically
failed review; inspect `ok` and `technical_passed` separately.

The first profile checks eight motion cases, both feet, at least twenty actual stance
samples per case, 3 cm maximum world-space drift, 1.5% signed cadence error and 4 cm
weapon grip error. Targets are tunable project decisions, not AAA industry standards.
Signed cadence checks body velocity plus retimed foot velocity: equal magnitudes moving
in the same direction are a failure. A contact sample records its world anchor and
actual modified foot position; numerical compliance does not approve the visual pose.

Records require exact engine identity, source hashes and explicit visual-review notes.
The supported scope is controlled native motion. Pair it with runtime input replay and
rendered sequences for start, stop, turns, cover, reloading, slopes and traversal.
Current observations do not establish complete gameplay animation quality.

Use the visual rubric for weight/balance, continuity, contacts, hostile readability and
material/light coherence. Retain comparable cameras and resolution. Honest notes must
identify remaining problems rather than translate passed numeric checks into a finish score.

Target handset acceptance separately requires 15+ minutes of active play, cold/warm
windows, frame-time distributions, pauses, renderer, resolution and memory scope.
Thermal and touch-latency observations should name their actual measurement method.
Desktop or synthetic long-session recorder tests are not Android FPS results.

Sources: The Coalition's GDC 2017 Motion Warping in Gears of War 4;
Infinity Ward's 2019 Modern Warfare animation/authenticity interview;
Naughty Dog's GDC 2021 Motion Matching presentation; Godot's renderer and LightmapGI
documentation. Apply the principles through tested game-owned Godot adapters.
