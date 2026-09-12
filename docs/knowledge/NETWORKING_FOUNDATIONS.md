# Networking Foundations

Scope: shared, 2D, 2.5D, 3D
Status: CURATED TECHNICAL FOUNDATION; implementation choices require workload-specific validation

## Core architecture families

ARCONT tracks networking techniques by assumptions rather than by popularity:
- authoritative server;
- deterministic lockstep;
- state/snapshot replication;
- snapshot interpolation;
- client prediction and reconciliation;
- rollback;
- networked physics.

## Snapshot interpolation

Snapshot interpolation reconstructs remote state between received simulation snapshots. It trades bandwidth/update rate, interpolation delay and visual smoothness. Jitter and packet loss affect the buffer required for stable playback.

## Deterministic lockstep

Lockstep can minimize state bandwidth but requires determinism and creates synchronization constraints. Cross-platform floating-point determinism and waiting for remote input are major design considerations. It must not be recommended without documenting player count, simulation determinism and latency assumptions.

## Prediction and reconciliation

For locally controlled responsive actions, prediction can hide round-trip latency while authoritative reconciliation corrects divergence. The acceptable correction strategy depends on gameplay semantics, collision model and tolerance for visible error.

## Rollback

Rollback is a distinct design choice, especially useful for some tightly synchronized competitive simulations. Its suitability depends on deterministic/resimulatable state, rollback window, state size, CPU budget and gameplay model.

## Required metadata for ARCONT network experiments

- authority model;
- simulation tick rate;
- send/snapshot rate;
- player/entity count;
- latency distribution;
- jitter;
- packet loss/reordering;
- bandwidth;
- state size;
- interpolation buffer;
- prediction horizon;
- correction magnitude;
- CPU cost of simulation/resimulation;
- platform and engine version.

## Questions generated

1. How does snapshot rate trade bandwidth against interpolation delay and error?
2. What correction magnitudes become visually objectionable for representative movement models?
3. What is rollback/resimulation cost as entity count and window grow?
4. Which simulation components remain deterministic across target platforms?
5. What network architecture best matches a future game's actual authority, player count and latency requirements?

ARCONT will never label one networking architecture 'best' without those conditions.
