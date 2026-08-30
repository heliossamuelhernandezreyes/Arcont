# Arcont

Godot 4.7.x tactical third-person action prototype, currently focused on an Android-first vertical slice.

## Current prototype

- Third-person camera with shoulder ADS and camera collision.
- Mobile multitouch movement, camera look, fire, ADS, dodge, crouch, melee, reload, weapon switch, throwable and R-3 command controls.
- Five provisional weapon profiles with penetration and active reload timing.
- Directional melee/parry/execution prototype.
- Infected, tactical ranged enemies, Xeno Lancer and Xeno Stalker.
- R-3 companion commands.
- Procedural ruined urban test district using CC0 provisional assets.
- Android export through GitHub Actions.

## Mobile TPS rescue

The `fix/mobile-camera-foundation` branch removes the old first-person weapon/camera coupling. `ThirdPersonADS` is the sole owner of physical `Camera3D` positioning; combat feedback only uses optical offsets. The weapon controller now lives under `Player`, while its provisional visual lives on the operator's world-space `WeaponMount`. Touch input tracks fingers independently so movement, look and combat inputs can coexist. Android uses Godot's Mobile renderer with a brighter fog-free fallback-safe environment.

The CI pipeline verifies project import, character rig/animations, structural TPS invariants, a main-scene boot and Android APK export. A passing CI build is still followed by real-device validation for camera feel, touch ergonomics, rendering and performance.
