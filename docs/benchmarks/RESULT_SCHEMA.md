# ARCONT Benchmark Result Schema

Formato canónico para resultados producidos por suites externas.

```yaml
schema_version: 1
benchmark_id: ARC-BENCH-SCENETREE-0001
run_id: UUID-or-stable-run-id
engine:
  name: godot
  version: 4.7.2-stable
  commit: ed1daf0bf001b61586d9930840f2f1394092c079
platform:
  os: android
  os_version: null
  device: null
  cpu: null
  gpu: null
  ram_gb: null
runtime:
  renderer: null
  resolution: null
  vsync: null
  fps_cap: null
  build_type: release
experiment:
  hypothesis_id: null
  variable: node_count
  value: 1000
  warmup_seconds: null
  sample_seconds: null
  repetitions: null
  seed: null
thermal:
  initial_celsius: null
  final_celsius: null
  throttling_observed: null
metrics:
  frame_time_ms:
    mean: null
    median: null
    p95: null
    p99: null
    max: null
  fps:
    mean: null
    median: null
  memory_mb:
    rss: null
    peak: null
  cpu_ms: null
  gpu_ms: null
  draw_calls: null
  objects: null
raw_data_ref: null
notes: null
aborted: false
abort_reason: null
created_at: null
```

## Reglas

- Los campos desconocidos son `null`; nunca se estiman para completar el esquema.
- `mean FPS` nunca sustituye frame time percentiles cuando estos están disponibles.
- Una corrida abortada sigue siendo evidencia y debe conservarse.
- Cada resultado debe ser inmutable una vez publicado; correcciones crean una nueva versión/run.
- Los datos crudos deben permanecer separables del resumen.
- Comparaciones entre runs requieren compatibilidad explícita de variables de control.

## Compatibilidad

Dos runs solo son directamente comparables si las diferencias relevantes están declaradas y forman parte de la pregunta experimental. Diferencias de renderer, resolución, temperatura, versión del motor o hardware pueden invalidar una comparación simple.

## Estadística mínima

Cuando el benchmark lo permita, conservar número de muestras y distribución suficiente para calcular media, mediana, p95, p99 y dispersión. ARCONT no debe reducir una distribución de frame times a un único FPS.