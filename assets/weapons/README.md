# Arcont Weapon Art Contract

The five gameplay weapons already exist mechanically. This folder is the destination for authored weapon art that will replace the current ART-PASS-1 procedural silhouettes without changing combat code.

## Slots
0 — 12G Shotgun
1 — AR-5 Rifle
2 — P9 Pistol
3 — M90 Bolt Sniper
4 — BR-7 Bayonet Rifle

## Authoring contract
- Godot units: 1 unit = 1 meter.
- Forward axis: local -Z.
- Origin: practical grip/receiver mount, suitable for `Player/BodyVisual/WeaponMount`.
- Muzzle socket must sit at the true barrel exit.
- Do not bake camera offsets into the mesh.
- Keep gameplay collision independent from the render mesh.
- Prefer GLB for final interchange into Godot.
- Materials should follow the Arcont art bible: restrained gunmetal/polymer/paint hierarchy, physically sensible metallic/roughness and purposeful accents.
- Each weapon must remain recognizable by silhouette at phone gameplay distance.
- Hero detail should be concentrated around receiver, sights, magazine/feeding system, muzzle and distinctive role-specific features.

## Current procedural silhouette targets
Approximate visible longest-axis contracts used by CI:
- 12G: 1.45–1.95 m
- AR-5: 1.45–1.90 m
- P9: 0.55–0.90 m
- M90: 2.05–2.65 m
- BR-7: 1.75–2.30 m including bayonet

These are validation envelopes, not sacred final design dimensions. Any deliberate change should update both the art decision record and the test.

## Replacement strategy
`WeaponVisualFactory` currently creates an `ART-PASS-1-PROXY` silhouette for each slot. Final authored scenes should be loadable by visual ID (`12g`, `ar5`, `p9`, `m90`, `br7`) and should preserve the same WeaponMount/muzzle interface. Ballistics, ammo, reload and recoil must remain independent from the mesh source.
