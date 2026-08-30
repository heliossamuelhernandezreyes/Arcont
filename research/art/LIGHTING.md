# Lighting Guide

## Goal
Lighting must establish mood, depth, navigation and combat readability while respecting Forward Mobile limits.

## Principles
- Establish large value structure first: key direction, sky/ambient fill and readable shadow shapes.
- Use contrast to guide attention; do not make every corner equally dramatic.
- Separate enemies/player/interactables from background values.
- Prefer a few meaningful shadowed lights over many expensive ones.
- Treat emissive signs, emergency lights and muzzle flashes as accents, not ambient replacement.

## Exterior baseline
Directional key + sky/ambient environment + selective local lights. Use architecture to create light/shadow rhythm. Avoid crushing shadow detail on phone displays.

## Interior baseline
Use authored light hierarchy and, when production layout is sufficiently stable, evaluate baked/lightmapped solutions for static contribution. Dynamic lights are reserved for gameplay, moving fixtures, muzzle flashes and key effects.

## Mobile renderer knowledge
Godot Forward Mobile uses single-pass lighting and has per-mesh light limits; shadow-casting lights are substantially more expensive than unshadowed lights. Therefore light overlap must be designed deliberately.

## Tonemapping and exposure
Pick one production tonemapping policy and judge materials under it. Avoid changing exposure to rescue badly authored assets. Check bright highlights and dark interiors on actual phone displays.

## Atmosphere
Fog/haze should create depth and mood only when it remains affordable and does not erase target silhouettes. Prefer level composition and value separation before expensive atmospheric tricks.

## Calibration scene
Maintain neutral material spheres/objects plus human, weapon, vehicle and architecture under a neutral lighting rig. Artistic scene lighting should be judged separately from material correctness.

## Audit questions
- Can the player immediately identify threats and traversal space?
- Are shadows hiding mechanics?
- Is a light actually contributing enough to justify a shadow?
- Does the frame retain depth without post-process abuse?
- Does it survive reduced mobile brightness and small-screen viewing?
