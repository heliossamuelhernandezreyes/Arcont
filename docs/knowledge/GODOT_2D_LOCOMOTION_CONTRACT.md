# Godot 2D locomotion contract

Status: **working contract / Mortofe benchmark consumer**

Trigger consumer: `heliossamuelhernandezreyes/Godot-juegos-2d/Mortofe`

Engine scope: Godot `4.7.2-stable`, commit `ed1daf0bf001b61586d9930840f2f1394092c079`.

## Purpose

Define what ARCONT means by a production-capable 2D action-platformer locomotion baseline. A controller is not considered reusable merely because it can move and jump on a flat floor.

## Controller requirements

A baseline action controller should explicitly define and validate:

- horizontal acceleration and deceleration,
- separate ground and air control,
- jump impulse,
- variable jump height,
- coyote time,
- jump buffering,
- dash timing/cooldown and collision behavior,
- slope behavior,
- floor snapping policy,
- one-way platform interaction,
- moving-platform carry behavior,
- knockback interaction with ordinary movement,
- recovery after falling out of the world,
- input abstraction through InputMap so touch/gamepad/keyboard share gameplay code.

## Mortofe benchmark track

The first Mortofe slice now acts as an external runtime benchmark. It contains:

- ordinary ground,
- fixed raised platforms,
- a one-way platform,
- a walkable slope,
- an `AnimatableBody2D` moving platform,
- enemies that can apply knockback,
- dash and variable-height jump,
- mobile multitouch controls.

The benchmark exists to expose controller failures before level art hides them.

## Coyote-time contract

Leaving a valid floor may preserve jump eligibility for a small bounded interval. The interval must be deterministic and must not refresh in air.

Mortofe currently uses a short coyote window. Final tuning is product-specific; the reusable requirement is that the window can be measured and regression-tested.

## Jump-buffer contract

A jump press shortly before landing may be queued for a short bounded interval. Buffer state must be consumed after the jump and must not generate repeated jumps from one press.

## Variable-height jump

Releasing jump while ascending may reduce upward velocity to produce a shorter jump. This must coexist with buffered/coyote jumps and touch input.

## Slope contract

Validation should include:

- ascending and descending without visible jitter,
- stopping on a slope without unwanted sliding when product policy says the actor should hold position,
- transitions between flat floor and slope without launching the actor,
- dash behavior into and across slope boundaries.

## One-way platform contract

Validation should include:

- jumping upward through the platform,
- landing from above,
- moving horizontally while standing on it,
- future drop-through behavior if the game design requires it,
- no false grounding while below the platform.

## Moving-platform contract

Use `AnimatableBody2D` or another physics-consistent mechanism rather than teleporting a static collider from a render callback. Validate:

- horizontal carry,
- vertical carry when introduced,
- jumping from a moving platform,
- platform reversal under the actor,
- dash while carried,
- no accumulating positional drift.

## Mobile-specific validation

Touch locomotion must additionally verify:

- analog joystick deadzone,
- stable movement strength while a second/third finger attacks, jumps or dashes,
- no movement cancellation when action fingers release,
- thumb reach across supported aspect ratios,
- frame-time stability during movement + combat.

## Promotion criteria

`characterbody2d_locomotion` remains PARTIAL until automated or device-backed evidence covers the controller behaviors above. A headless parser/smoke run proves compatibility, not feel or physics quality.
