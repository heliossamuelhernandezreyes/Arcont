# Godot — Resources and Data-Driven Architecture

## Candidate direction
As content grows, represent tunable definitions as typed custom Resources rather than expanding hard-coded dictionaries in controllers.

Candidates:
- WeaponDefinition
- Ammo/BallisticProfile
- DamageProfile
- SurfaceMaterialProfile
- EnemyArchetype
- AIProfile
- ThrowableDefinition
- EncounterDefinition
- Loot/SupplyDefinition
- AudioEventDefinition
- VFXProfile

## Principles
- Controllers implement behavior; Resources describe content/tuning.
- Avoid making every tiny value a Resource if it adds indirection without reuse.
- Version schemas carefully because saved `.tres`/`.res` content becomes production data.
- Prefer explicit typed fields and validation.
- Keep runtime mutable state separate from shared definition Resources unless duplication is intentional.

## Benefits
Designer-friendly tuning, less controller churn, easier balancing, reusable validation, easier content comparison and potential future mod/data-pack support.

## References
- Godot Resources: https://docs.godotengine.org/en/stable/tutorials/scripting/resources.html
- Resource class: https://docs.godotengine.org/en/stable/classes/class_resource.html

## Status
CANDIDATE. Weapon definitions are the clearest first migration once vertical-slice feel stabilizes.
