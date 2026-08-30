# AI — Architecture and Tactical Behavior

## Separation of concerns
Perception -> memory/belief -> tactical decision -> navigation/movement -> combat execution.

Avoid giving every enemy omniscient direct access to the player's current state.

## Arcont layers
### Perception
Vision, sound, damage/contact reports, R-3, explosions and environmental events.

### Memory / shared intelligence
Last known position, confidence, age, source and squad-shared contacts. AwarenessDirector is a natural central event/intelligence service but should not become a universal god object.

### Tactical decision
Cover, flank, suppress, advance, retreat, hold, investigate, melee pressure, ability use.

### Movement
Navigation/path scheduler + local steering/separation.

### Combat
Aim/fire/melee/ability execution with archetype-specific rules.

## Different intelligence budgets
- Infected: cheap pursuit, sound attraction, local separation, simple state.
- Tactical ranged: cover/exposure/flank/suppression.
- Xeno: distinct behavior grammar and abilities.
- Boss/elite: larger update budget and authored sequences.
- R-3: player-command priority plus bounded autonomy.

## Research paradigms
- Finite/hierarchical state machines: predictable, excellent baseline.
- Utility AI: useful for continuous tactical choices.
- Behavior trees: readable hierarchical action selection.
- GOAP: powerful for planning but can be unnecessary complexity.
- Hybrid systems are often more practical than ideological purity.

## Reference
- Operation Steel Tide: https://github.com/AetherRadar/operation-steel-tide — tactical shooter architecture reference; audit license before reuse.
- Godot navigation docs under ../godot/navigation.md.

## Performance rule
Perception and decision frequencies should scale by importance/distance. Expensive cover/path queries should be scheduled and cached where possible.
