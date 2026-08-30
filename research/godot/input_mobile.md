# Godot — Mobile Input and Touch UX

## Engineering rules
- Track touch IDs/finger ownership explicitly.
- Movement, look and action touches must coexist.
- Avoid accidental mouse/touch emulation loops.
- Consume GUI/gameplay events deliberately.
- Separate raw input acquisition from gameplay commands.
- Expose sensitivity and eventually HUD layout/remapping.

## UX research queue
- Thumb reach zones and handedness.
- Tap vs hold vs drag conflict resolution.
- Contextual actions to reduce button count.
- Gyroscope aiming and calibration.
- Aim assist: slowdown, friction, magnetism, rotational assist; evaluate ethically and separately by input type.
- Swipe acceleration curves.
- Deadzones and response curves for gamepads.
- Haptics as feedback, not noise.
- Accessibility: hold/toggle alternatives, reduced rapid tapping, scalable controls.

## Arcont risk
The current action vocabulary is large: move/look/fire/ADS/reload/weapon/crouch/dodge/melee/throwable/R-3/camera/menu. A phone HUD can become cognitively and physically overloaded even if multitouch code is correct.

## References
- Godot InputEventScreenTouch: https://docs.godotengine.org/en/stable/classes/class_inputeventscreentouch.html
- Godot InputEventScreenDrag: https://docs.godotengine.org/en/stable/classes/class_inputeventscreendrag.html
- selgesel mobile TPS (MIT): https://github.com/selgesel/godot4-third-person-controller
- etherealxx mobile TPS (MIT): https://github.com/etherealxx/Godot-Third-Person-Controller-Mobile

## Status
Finger ownership architecture: IMPLEMENTED.
Ergonomics/gyro/assist/configurable HUD: OPEN.
