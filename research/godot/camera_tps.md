# Godot — Third-Person Camera

## Arcont principles
- One system owns physical camera position/orbit.
- SpringArm3D is the default collision mechanism for a shoulder camera.
- Camera orbit and character facing are related but not identical state.
- ADS should transition camera/FOV/shoulder composition without moving weapon ownership into the camera hierarchy.
- Exclude the player's collision RID from camera collision when appropriate.
- Camera feedback should be layered: recoil/impulse/noise must not fight base camera control.

## Topics to preserve and test
- Shoulder swap and obstruction-aware shoulder choice.
- Near-wall aim correction and muzzle/camera parallax.
- Camera collision smoothing and rapid geometry changes.
- ADS transition curves and FOV accessibility.
- Lock-on only if future design needs it.
- Camera-relative movement vs aim-relative facing.
- Motion sickness: shake amplitude, FOV, acceleration and optional reductions.
- Photo/spectator/debug cameras as future tooling.

## Sources
- Godot SpringArm3D documentation: https://docs.godotengine.org/en/4.7/tutorials/3d/spring_arm.html
- GDQuest Godot 4 3D third-person controller: https://github.com/gdquest-demos/godot-4-3d-third-person-controller
- selgesel touchscreen TPS controller (MIT): https://github.com/selgesel/godot4-third-person-controller
- Jeh3no third-person controller (MIT): https://github.com/Jeh3no/Godot-Third-Person-Controller

## Current status
Core ownership pattern: IMPLEMENTED.
Feel/parallax/obstruction polish: TESTING / OPEN.
