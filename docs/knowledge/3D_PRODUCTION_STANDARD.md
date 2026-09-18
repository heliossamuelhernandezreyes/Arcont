# ARCONT 3D Production Standard v1.0

Status: production candidate
Target: stylized 3D games with distant tactical/RTS cameras and Godot delivery.

## Goal

Produce original, readable, expressive 3D assets with a strong silhouette at gameplay distance. The reference bar is the readability and exaggeration associated with classic stylized RTS art, without copying protected characters, meshes, textures, insignia, architecture, or other distinctive designs.

## Canonical pipeline

CONCEPT -> BLOCKOUT -> HIGH/LOW MODEL -> RETOPOLOGY -> UV -> BAKE -> TEXTURE -> RIG -> ANIMATION -> GLB -> VALIDATION -> LOD -> ENGINE -> RUNTIME EVIDENCE

Every production asset has a stable semantic ID. Maps and gameplay refer to that ID, never to an arbitrary mesh filename.

## Geometry budgets

Budgets are starting gates, not universal performance claims.

| Class | LOD0 target | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| hero | 15k-30k tris | <=60% | <=30% | <=12% |
| troop | 8k-18k tris | <=55% | <=25% | <=10% |
| creep | 4k-10k tris | <=50% | <=22% | <=8% |
| large structure | 20k-60k tris | <=55% | <=25% | proxy/impostor |
| prop | 500-8k tris | <=50% | <=20% | optional |

Close Seal may tighten these after Android and desktop evidence.

## Tactical readability gates

At the intended gameplay camera:
- class and facing must remain identifiable;
- weapon/action silhouette must not merge into the torso;
- team identification must not depend on tiny details;
- hero silhouette must be unique among nearby troops;
- important gameplay state must survive LOD changes;
- decorative noise must not dominate the silhouette.

Exaggeration is intentional: hands, shoulders, weapons, helmets, mantles and major accessories may be proportionally enlarged when this improves tactical recognition.

## Materials and textures

Prefer a small number of material slots. Reuse atlases by unit family where practical. Author PBR-compatible base color, normal and ORM-style packed data when justified. Validate mipmaps and compression. KTX2/Basis is a delivery candidate and must be benchmarked rather than assumed superior.

Suggested source resolution:
- hero: 2K master, with platform variants;
- troop family: 1K-2K atlas;
- creeps/props: 512-1K where visual evidence allows.

## Rig contract

Shared skeletons are preferred within compatible unit families. Bone names and attachment sockets are stable API.

Required humanoid sockets:
- hand_r
- hand_l
- weapon
- shield
- head
- chest
- root_fx

Animation LOD may reduce update frequency or IK at distance. Collision remains simpler than render geometry.

## Minimum animation set for a combat hero

idle, locomotion, attack_primary, attack_secondary, cast, hit, death, victory.

A vertical-slice hero should additionally test turn/facing readability, weapon trails or FX attachment, root motion policy, retargetability and distant animation LOD.

## Godot delivery

Canonical interchange: GLB/glTF 2.0.

Production import must preserve:
- stable scale and forward/up convention;
- skeleton and animation names;
- material assignments;
- semantic asset ID;
- LOD membership;
- attachment sockets;
- provenance/license metadata.

Gameplay code should resolve semantic IDs through an asset registry. Do not hard-code artistic filenames into map semantics.

## Map Forge integration

Example:

structure.fortress_tower -> AssetResolver -> cs_structure_fortress_tower_a.glb

The canonical map continues to own gameplay meaning, position and traversal. The visual asset is replaceable. Navigation/collision changes require their own physical-world validation.

## Performance evidence

Validate independently:
- triangles/vertices;
- draw calls and material changes;
- texture resident memory;
- shadow cost;
- skinning/animation CPU/GPU cost;
- visible unit count;
- LOD transition cost/quality;
- Android frame time and memory;
- desktop frame time.

Never declare an asset mobile-safe from triangle count alone.

## First vertical slice: Close Seal Hero

The existing procedural Hero is the replacement target.

Art brief:
- original heroic dark-fantasy commander;
- broad readable shoulders and mantle;
- oversized single-edged or straight fantasy blade with clean silhouette;
- luminous seal/focus as a unique gameplay identifier;
- restrained surface detail at RTS distance;
- faction color zones separated from metal/leather;
- silhouette readable in neutral, attack and cast poses.

Deliverables:
1. cs_hero_01_lod0.glb
2. LOD1-LOD3 or documented generation recipe
3. texture set
4. shared/declared skeleton
5. minimum animation set
6. asset manifest
7. Godot import test
8. 1280x720 tactical-camera screenshot
9. performance evidence

## Acceptance

An asset is not production-ready merely because it imports. It passes only when provenance, technical validation, tactical readability, animation, LOD behavior and runtime evidence are recorded.
