# Physics and Simulation

Dimensions: shared, 2D, 2.5D, 3D
Status: source-derived starter knowledge; requires engine/platform benchmarks

## Source anchors

NVIDIA PhysX documents a broad simulation stack including rigid bodies, scene queries, joints, articulations, character controllers, soft bodies, SDF collision, position-based dynamics and destruction/fracture support. ARCONT treats these as implementation references, not universal prescriptions.

## Transferable model

A real-time physics system should be decomposed into at least:

1. broad phase / spatial candidate generation;
2. narrow phase contact generation;
3. constraint solving;
4. integration;
5. scene queries (ray, sweep, overlap);
6. sleeping/activation;
7. collision-shape representation;
8. continuous collision where required;
9. character-control semantics;
10. destruction/deformation where applicable.

A benchmark that only reports 'number of rigid bodies' hides which layer is expensive.

## Important variables

- active vs sleeping bodies;
- static / kinematic / dynamic mix;
- contact-pair density;
- shape type and geometric complexity;
- joint/constraint count;
- solver iterations;
- fixed timestep and substeps;
- CCD enabled/disabled;
- query volume and frequency;
- destruction fragment count;
- CPU vs GPU solver path where available.

## Research questions

- Does performance correlate more with active bodies or total bodies?
- At what contact density does narrow-phase/solver cost dominate?
- What does CCD cost on fast small objects compared with tunneling risk?
- When is a simple collision proxy substantially more valuable than reducing visual mesh complexity?
- How expensive is creating/removing bodies compared with keeping pooled/sleeping bodies?
- What is the cost of dynamic destruction on collision, navigation and memory together?

## Benchmark families

### PHY-001: body baseline
Sweep static/kinematic/dynamic body counts independently. Record active/sleeping state and frame-time percentiles.

### PHY-002: contact density
Keep body count fixed; alter spatial packing to vary simultaneous contact pairs.

### PHY-003: shape complexity
Compare primitive, convex, compound and complex/static collision representations under matched workloads.

### PHY-004: query workload
Ray/sweep/overlap queries with controlled scene density and query count.

### PHY-005: constraints
Scale joints/articulations independently of body count.

### PHY-006: lifecycle churn
Create/destroy vs reuse/reposition the same amount of physics state.

### PHY-007: destruction
Measure fracture/fragment creation, temporary bodies, cleanup and cross-system consequences.

## Correctness metrics matter

Performance is not the only metric. ARCONT should preserve:

- tunneling incidents;
- unstable stacks;
- constraint error;
- penetration depth;
- simulation divergence;
- determinism/repeatability where relevant;
- visual/gameplay artifacts.

A faster configuration that materially breaks simulation semantics is not automatically superior.

## Transfer rule

Physics advice must remain scoped by engine version, backend, timestep, solver configuration, scene composition and hardware. A conclusion from PhysX, Godot Physics or another backend is not automatically portable without reproduction.