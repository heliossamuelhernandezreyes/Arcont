# ARCONT Upstream Observability Layer

Status: integration architecture
Scope: Godot 4.7.2-stable canonical engine pin

ARCONT does not replace profilers or upstream benchmark suites. It treats them as instruments and evidence sources beneath the knowledge/maturity layer.

## Roles

### Godot Benchmarks
Upstream comparative benchmark source for rendering, scripting, scene/runtime and engine-performance measurements. Imported observations remain EXTERNAL evidence until provenance, engine identity, metric semantics and environment are recorded.

Canonical upstream: `godotengine/godot-benchmarks`.

### Perfetto
Primary tracing instrument for Android and system-level timing. Godot 4.7+ provides Perfetto export templates for stable releases. ARCONT should use Perfetto when a hypothesis requires scheduler/thread/system tracing rather than only aggregate frame metrics.

### Tracy
Cross-platform tracing/sampling instrument for deep CPU investigation. Tracy evidence is diagnostic by default and becomes claim-supporting evidence only after a preregistered question and trace-analysis protocol identify the metric/event used.

## Evidence boundary

External tools never promote a claim by themselves.

Pipeline:

`question -> claim/hypothesis -> instrument selection -> preregistration -> execution/import -> raw immutable evidence -> provenance -> semantic normalization -> validation -> observation -> reproduction -> maturity -> decision rule`

ARCONT owns the last five stages. The instrument owns measurement only.

## Instrument-selection rule

- Use ARCONT Runtime Lab for controlled microbenchmarks and falsifiable sweeps.
- Use Godot Benchmarks for upstream comparison, regression context and candidate hypotheses.
- Use Perfetto for Android/system scheduling, threads, CPU frequency and trace-level questions.
- Use Tracy for cross-platform CPU tracing/sampling and hotspot investigation.
- Multiple instruments may support one claim, but their measurements must not be silently treated as equivalent.

## Provenance minimum

Every imported observation must identify:

- provider/instrument and version or upstream commit;
- Godot version and commit when applicable;
- source URI/repository and immutable source reference where available;
- platform, hardware and build type when available;
- exact metric name and original unit;
- ARCONT normalized metric name/unit;
- collection/import timestamp;
- raw evidence hash when raw evidence is preserved;
- limitations and missing provenance fields.

Missing fields are recorded as unknown, never inferred.

## Maturity policy

External benchmark data can source-trace a claim and can contribute observations when its protocol and provenance are sufficient. It cannot automatically grant L4+ maturity. Independent reproduction, hardware diversity and version diversity continue to follow `docs/MATURITY_MODEL.md`.

## First integration campaign

1. Build a catalog adapter for the public Godot Benchmarks suite and its metric vocabulary.
2. Map relevant upstream SceneTree/process benchmarks, if present, to ARCONT claims without declaring semantic equivalence prematurely.
3. Define Perfetto trace manifests for Android release builds.
4. Define Tracy trace manifests for CPU investigations.
5. Add cross-source evidence records so Runtime Lab, upstream benchmarks and traces can support or contradict the same claim while retaining separate provenance.

## Non-goals

- vendoring entire third-party repositories into ARCONT;
- treating profiler screenshots as canonical evidence;
- copying upstream conclusions without source/version provenance;
- changing preregistered experiments after seeing external results;
- promoting maturity because two tools report superficially similar numbers.
