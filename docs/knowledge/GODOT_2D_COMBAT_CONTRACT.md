# Godot 2D combat contract

Status: **working contract / Mortofe consumer-validated for parse + headless smoke**

Trigger consumer: `heliossamuelhernandezreyes/Godot-juegos-2d/Mortofe`

Engine scope: Godot `4.7.2-stable`, commit `ed1daf0bf001b61586d9930840f2f1394092c079`.

## Purpose

Define a reusable 2D action-combat boundary for ARCONT without storing production game code inside ARCONT. Mortofe owns the implementation; ARCONT records the contract, evidence and validation backlog.

## Separation of responsibilities

### Actor/controller

Owns:

- attack timing and cooldowns,
- invulnerability state,
- dash immunity policy,
- parry state,
- knockback response,
- health/death,
- animation state.

### Hitbox2D

Owns:

- a damage payload,
- source actor reference,
- target hurtbox mask,
- attack-window activation/deactivation,
- one-hit-per-target bookkeeping for the current window,
- delivery to compatible Hurtbox2D receivers.

A hitbox should not directly know enemy/player controller classes.

### Hurtbox2D

Owns:

- target collision layer,
- receiver shape,
- forwarding a hit payload to its owning actor,
- giving the actor a parry/interception opportunity before damage.

A hurtbox should not own health or knockback policy.

## Collision-layer policy

Production bodies and combat detection are separate concepts. A CharacterBody2D body layer is for world/body collision; combat hitboxes should detect combat hurtbox layers rather than relying on body collision.

Mortofe reference layout currently includes:

- World,
- PlayerBody,
- EnemyBody,
- PlayerHurtbox,
- EnemyHurtbox,
- attack detection masks targeted at hurtbox layers.

Exact numerical bits are product/project configuration. The architectural requirement is the separation.

## Attack-window contract

An attack cycle should distinguish:

1. startup,
2. active hit window,
3. recovery,
4. next-attack availability.

A hitbox is enabled only for the active window. Repeated physics overlap during one active window must not deal repeated damage to the same hurtbox unless the move explicitly declares multi-hit behavior.

## Damage delivery contract

A generic hit payload should be able to evolve beyond `damage` without changing every actor. Future payload fields may include:

- poise/stagger damage,
- knockback vector or scalar,
- hitstop request,
- elemental/damage tags,
- attack direction,
- parry class,
- armor-piercing flags,
- source ability/weapon id.

Mortofe begins with source actor + integer damage and leaves response policy in the receiver actor.

## Parry path

Hurtbox reception must permit an actor-level interception hook before damage. A reusable sequence is:

`Hitbox2D -> Hurtbox2D -> actor.try_parry_hit(hitbox) -> actor.take_damage(...)`

If the parry hook consumes the hit, ordinary damage is skipped. This keeps parry state in gameplay logic rather than in a generic collision component.

## Required validation

The contract is not READY until tests cover:

- one target hit once in one attack window,
- two targets hit by one valid sweep,
- repeated attacks can hit the same target on later windows,
- invulnerability rejects damage but does not corrupt hitbox state,
- dash immunity policy,
- parry consumes the correct attack classes,
- knockback direction relative to source,
- actor deletion during an active hit window,
- overlapping multiple attackers,
- mobile frame stability during dense Area2D combat.

## Mortofe evidence

Reference implementation paths:

- `Mortofe/scripts/combat/hitbox_2d.gd`
- `Mortofe/scripts/combat/hurtbox_2d.gd`
- `Mortofe/scripts/player.gd`
- `Mortofe/scripts/enemy.gd`

The implementation remains external to ARCONT. Promote individual capabilities only after CI/runtime evidence supports them.
