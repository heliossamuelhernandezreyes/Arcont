# Gameplay — Game Feel

Game feel is the relationship between input, simulation, animation, camera, audio and visual response. It must be tuned as a system.

## Shooter response chain
Input -> trigger latency -> weapon animation -> recoil -> muzzle VFX -> projectile/raycast -> impact -> target reaction -> audio -> camera/controller feedback.

Measure and tune the complete chain rather than polishing components in isolation.

## Useful tools
- Input buffering where appropriate.
- Short anticipation for readable heavy actions.
- Recoil patterns with recoverability.
- Camera impulse with accessibility scaling.
- Hit reactions proportional to weapon/target state.
- Micro-pauses/hit-stop mainly for melee/heavy impacts; avoid disrupting rapid gunfire.
- Screen effects kept subordinate to target readability.
- Strong sound transients and material response.
- Animation pose quality and weapon inertia.
- Enemy telegraphs and recovery windows.

## Questions for every action
- Is intent obvious before it happens?
- Is response immediate enough?
- Does the result communicate force?
- Can the player understand why they missed/took damage?
- Does feedback obscure gameplay?
- Does it remain comfortable on a phone?

## Arcont priorities
1. Move/look latency.
2. ADS transition.
3. Fire/recoil/impact.
4. Damage and limb reaction.
5. Dodge/vault/mantle commitment.
6. Melee/parry/execution readability.
7. R-3 command acknowledgement.

## Reference-study targets
Gears of War (cover/active reload/combat cadence), The Last of Us (impact/animation), Dead Space (functional dismemberment), F.E.A.R. (combat-space AI/readability), Helldivers (pressure/readability), Resident Evil (encounter staging), Metal Gear (awareness), Left 4 Dead (director/pacing), Doom (enemy roles and combat readability). Study principles, not assets/code.
