# ARCONT External Runtime Harness — Implementation Contract

This document specifies the external executable harness that produces runtime evidence for ARCONT. The harness MUST live outside the ARCONT repository.

## Boundary

ARCONT stores preregistration, schemas, source traces, hashes, accepted result metadata, interpretations and decisions. The external harness stores the minimal Godot project needed to execute benchmarks and the raw samples it produces.

The harness is not a game. It must not contain production gameplay, levels, characters, product assets or unrelated experiments.

## Required repository identity

A harness result is acceptable only when it records the exact harness Git commit. A dirty working tree must be rejected or explicitly marked and the run must not be promoted to canonical evidence.

Recommended external repository name: `Arcont-Runtime-Lab`.

## Runner input

The runner consumes a manifest emitted by:

```bash
python tools/runtime_evidence.py emit-manifest ARC-BENCH-SCENETREE-INACTIVE-NODE-001
```

The manifest fixes:

- benchmark ID;
- campaign ID;
- Godot version and exact commit;
- hypothesis reference;
- experimental variable;
- sweep values;
- warm-up;
- sample duration;
- repetitions;
- metrics;
- controls;
- abort thresholds.

The runner MUST NOT silently modify those values. A changed design requires a new preregistration commit in ARCONT.

## Minimal external layout

```text
Arcont-Runtime-Lab/
  README.md
  project.godot
  runner/
    benchmark_runner.gd
    metrics_collector.gd
    environment_probe.gd
    result_writer.gd
  benchmarks/
    baseline_empty.gd
    scenetree_inactive_node.gd
    scenetree_process_node.gd
    scenetree_physics_node.gd
    scenetree_priority_churn.gd
  manifests/
  raw/
  results/
```

ARCONT itself must not copy this executable project into `main`.

## Environment probe

Before each run, record at minimum:

- OS and version;
- device identifier/model;
- CPU;
- GPU;
- renderer;
- viewport resolution;
- build type;
- VSync state;
- physics tick rate where applicable;
- power/battery state when available;
- thermal state/temperature when available.

Unknown values are `null`; they are never guessed.

## Timing

Use a monotonic timing source. Warm-up data must not enter the measured sample distribution. Raw per-frame or per-interval samples must be retained before summary statistics are calculated.

The summary MUST be derivable from raw data. At minimum, frame-time summaries should provide count, mean, median, p95, p99, minimum and maximum when enough samples exist.

## Repetitions

Every planned sweep point is an independent run. Every run records its repetition index. The harness must not combine repetitions into one opaque result file.

ARCONT treats one valid run as an observation, not a reproduction. Promotion to L4 requires independent repeated evidence according to the maturity model.

## Abort behavior

Abort thresholds are safety controls, not data-cleaning tools. When a threshold is hit:

1. stop increasing load;
2. write a result with `aborted=true`;
3. record a machine-readable and human-readable abort reason;
4. preserve all raw samples collected before the abort;
5. never convert the partial run into a successful run by deleting the terminal samples.

## Files and hashes

Recommended raw format: JSON Lines or CSV with an explicit schema/version header.

For every completed run:

1. write raw samples;
2. close and fsync where supported;
3. compute SHA-256 of the exact raw artifact;
4. write the result JSON referencing that hash;
5. record the exact harness commit.

The result is then checked in ARCONT with:

```bash
python tools/runtime_evidence.py validate-result path/to/run.result.json
```

## Separation of measurement and interpretation

The external harness may calculate descriptive statistics. It MUST NOT label a result as a regression, optimization rule, engine limitation or best practice. Those are ARCONT knowledge-layer decisions and require comparison, repetition, source context and maturity gates.

## First implementation order

1. `ARC-BENCH-BASELINE-EMPTY-001`
2. `ARC-BENCH-SCENETREE-INACTIVE-NODE-001`
3. `ARC-BENCH-SCENETREE-PROCESS-NODE-001`
4. `ARC-BENCH-SCENETREE-PHYSICS-NODE-001`
5. `ARC-BENCH-SCENETREE-PRIORITY-CHURN-001`

Do not add physics, rendering or navigation benchmarks until the first campaign can complete end-to-end: preregistration → raw data → hash → result validation → observation → reproduction.
